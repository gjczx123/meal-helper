"""桌面通知。托盘可用时走托盘气泡，否则只写日志。"""
from . import logger

_sink = None


def set_sink(fn):
    global _sink
    _sink = fn


def notify(title: str, message: str):
    logger.get().info("notify: %s | %s", title, message)
    if _sink:
        try:
            _sink(title, message)
        except Exception:
            pass
