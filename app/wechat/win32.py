"""Win32 窗口/输入/剪贴板。统一按物理像素工作。"""
import ctypes
import ctypes.wintypes as wt
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_RESTORE = 9
VK_CONTROL = 0x11
VK_A, VK_C, VK_V, VK_F, VK_RETURN, VK_DELETE, VK_ALT = 0x41, 0x43, 0x56, 0x46, 0x0D, 0x2E, 0x12

_dpi_done = False


def set_dpi_aware():
    """必须在任何界面/坐标计算之前调用。"""
    global _dpi_done
    if _dpi_done:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
    _dpi_done = True


def find_window(process: str = "Weixin.exe", title: str = "微信"):
    pid_map = {}
    cb_type = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    found = {"hwnd": None}

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        text = buf.value
        if title not in text:
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = kernel32.OpenProcess(0x1000, False, pid.value)
        if not h:
            return True
        try:
            b = ctypes.create_unicode_buffer(1024)
            size = wt.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h, 0, b, ctypes.byref(size)):
                if process.lower() in b.value.lower():
                    found["hwnd"] = hwnd
                    return False
        finally:
            kernel32.CloseHandle(h)
        return True

    user32.EnumWindows(cb_type(cb), 0)
    return found["hwnd"]


def rect(hwnd) -> tuple:
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def foreground():
    return user32.GetForegroundWindow()


def activate(hwnd) -> bool:
    try:
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        return user32.GetForegroundWindow() == hwnd
    except Exception:
        return False


def restore(hwnd):
    try:
        if hwnd:
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def click(x: int, y: int):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(0x0004, 0, 0, 0, 0)


def key(vk: int):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(vk, 0, 2, 0)


def hotkey(*vks):
    for v in vks:
        user32.keybd_event(v, 0, 0, 0)
        time.sleep(0.02)
    for v in reversed(vks):
        user32.keybd_event(v, 0, 2, 0)
        time.sleep(0.02)


def set_clipboard(text: str) -> bool:
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    data = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h:
            return False
        p = kernel32.GlobalLock(h)
        ctypes.memmove(p, data, len(data))
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
        return True
    finally:
        user32.CloseClipboard()


def paste(text: str):
    set_clipboard(text)
    time.sleep(0.08)
    hotkey(VK_CONTROL, VK_V)


def idle_seconds() -> float:
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]
    li = LASTINPUTINFO()
    li.cbSize = ctypes.sizeof(li)
    if not user32.GetLastInputInfo(ctypes.byref(li)):
        return 0.0
    return (kernel32.GetTickCount() - li.dwTime) / 1000.0


def session_locked() -> bool:
    """锁屏检测：拿不到输入桌面即视为锁定。"""
    h = user32.OpenInputDesktop(0, False, 0x0100)
    if h:
        user32.CloseDesktop(h)
        return False
    return True

def show(hwnd, cmd: int):
    user32.ShowWindow(hwnd, cmd)


def is_minimized(hwnd) -> bool:
    return bool(user32.IsIconic(hwnd))


def right_click(x: int, y: int):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    user32.mouse_event(0x0008, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(0x0010, 0, 0, 0, 0)
