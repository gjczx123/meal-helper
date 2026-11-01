"""配置与餐标（7 天菜单）的读写。"""
import json
import shutil
from datetime import date
from pathlib import Path

from . import paths

DEFAULT_CONFIG = {
    "target_remark": "",
    "meals": {
        "早餐": {"time": "08:30", "ask_text": "早上好呀，早餐吃了什么？记得报备哦～"},
        "午餐": {"time": "12:30", "ask_text": "中午啦，吃了什么呀？"},
        "晚餐": {"time": "18:30", "ask_text": "晚饭吃什么啦？记得报备～"},
    },
    "wait_minutes": 30,
    "poll_seconds": 15,
    "auto_reply": True,
    "warn_on_over": True,
    "keep_unlocked": True,
    "keep_days": 60,
    "wechat": {
        "process": "Weixin.exe",
        "title": "微信",
        "data_root": "",
    },
    "reader": {"calibrated": False, "menu_offset": [70, 0]},
    "vision": {
        "enabled": False,
        "api_key": "",
        "model": "doubao-1.5-vision-pro-32k-250115",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    },
}


class ConfigError(Exception):
    pass


def _read_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _seed(path: Path, default: dict):
    if path.exists():
        return
    src = Path(__file__).resolve().parent.parent / path.name
    if src.exists():
        shutil.copyfile(src, path)
    else:
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_time(t: str) -> str:
    """把 8:30 / 4:30 这类写法补成 08:30 / 04:30，避免旧配置把程序卡死。"""
    t = str(t).strip().replace("：", ":")
    if ":" in t:
        h, _, m = t.partition(":")
        if h.isdigit() and m.isdigit():
            return f"{int(h):02d}:{int(m):02d}"
    return t


def load_config() -> dict:
    p = paths.config_path()
    _seed(p, DEFAULT_CONFIG)
    cfg = _merge(DEFAULT_CONFIG, _read_json(p))
    for name, m in cfg["meals"].items():
        m["time"] = _normalize_time(m.get("time", ""))
    return cfg


def save_config(cfg: dict) -> None:
    p = paths.config_path()
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_plan() -> dict:
    p = paths.plan_path()
    _seed(p, {"cycle_start": date.today().isoformat(), "days": []})
    plan = _read_json(p)
    if not plan.get("days"):
        raise ConfigError("standards.json 里没有菜单（days 为空）")
    return plan


def save_plan(plan: dict) -> None:
    p = paths.plan_path()
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def _valid_time(t: str) -> bool:
    t = str(t).strip()
    if len(t) != 5 or t[2] != ":":
        return False
    h, m = t[:2], t[3:]
    if not (h.isdigit() and m.isdigit()):
        return False
    return 0 <= int(h) <= 23 and 0 <= int(m) <= 59


def validate_settings(cfg: dict) -> list:
    errs = []
    for name, m in cfg.get("meals", {}).items():
        m["time"] = _normalize_time(m.get("time", ""))
        if not _valid_time(str(m.get("time", ""))):
            errs.append(f"{name} 的时间应为 HH:MM")
        if not str(m.get("ask_text", "")).strip():
            errs.append(f"{name} 的提醒话术不能为空")
    if not str(cfg.get("target_remark", "")).strip():
        errs.append("她的微信备注不能为空")
    try:
        if int(cfg.get("wait_minutes", 0)) <= 0:
            errs.append("等待时间要大于 0 分钟")
    except Exception:
        errs.append("等待时间必须是数字")
    return errs