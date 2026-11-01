"""数据目录与资源定位。打包成 exe 后依然可用。"""
import os
import sys
from pathlib import Path

APP_NAME = "三餐助手"


def home() -> Path:
    """数据目录：%APPDATA%/三餐助手（可用 MEALHELPER_HOME 覆盖，便于测试）。"""
    env = os.environ.get("MEALHELPER_HOME")
    p = Path(env) if env else Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def resource(name: str) -> Path:
    """随程序分发的只读资源（图标等）。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "assets" / name


def db_path() -> Path:
    return home() / "meals.db"


def config_path() -> Path:
    return home() / "config.json"


def plan_path() -> Path:
    return home() / "standards.json"


def log_dir() -> Path:
    d = home() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def photos_dir() -> Path:
    d = home() / "photos"
    d.mkdir(parents=True, exist_ok=True)
    return d
