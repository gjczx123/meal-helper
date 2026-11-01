import unittest
from datetime import date, datetime

from app import db, plan as planmod, service
from app.config import load_config, load_plan
from tests.helpers import use_temp_home


class FakeSender:
    def __init__(self, ok=True):
        self.ok = ok
        self.sent = []

    def send(self, text, remark="", verify=None):
        self.sent.append(text)
        return self.ok


class FakeReader:
    def __init__(self, msgs):
        self.msgs = msgs
        self.calls = 0

    def poll(self, remark, since=None):
        self.calls += 1
        return self.msgs if self.calls == 1 else []


class ServiceTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()
        self.cfg = load_config()
        self.cfg["target_remark"] = "她"
        self.plan = load_plan()
        self.now = datetime(2026, 11, 1, 12, 30)

    def run_meal(self, reader, sender=None):
        return service.run_meal(self.cfg, self.plan, "午餐", sender or FakeSender(),
                                reader, now=self.now, sleep=lambda s: None,
                                wait_minutes=1, poll_seconds=0)

    def test_reply_recorded(self):
        r = self.run_meal(FakeReader([{"id": "x1", "text": "午餐肉一份，魔芋面", "ts": "12:31"}]))
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "normal")
        rec = db.by_date("2026-11-01")[0]
        self.assertEqual(rec["meal"], "午餐")

    def test_send_failure(self):
        r = self.run_meal(FakeReader([]), FakeSender(ok=False))
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "send_failed")

    def test_no_reply(self):
        r = service.run_meal(self.cfg, self.plan, "午餐", FakeSender(),
                             FakeReader([]), now=self.now, sleep=lambda s: None,
                             wait_minutes=0, poll_seconds=0)
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "no_reply")
