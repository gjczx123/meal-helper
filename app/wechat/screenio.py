"""截图通道：PrintWindow 抓微信窗口 + 找最后一条消息 + 右键复制。

不碰微信的加密库，只做"看屏幕 + 复制文字"。
"""
import ctypes
import ctypes.wintypes as wt
import hashlib
import time

import numpy as np
from PIL import Image

from . import win32

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
k32 = ctypes.windll.kernel32

k32.GlobalAlloc.restype = ctypes.c_void_p
k32.GlobalLock.restype = ctypes.c_void_p
k32.GlobalLock.argtypes = [ctypes.c_void_p]
k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.GetClipboardData.restype = ctypes.c_void_p

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class _BIH(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG),
                ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def capture(hwnd) -> Image.Image:
    """窗口被遮挡也能抓到（PrintWindow + RENDERFULLCONTENT）。"""
    left, top, right, bottom = win32.rect(hwnd)
    w, h = right - left, bottom - top
    if w <= 0 or h <= 0:
        raise RuntimeError("窗口尺寸异常")
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)
    bi = _BIH()
    bi.biSize = ctypes.sizeof(bi)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")


def chat_signature(img: Image.Image) -> str:
    """只取聊天区，做指纹，用来判断有没有新消息。"""
    w, h = img.size
    box = (int(w * 0.38), int(h * 0.10), int(w * 0.99), int(h * 0.76))
    crop = img.crop(box).resize((160, 120))
    return hashlib.md5(crop.tobytes()).hexdigest()


def chat_left(arr) -> int:
    """聊天区左边界：用选中的绿色会话行右边缘判断，找不到就按比例兜底。"""
    h, w = arr.shape[:2]
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    green = (np.abs(r - 21) < 45) & (np.abs(g - 172) < 45) & (np.abs(b - 112) < 55)
    ys, xs = np.nonzero(green)
    if len(xs) > 500:
        return int(xs.max())
    return int(w * 0.42)


def _message_blocks(img):
    """按文字行分块，返回 [(box, is_mine), ...] 从上到下。"""
    w, h = img.size
    arr = np.asarray(img).astype(int)
    lum = (arr[:, :, 0] * 299 + arr[:, :, 1] * 587 + arr[:, :, 2] * 114) // 1000
    left = chat_left(arr)
    x0, x1 = min(left + 4, w - 10), int(w * 0.995)
    y0, y1 = int(h * 0.08), int(h * 0.97)
    sub = lum[y0:y1, x0:x1]
    dark = sub < 120
    rows = dark.sum(axis=1)
    idx = np.where(rows >= 2)[0]
    if len(idx) == 0:
        return []

    groups = []
    cur = [int(idx[0])]
    for i in idx[1:]:
        if int(i) - cur[-1] <= 7:
            cur.append(int(i))
        else:
            groups.append(cur)
            cur = [int(i)]
    groups.append(cur)

    out = []
    for g in groups:
        block = dark[g[0]:g[-1] + 1]
        cols = np.where(block.sum(axis=0) > 0)[0]
        if len(cols) == 0:
            continue
        tx0, tx1 = x0 + int(cols.min()), x0 + int(cols.max())
        if tx1 - tx0 < 8:
            continue
        is_mine = tx0 > left + int(w * 0.17)
        box = (max(0, tx0 - 30), max(0, y0 + g[0] - 24),
               min(w, tx1 + 28), min(h, y0 + g[-1] + 20))
        out.append((box, is_mine))
    return out


def find_last_message(img):
    """最后一条消息（可能是自己发的）。"""
    blocks = _message_blocks(img)
    return blocks[-1] if blocks else None


def find_last_hers(img):
    """她最近发的一条（不管最后一条是谁发的）。"""
    for box, is_mine in reversed(_message_blocks(img)):
        if not is_mine:
            return box, False
    return None


def _set_clip(text: str):
    data = text.encode("utf-16-le") + b"\x00\x00"
    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    handle = k32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    ptr = k32.GlobalLock(handle)
    ctypes.memmove(ptr, data, len(data))
    k32.GlobalUnlock(handle)
    user32.SetClipboardData(CF_UNICODETEXT, handle)
    user32.CloseClipboard()


def get_clipboard() -> str:
    user32.OpenClipboard(None)
    handle = user32.GetClipboardData(CF_UNICODETEXT)
    if not handle:
        user32.CloseClipboard()
        return ""
    ptr = k32.GlobalLock(handle)
    text = ctypes.wstring_at(ptr) if ptr else ""
    k32.GlobalUnlock(handle)
    user32.CloseClipboard()
    return text


def copy_message(hwnd, x: int, y: int, menu_offset=(70, 0)) -> str:
    """右键气泡 → 点菜单里的「复制」→ 读剪贴板。坐标是窗口内坐标。"""
    left, top, _, _ = win32.rect(hwnd)
    sx, sy = left + x, top + y
    win32.right_click(sx, sy)
    time.sleep(0.9)
    win32.click(sx + menu_offset[0], sy + menu_offset[1])
    time.sleep(0.5)
    return get_clipboard().strip()

def chat_title(img: Image.Image) -> str:
    """聊天区顶部标题（当前会话的名字）。左边界用选中行算，避开左侧搜索框。"""
    w, h = img.size
    arr = np.asarray(img).astype(int)
    left = chat_left(arr)
    box = (max(0, left + 8), int(h * 0.05), int(w * 0.96), int(h * 0.20))
    return img.crop(box)