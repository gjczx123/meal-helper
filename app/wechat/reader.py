"""读她的回复：截图 + OCR。

不点击、不碰微信的数据库。最小化的窗口临时还原，读完缩回去。
"""
import time
from datetime import datetime

from .. import logger
from . import ocr, screenio, visionapi, win32

# 气泡里常见的非正文
NOISE = ("微信电脑版", "查看更多", "以下为新消息")


class Reader:
    mode = "screen"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.wx = cfg.get("wechat", {})
        self.last_error = ""
        self._sig = ""
        self._seen = set()
        self._last_text = ""
        self._last_at = 0.0
        self.engine = "?"

    def status(self) -> dict:
        hwnd = self._find()
        try:
            from .ocr import _rapid
            self.engine = "RapidOCR" if _rapid() is not None else "Windows OCR"
        except Exception:
            self.engine = "视觉模型" if visionapi.enabled(self.cfg) else "OCR"
        return {
            "ready": bool(hwnd),
            "mode": "截图 + " + self.engine,
            "error": "" if hwnd else "没找到微信窗口",
        }

    @staticmethod
    def _title_of(img) -> str:
        lines = [l.strip() for l in ocr.recognize(screenio.chat_title(img)).splitlines() if l.strip()]
        return lines[0].replace(" ", "") if lines else ""

    def _is_her_chat(self, hwnd, img, remark: str) -> bool:
        """确认当前打开的会话是她，否则不读（避免把别的聊天记进台账）。"""
        if not remark:
            self.last_error = "没设置她的微信备注，不敢读"
            return False
        title = self._title_of(img)
        if remark.replace(" ", "") in title or title in remark.replace(" ", ""):
            return True

        if not self.cfg.get("reader", {}).get("auto_switch", True):
            self.last_error = f"当前会话是「{title}」，不是她，已跳过"
            return False

        # 切到她的会话再看一眼
        try:
            win32.activate(hwnd)
            time.sleep(0.3)
            win32.hotkey(0x11, 0x46)      # Ctrl+F
            time.sleep(0.5)
            win32.hotkey(0x11, 0x41)      # 全选
            win32.key(0x2E)               # 删除
            win32.paste(remark)
            time.sleep(0.9)
            win32.key(0x0D)               # 回车
            time.sleep(0.9)
        except Exception:
            pass
        img2 = screenio.capture(hwnd)
        title2 = self._title_of(img2)
        if remark.replace(" ", "") in title2:
            return True
        self.last_error = f"没切到她的会话（当前「{title2 or title}」）"
        return False

    def _find(self):
        return win32.find_window(self.wx.get("process", "Weixin.exe"),
                                 self.wx.get("title", "微信"))

    def test_read(self, remark: str = ""):
        """诊断用：读她最近发的一条，不要求它是最新消息。返回 (文字, 错误)。"""
        hwnd = self._find()
        if not hwnd:
            return "", "没找到微信窗口"
        was_min = win32.is_minimized(hwnd)
        try:
            if was_min:
                win32.show(hwnd, 9)
                time.sleep(0.9)
            img = screenio.capture(hwnd)
            if not self._is_her_chat(hwnd, img, remark):
                return "", self.last_error or "当前不是她的会话"
            img = screenio.capture(hwnd)
            spot = screenio.find_last_hers(img)
            if not spot:
                return "", "聊天区里没找到她发的文字消息"
            crop = img.crop(spot[0])
            if visionapi.enabled(self.cfg):
                text = visionapi.read_image(self.cfg, crop)
                if not text:
                    text = ocr.recognize(crop)
            else:
                text = ocr.recognize(crop)
            return text, "" if text else "读出来是空的（可能是图片）"
        except Exception as e:
            return "", str(e)
        finally:
            if was_min:
                try:
                    win32.show(hwnd, 6)
                except Exception:
                    pass

    def poll(self, remark: str, since=None) -> list:
        hwnd = self._find()
        if not hwnd:
            self.last_error = "没找到微信窗口"
            return []

        was_min = win32.is_minimized(hwnd)
        try:
            if was_min:
                win32.show(hwnd, 9)
                time.sleep(0.9)
                for _ in range(12):
                    r = win32.rect(hwnd)
                    if r[2] - r[0] > 600 and r[3] - r[1] > 400:
                        break
                    time.sleep(0.2)

            img = screenio.capture(hwnd)
            if not self._is_her_chat(hwnd, img, remark):
                return []
            img = screenio.capture(hwnd)
            sig = screenio.chat_signature(img)
            if sig == self._sig or sig in self._seen:
                return []
            self._sig = sig

            spot = screenio.find_last_message(img)
            if not spot:
                self.last_error = "聊天区没找到文字消息"
                return []
            box, is_mine = spot
            if is_mine:
                self.last_error = "最后一条是我自己发的"
                return []

            crop = img.crop(box)
            if visionapi.enabled(self.cfg):
                text = visionapi.read_image(self.cfg, crop)
                self.engine = "视觉模型"
                if not text:
                    text = ocr.recognize(crop)
                    self.engine = "OCR（视觉失败）"
            else:
                text = ocr.recognize(crop)
            text = "\n".join(l for l in text.splitlines()
                             if l.strip() and not any(n in l for n in NOISE))

            now = time.time()
            if text and text == self._last_text and now - self._last_at < 120:
                return []
            self._last_text = text
            self._last_at = now
            self._seen.add(sig)
            if not text:
                self.last_error = "这条没有文字（可能是图片）"
                return [{"id": sig, "ts": datetime.now().strftime("%H:%M:%S"),
                         "text": "", "image_path": ""}]

            self.last_error = ""
            return [{"id": sig, "ts": datetime.now().strftime("%H:%M:%S"),
                     "text": text, "image_path": ""}]
        except Exception as e:
            self.last_error = str(e)
            logger.get().exception("截图读取失败")
            return []
        finally:
            if was_min:
                try:
                    win32.show(hwnd, 6)
                except Exception:
                    pass