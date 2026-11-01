"""发送：搜会话 → 粘贴 → 回车。带锁屏/空闲保护与演练模式。"""
import time

from .. import logger
from . import ocr, screenio, win32

VK_CONTROL, VK_A, VK_DELETE, VK_F, VK_RETURN = 0x11, 0x41, 0x2E, 0x46, 0x0D


class Sender:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.wx = cfg.get("wechat", {})
        self.dry_run = bool(cfg.get("dry_run", True))
        self.last_error = ""

    def available(self) -> bool:
        return bool(win32.find_window(self.wx.get("process", "Weixin.exe"),
                                      self.wx.get("title", "微信")))

    def _verify_chat(self, hwnd, remark: str) -> bool:
        try:
            img = screenio.capture(hwnd)
            title = ocr.recognize(screenio.chat_title(img)).replace(" ", "")
        except Exception:
            return False
        want = remark.replace(" ", "")
        return bool(title) and (want in title or title in want)

    def send(self, text: str, remark: str = "", verify=None) -> bool:
        log = logger.get()
        if not remark.strip():
            self.last_error = "没有设置她的微信备注"
            return False
        if self.dry_run:
            log.info("[演练] 本应发送给 %s：%s", remark, text)
            return True
        if win32.session_locked():
            self.last_error = "电脑锁屏中，无法发送"
            return False

        hwnd = win32.find_window(self.wx.get("process", "Weixin.exe"),
                                 self.wx.get("title", "微信"))
        if not hwnd:
            self.last_error = "没找到微信窗口"
            return False

        fg = win32.foreground()
        try:
            waited = 0
            while win32.idle_seconds() < 3 and waited < 120:
                time.sleep(5)
                waited += 5

            if not win32.activate(hwnd):
                self.last_error = "微信窗口提不到最前面"
                return False
            time.sleep(0.3)

            win32.hotkey(VK_CONTROL, VK_F)
            time.sleep(0.5)
            win32.hotkey(VK_CONTROL, VK_A)
            win32.key(VK_DELETE)
            win32.paste(remark)
            time.sleep(1.0)
            win32.key(VK_RETURN)
            time.sleep(0.9)

            # 发错人防护：确认打开的是她的会话
            if not self._verify_chat(hwnd, remark):
                self.last_error = f"发错人防护：当前会话不是「{remark}」，已中止"
                logger.get().warning(self.last_error)
                return False

            left, top, right, bottom = win32.rect(hwnd)
            w, h = right - left, bottom - top
            win32.click(left + int(w * 0.45), top + int(h * 0.88))
            time.sleep(0.3)
            win32.paste(text)
            time.sleep(0.3)
            win32.key(VK_RETURN)
            time.sleep(0.6)
            self.last_error = ""
            return True
        except Exception as e:
            self.last_error = str(e)
            log.exception("发送异常")
            return False
        finally:
            win32.restore(fg)