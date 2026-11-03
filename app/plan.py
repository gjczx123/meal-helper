"""7 天轮转菜单。"""
from datetime import date


def parse_date(s: str) -> date:
    return date.fromisoformat(str(s)[:10])


def day_index(cycle_start: date, today: date) -> int:
    """返回 1..7，DAY1 为 cycle_start 当天。"""
    delta = (today - cycle_start).days
    if delta < 0:          # 起始日还没到，按第 1 天算
        return 1
    return delta % 7 + 1


def day_plan(plan: dict, today: date) -> dict:
    idx = day_index(parse_date(plan["cycle_start"]), today)
    for d in plan["days"]:
        if int(d["day"]) == idx:
            out = dict(d)
            out.setdefault("off_plan", plan.get("off_plan") or [])
            return out
    raise KeyError(f"菜单里没有 DAY{idx}")


def meal_items(day: dict, meal: str) -> list:
    return list((day.get("meals") or {}).get(meal) or [])