"""到点与补发的时间计算（纯逻辑）。"""
from datetime import datetime, timedelta


def _at(now: datetime, hhmm: str) -> datetime:
    hh, mm = [int(x) for x in hhmm.split(":")]
    return now.replace(hour=hh, minute=mm, second=0, microsecond=0)


def due_meals(now: datetime, meals_cfg: dict, sent: set, wait_minutes: int = 30) -> list:
    """到点但今天还没发、且还在等待窗口内的餐次。"""
    out = []
    for name, m in meals_cfg.items():
        if name in sent:
            continue
        t = _at(now, m["time"])
        if t <= now <= t + timedelta(minutes=wait_minutes):
            out.append(name)
    return out


def next_run(now: datetime, meals_cfg: dict) -> tuple:
    """返回 (下一次时间, 餐次名)；今天的都过了就取明天最早的一顿。"""
    best = None
    for name, m in meals_cfg.items():
        t = _at(now, m["time"])
        if t <= now:
            t = t + timedelta(days=1)
        if best is None or t < best[0]:
            best = (t, name)
    return best
