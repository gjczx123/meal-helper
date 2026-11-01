import re
import unittest
from datetime import date

from app import analyze, parse, plan as planmod, reply
from app.config import load_plan
from tests.helpers import use_temp_home


class ReplyTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()
        self.plan = load_plan()
        self.day = planmod.day_plan(self.plan, date(2026, 11, 1))
        self.light = planmod.day_plan(self.plan, date(2026, 11, 2))

    def verdict(self, text, meal="午餐"):
        return analyze.judge(parse.parse(text, self.day, meal), self.day, meal)

    def test_unparsed_silent(self):
        self.assertIsNone(reply.build(self.verdict("嗯"), self.day))

    def test_normal_reply(self):
        self.assertIsNotNone(reply.build(self.verdict("午餐肉"), self.day))

    def test_no_numbers(self):
        for text in ("午餐肉两片", "米饭", "奶茶"):
            r = reply.build(self.verdict(text), self.day) or ""
            self.assertIsNone(re.search(r"\d", r), r)
            self.assertNotIn("份", r)

    def test_warn_off(self):
        v = self.verdict("米饭")
        self.assertIsNone(reply.build(v, self.day, warn_on_over=False))

    def test_light_day_fasting_encourages(self):
        r = reply.build({"status": "fasting"}, self.light)
        self.assertIn("轻断", r)
