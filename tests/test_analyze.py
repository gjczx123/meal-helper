import unittest
from datetime import date

from app import analyze, parse, plan as planmod
from app.config import load_plan
from tests.helpers import use_temp_home


class JudgeTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()
        self.day = planmod.day_plan(load_plan(), date(2026, 11, 1))

    def judge(self, text, meal):
        return analyze.judge(parse.parse(text, self.day, meal), self.day, meal)

    def test_in_plan_ok(self):
        self.assertEqual(self.judge("午餐肉一片，魔芋面", "午餐")["status"], "normal")

    def test_over_qty(self):
        v = self.judge("午餐肉两片", "午餐")
        self.assertEqual(v["status"], "over")
        self.assertEqual(v["reasons"][0]["kind"], "over_qty")

    def test_off_plan(self):
        v = self.judge("吃了一碗米饭", "午餐")
        self.assertEqual(v["status"], "over")
        self.assertEqual(v["reasons"][0]["kind"], "off_plan")

    def test_fasting(self):
        self.assertEqual(self.judge("没吃", "早餐")["status"], "fasting")

    def test_unparsed(self):
        self.assertEqual(self.judge("嗯嗯好的", "早餐")["status"], "unparsed")
