import unittest
from datetime import datetime

from app import state
from tests.helpers import use_temp_home


class StateTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()

    def test_dedupe(self):
        s = state.MealSession("2026-11-01", "早餐", datetime.now())
        a = s.take_new([{"id": "m1", "text": "a"}])
        b = s.take_new([{"id": "m1", "text": "a"}])
        self.assertEqual(len(a), 1)
        self.assertEqual(b, [])

    def test_merge(self):
        s = state.MealSession("2026-11-01", "早餐", datetime.now())
        t = s.merge_text([{"text": "吃了"}, {"text": "鸡蛋"}])
        self.assertEqual(t, "吃了，鸡蛋")
