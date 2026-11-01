"""一顿饭的完整流程：发送 → 等待 → 读取 → 判定 → 记账 → 回复。"""
import time
from datetime import datetime, timedelta

from . import analyze, db, logger, notify, parse, reply
from . import plan as planmod
from .state import MealSession


def run_meal(cfg: dict, plan: dict, meal: str, sender, reader,
             now: datetime = None, sleep=time.sleep,
             wait_minutes: int = None, poll_seconds: int = None) -> dict:
    now = now or datetime.now()
    today = now.date()
    wait_minutes = int(wait_minutes if wait_minutes is not None else cfg.get("wait_minutes", 30))
    poll_seconds = int(poll_seconds if poll_seconds is not None else cfg.get("poll_seconds", 15))
    remark = cfg.get("target_remark", "")
    log = logger.get()

    try:
        day = planmod.day_plan(plan, today)
    except Exception as e:
        log.error("菜单读取失败：%s", e)
        notify.notify("菜单读不到", str(e))
        return {"ok": False, "reason": "plan_error"}

    ask = cfg["meals"][meal]["ask_text"]
    session = MealSession(today.isoformat(), meal, now)

    sent_ok = False
    try:
        sent_ok = bool(sender.send(ask, remark))
    except Exception as e:
        log.exception("发送异常：%s", e)
        sent_ok = False

    db.log("ask", remark, ask, 1 if sent_ok else 0,
           "" if sent_ok else "send failed")

    if not sent_ok:
        db.insert_meal({
            "date": today.isoformat(), "meal": meal, "msg_time": now.strftime("%H:%M:%S"),
            "source": "system", "raw_text": "", "status": "missed",
            "verdict_reason": "提醒没发出去", "plan_day": day.get("day"),
        })
        notify.notify("提醒没发出去", f"{meal}的提醒发送失败，请检查微信窗口")
        return {"ok": False, "reason": "send_failed"}

    deadline = time.monotonic() + wait_minutes * 60
    msgs = []
    while time.monotonic() < deadline:
        try:
            batch = reader.poll(remark, since=now) or []
        except Exception as e:
            log.exception("读消息异常：%s", e)
            notify.notify("读消息失败", str(e))
            batch = []
        new = session.take_new(batch)
        if new:
            msgs = new
            break
        sleep(poll_seconds)

    if not msgs:
        db.insert_meal({
            "date": today.isoformat(), "meal": meal, "msg_time": "",
            "source": "none", "raw_text": "", "status": "missed",
            "verdict_reason": "等待窗口内没有回复", "plan_day": day.get("day"),
        })
        return {"ok": False, "reason": "no_reply"}

    text = session.merge_text(msgs)
    image_path = next((m.get("image_path") for m in msgs if m.get("image_path")), "")
    source = "image" if image_path else "text"

    parsed = parse.parse(text, day, meal)
    verdict = analyze.judge(parsed, day, meal)
    answer = reply.build(verdict, day, cfg.get("auto_reply", True), cfg.get("warn_on_over", True))

    rid = db.insert_meal({
        "date": today.isoformat(),
        "meal": meal,
        "msg_time": str(msgs[0].get("ts") or ""),
        "source": source,
        "raw_text": text,
        "image_path": image_path,
        "plan_day": day.get("day"),
        "items": verdict.get("items", []),
        "status": verdict["status"],
        "verdict_reason": "、".join(r["name"] for r in verdict.get("reasons", [])),
        "analysis": verdict,
        "reply_text": answer or "",
        "sent_at": datetime.now().strftime("%H:%M:%S"),
        "verify_ok": 1,
    })

    if answer:
        try:
            sender.send(answer, remark)
            db.log("reply", remark, answer, 1)
        except Exception as e:
            log.exception("回复发送失败：%s", e)
            db.log("reply", remark, answer, 0, str(e))

    return {"ok": True, "record_id": rid, "status": verdict["status"],
            "text": text, "reply": answer, "day": day.get("day")}