"""把她的回复解析成条目：计划内的命中 + 计划外的关键词。"""
import re

FASTING_WORDS = ("没吃", "不饿", "不吃", "没胃口", "没来得及", "跳过", "没时间吃", "忘了吃")

_NUM = {"半": 0.5, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

_QTY = re.compile(r"(\d+|[一二两三四五六七八九十半])\s*[份个片袋碗杯根块盒包瓶只]?")


def is_fasting(text: str) -> bool:
    t = (text or "").strip()
    return any(w in t for w in FASTING_WORDS)


def _to_num(tok: str) -> float:
    if tok in _NUM:
        return float(_NUM[tok])
    try:
        return float(tok)
    except ValueError:
        return 1.0


def _qty_near(text: str, start: int, end: int) -> float:
    # 只在同一小句里找数量词，避免把邻居的数量算到自己头上
    lo = max(text.rfind(c, 0, start) for c in "，,。；;、\n") + 1
    hi_candidates = [text.find(c, end) for c in "，,。；;、\n"]
    hi_candidates = [i for i in hi_candidates if i != -1]
    hi = min(hi_candidates) if hi_candidates else len(text)
    lo, hi = max(lo, start - 6), min(hi, end + 6)
    win = text[lo:hi]
    hits = list(_QTY.finditer(win))
    if not hits:
        return 1.0
    center = (start - lo + end - lo) / 2
    best = min(hits, key=lambda m: abs((m.start() + m.end()) / 2 - center))
    return _to_num(best.group(1))


def parse(text: str, day: dict, meal: str) -> dict:
    """返回 {"fasting": bool, "items": [{name, qty, matched, planned_qty}]}"""
    raw = (text or "").strip()
    if not raw:
        return {"fasting": False, "items": []}
    if is_fasting(raw):
        return {"fasting": True, "items": []}

    items = []
    spans = []
    for mi in (day.get("meals") or {}).get(meal) or []:
        aliases = sorted(mi.get("aliases") or [mi["name"]], key=len, reverse=True)
        hit = None
        for a in aliases:
            idx = raw.find(a)
            if idx >= 0 and not any(s <= idx < e for s, e in spans):
                hit = (idx, idx + len(a), a)
                break
        if hit:
            s, e, _ = hit
            spans.append((s, e))
            items.append({
                "name": mi["name"],
                "qty": _qty_near(raw, s, e),
                "matched": True,
                "planned_qty": float(mi.get("qty", 1)),
            })

    leftover = raw
    for s, e in sorted(spans, reverse=True):
        leftover = leftover[:s] + " " * (e - s) + leftover[e:]

    for kw in (day.get("off_plan") or []) + ["奶茶", "可乐", "炸鸡", "米饭", "面条", "薯条", "蛋糕"]:
        if kw and kw in leftover and not any(i["name"] == kw for i in items):
            items.append({"name": kw, "qty": 1.0, "matched": False, "planned_qty": None})
            leftover = leftover.replace(kw, " ")

    return {"fasting": False, "items": items}