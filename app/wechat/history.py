"""回溯聊天记录：找到「我发的那条提醒」，把它下面她的回复捞回来。

用途：等待窗口结束仍没读到回复时，自动翻聊天记录补录。
"""
import time
from datetime import datetime

from .. import logger, paths
from . import ocr, screenio, visionapi, win32


def _read(cfg, crop) -> str:
    if visionapi.enabled(cfg):
        t = visionapi.read_image(cfg, crop)
        if t:
            return t
    return ocr.recognize(crop)


def _similar(a: str, b: str) -> bool:
    a = "".join(ch for ch in (a or "") if ch.isalnum())
    b = "".join(ch for ch in (b or "") if ch.isalnum())
    if not a or not b:
        return False
    return a[:8] in b or b[:8] in a


def find_replies(cfg: dict, ask_text: str, max_scroll: int = 3):
    """返回 (她在这条提醒之后的回复列表, 错误说明)。"""
    wx = cfg.get("wechat", {})
    hwnd = win32.find_window(wx.get("process", "Weixin.exe"), wx.get("title", "微信"))
    if not hwnd:
        return [], "没找到微信窗口"

    was_min = win32.is_minimized(hwnd)
    debug = paths.log_dir() / "last_scan.png"
    try:
        if was_min:
            win32.show(hwnd, 9)
            time.sleep(1.0)

        # 先滚到最新，避免上次扫描把画面留在历史里
        win32.activate(hwnd)
        win32.wheel(-360 * 15)
        time.sleep(0.8)

        for _ in range(max_scroll + 1):
            img = screenio.capture(hwnd)
            try:
                img.save(debug)
            except Exception:
                pass

            blocks = screenio._message_blocks(img)
            if not blocks:
                return [], "聊天区没识别到消息"

            texts = {}
            idx_ask = None
            for i in range(len(blocks) - 1, -1, -1):
                box, is_mine = blocks[i]
                if not is_mine:
                    continue
                t = _read(cfg, img.crop(box))
                texts[i] = t
                if _similar(t, ask_text):
                    idx_ask = i
                    break

            if idx_ask is not None:
                out = []
                for j in range(idx_ask + 1, len(blocks)):
                    box, is_mine = blocks[j]
                    if is_mine:
                        continue
                    t = texts.get(j) or _read(cfg, img.crop(box))
                    if t:
                        out.append(t)
                return out, ""

            win32.wheel(360)
            time.sleep(0.9)
        return [], "没找到那条提醒消息（可能已经滚出屏幕）"
    except Exception as e:
        logger.get().warning("回溯聊天失败：%s", e)
        return [], str(e)
    finally:
        try:
            win32.wheel(-360 * 15)      # 还原到最新
        except Exception:
            pass
        if was_min:
            try:
                win32.show(hwnd, 6)
            except Exception:
                pass