"""单实例锁（Windows 命名互斥体）。"""
import ctypes

_mutex = None
ERROR_ALREADY_EXISTS = 183


def acquire(name: str = "MealHelperSingleInstance") -> bool:
    global _mutex
    k32 = ctypes.windll.kernel32
    _mutex = k32.CreateMutexW(None, False, name)
    return k32.GetLastError() != ERROR_ALREADY_EXISTS
