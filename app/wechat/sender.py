"""发送：搜会话 → 粘贴 → 回车。带锁屏/空闲保护与演练模式。"""
import time

from .. import logger
from . import ocr, screenio, win32

VK_CONTROL, VK_A, VK_DELETE, VK_F, VK_RETURN = 0x11, 0x41, 0x2E, 0x46, 0x0D
VK_DOWN = 0x28


class Sender:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.wx = cfg.get("wechat", {})
        self.dry_run = bool(cfg.get("dry_run", True))
        self.last_error = ""

    def available(self) -> bool:
        return bool(win32.find_window(self.wx.get("process", "Weixin.exe"),
                                      self.wx.get("title", "微信")))

    def _open_by_search(self, hwnd, remark: str) -> str:
        """Ctrl+F 搜索 → 回车打开第一条会话 → 校验标题。"""
        try:
            win32.hotkey(VK_CONTROL, VK_F)
            time.sleep(0.6)
            win32.hotkey(VK_CONTROL, VK_A)
            win32.key(VK_DELETE)
            time.sleep(0.3)
            win32.paste(remark)
            time.sleep(1.5)
            win32.key(VK_RETURN)          # 微信 4.x：回车直接打开第一条结果
            time.sleep(1.5)
            state = self._verify_chat(hwnd, remark)
            if state != "ok":
                # 兜底：点下拉里的第一条
                left, top, right, bottom = win32.rect(hwnd)
                win32.click(left + int((right - left) * 0.50),
                            top + int((bottom - top) * 0.365))
                time.sleep(1.2)
                state = self._verify_chat(hwnd, remark)
            return state
        except Exception as e:
            logger.get().warning("搜索打开会话失败：%s", e)
            return "unknown"

    def _verify_chat(self, hwnd, remark: str) -> str:
        """返回 ok / different / unknown。标题读不出来只算 unknown，不拦发送。"""
        try:
            img = screenio.capture(hwnd)
            lines = [l.strip() for l in ocr.recognize(screenio.chat_title(img)).splitlines() if l.strip()]
            title = lines[0].replace(" ", "") if lines else ""
        except Exception:
            return "unknown"
        want = remark.replace(" ", "")
        if not title:
            return "unknown"
        # 标题可能被截断，用前 6 个字比对
        if want[:6] in title or title[:6] in want:
            return "ok"
        return "different"

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

            state = self._verify_chat(hwnd, remark)
            if state != "ok":
                state = self._open_by_search(hwnd, remark)

            if state == "different":
                self.last_error = f"当前会话不是「{remark}」，已中止发送"
                logger.get().warning(self.last_error)
                return False
            if state == "unknown":
                self.last_error = "标题没读出来，已按备注搜索后直接发送"
                logger.get().warning(self.last_error)

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