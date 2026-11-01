import unittest
from datetime import date

from app import parse
from app.config import load_plan
from app import plan as planmod
from tests.helpers import use_temp_home


class ParseTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()
        self.day = planmod.day_plan(load_plan(), date(2026, 11, 1))  # DAY1

    def test_alias_and_qty(self):
        r = parse.parse("吃了全麦面包两片", self.day, "早餐")
        self.assertEqual(len(r["items"]), 1)
        self.assertEqual(r["items"][0]["name"], "全麦吐司")
        self.assertEqual(r["items"][0]["qty"], 2.0)
        self.assertTrue(r["items"][0]["matched"])

    def test_off_plan(self):
        r = parse.parse("中午吃了米饭一碗", self.day, "午餐")
        names = [i["name"] for i in r["items"]]
        self.assertIn("米饭", names)
        self.assertFalse([i for i in r["items"] if i["name"] == "米饭"][0]["matched"])

    def test_fasting(self):
        r = parse.parse("没吃，不饿", self.day, "早餐")
        self.assertTrue(r["fasting"])
        self.assertEqual(r["items"], [])

    def test_empty(self):
        r = parse.parse("", self.day, "早餐")
        self.assertFalse(r["fasting"])
        self.assertEqual(r["items"], [])

    def test_plan_item_not_counted_twice(self):
        r = parse.parse("午餐肉一份，还有一包魔芋面", self.day, "午餐")
        names = sorted(i["name"] for i in r["items"])
        self.assertEqual(names, ["0脂荞麦魔芋面", "午餐肉"])
