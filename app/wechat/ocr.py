"""把截图里的文字读出来。优先本地 RapidOCR，没有就退回 Windows 自带 OCR。"""
import re
import subprocess
import tempfile
from pathlib import Path

from .. import paths

_engine = None
_tried = False

CJK = r"\u4e00-\u9fa5"


def _rapid():
    global _engine, _tried
    if not _tried:
        _tried = True
        try:
            from rapidocr_onnxruntime import RapidOCR
            _engine = RapidOCR()
        except Exception:
            _engine = None
    return _engine


def normalize(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"(?<=[" + CJK + r"])\s+(?=[" + CJK + r"])", "", text)
    return text.strip()


def _prep(img):
    """微信气泡字号小，1.5 倍 + 锐化后 Windows OCR 明显更准。"""
    from PIL import ImageFilter
    base = img.convert("RGB")
    big = base.resize((int(base.width * 1.5), int(base.height * 1.5)), 1)
    return big.filter(ImageFilter.SHARPEN)


def recognize(img) -> str:
    engine = _rapid()
    if engine is not None:
        try:
            import numpy as np
            result, _ = engine(np.array(img))
            if result:
                return normalize("\n".join(line[1] for line in result))
            return ""
        except Exception:
            pass
    return _windows_ocr(_prep(img))


def _windows_ocr(img) -> str:
    script = paths.resource("ocr.ps1")
    if not script.exists():
        return ""
    tmp = Path(tempfile.gettempdir()) / "meal_helper_ocr.png"
    img.save(tmp)
    try:
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(script), "-Path", str(tmp)],
            capture_output=True, creationflags=0x08000000, timeout=20,
        )
        return normalize(out.stdout.decode("utf-8", "ignore"))
    except Exception:
        return ""