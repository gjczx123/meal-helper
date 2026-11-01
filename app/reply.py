"""话术：轻、短、不报数字、不列清单。"""
import random
import re

NORMAL = [
    "收到，今天这样挺好～",
    "好呀，记下啦，继续保持～",
    "不错不错，这个搭配可以～",
]

LIGHT_FASTING = "今天轻断，不吃也行，多喝水～"
NORMAL_FASTING = "记得吃点东西呀，别饿着～"


def _clean(name: str) -> str:
    return re.sub(r"[0-9]", "", name or "").strip()


def build(verdict: dict, day: dict, auto_reply: bool = True, warn_on_over: bool = True):
    status = verdict.get("status")
    if status == "unparsed":
        return None
    if not auto_reply:
        return None
    if status == "fasting":
        return LIGHT_FASTING if day.get("type") == "light" else NORMAL_FASTING
    if status == "over":
        if not warn_on_over:
            return None
        reasons = verdict.get("reasons") or []
        first = reasons[0] if reasons else {}
        if first.get("kind") == "off_plan":
            return f"「{_clean(first.get('name'))}」不在今天的计划里哦，晚上注意点～"
        if first.get("kind") == "over_qty":
            return "这个吃多啦，下次按计划来～"
        return "今天这个有点超哦，注意一下～"
    return random.choice(NORMAL)
