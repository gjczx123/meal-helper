"""落盘日志。"""
import logging
from datetime import datetime

from . import paths

_ready = False


def get(name: str = "meal") -> logging.Logger:
    global _ready
    logger = logging.getLogger(name)
    if not _ready:
        fh = logging.FileHandler(paths.log_dir() / f"app-{datetime.now():%Y-%m-%d}.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        _ready = True
    return logger
