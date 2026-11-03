"""三餐助手 · 应用包"""
__version__ = "1.2.1"

import datetime
import sys
from pathlib import Path


def build_stamp() -> str:
    """当前二进制的构建时间，用来确认跑的是不是新版本。"""
    try:
        p = Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__).resolve()
        return datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "?"