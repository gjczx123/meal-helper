"""餐次会话：去重、合并多条消息。"""
from datetime import datetime

from . import db


class MealSession:
    def __init__(self, date: str, meal: str, asked_at: datetime):
        self.date = date
        self.meal = meal
        self.asked_at = asked_at
        self.status = "waiting"
        self.handled_msg_ids = set()

    def take_new(self, msgs: list) -> list:
        """过滤掉已处理过的消息，并标记为已处理。"""
        out = []
        for m in msgs or []:
            mid = str(m.get("id"))
            if mid in self.handled_msg_ids or db.is_seen(mid):
                continue
            self.handled_msg_ids.add(mid)
            db.mark_seen(mid)
            out.append(m)
        return out

    @staticmethod
    def merge_text(msgs: list) -> str:
        parts = [str(m.get("text") or "").strip() for m in msgs]
        return "，".join([p for p in parts if p])
