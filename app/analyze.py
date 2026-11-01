"""严格判定：计划内不超量=合规；超量=超；计划外=超。"""


def judge(parsed: dict, day: dict, meal: str) -> dict:
    if parsed.get("fasting"):
        return {"status": "fasting", "reasons": [], "items": []}
    items = parsed.get("items") or []
    if not items:
        return {"status": "unparsed", "reasons": [], "items": []}

    reasons = []
    for it in items:
        if not it["matched"]:
            reasons.append({"kind": "off_plan", "name": it["name"]})
        elif float(it["qty"]) > float(it["planned_qty"]) + 1e-9:
            reasons.append({"kind": "over_qty", "name": it["name"]})

    return {"status": "over" if reasons else "normal", "reasons": reasons, "items": items}
