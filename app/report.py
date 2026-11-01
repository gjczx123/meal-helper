"""周报：最近 7 天的记账汇总。"""
from collections import Counter
from datetime import date, timedelta

from . import db

LABEL = {"normal": "正常", "over": "超标", "fasting": "未进食",
         "unparsed": "未识别", "missed": "未报备"}


def weekly_text(ref: date = None, days: int = 7) -> str:
    ref = ref or date.today()
    rows = db.recent(600)
    by_day = {}
    over_counter = Counter()
    for r in rows:
        by_day.setdefault(r["date"], []).append(r)
        if r["status"] == "over":
            for name in (r.get("verdict_reason") or "").split("、"):
                if name.strip():
                    over_counter[name.strip()] += 1

    lines = [f"三餐助手 · 最近 {days} 天汇总"]
    total = {"normal": 0, "over": 0, "fasting": 0, "unparsed": 0, "missed": 0}
    for i in range(days - 1, -1, -1):
        d = (ref - timedelta(days=i)).isoformat()
        recs = by_day.get(d, [])
        if not recs:
            lines.append(f"{d[5:]}  没有记录")
            continue
        cnt = Counter(r["status"] for r in recs)
        for k in total:
            total[k] += cnt.get(k, 0)
        parts = " ".join(f"{LABEL[k]} {cnt[k]}" for k in LABEL if cnt.get(k))
        lines.append(f"{d[5:]}  {parts}")
    lines.append("")
    lines.append("合计：" + "  ".join(f"{LABEL[k]} {v}" for k, v in total.items() if v))
    if over_counter:
        top = "、".join(f"{n}（{c}次）" for n, c in over_counter.most_common(3))
        lines.append("最常超标：" + top)
    return "\n".join(lines)
