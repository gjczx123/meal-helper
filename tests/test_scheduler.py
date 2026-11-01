import unittest
from datetime import datetime

from app import scheduler

MEALS = {"早餐": {"time": "08:30"}, "午餐": {"time": "12:30"}, "晚餐": {"time": "18:30"}}


class SchedulerTest(unittest.TestCase):
    def test_due_in_window(self):
        now = datetime(2026, 11, 1, 8, 45)
        self.assertEqual(scheduler.due_meals(now, MEALS, set()), ["早餐"])

    def test_not_due_after_window(self):
        now = datetime(2026, 11, 1, 10, 0)
        self.assertEqual(scheduler.due_meals(now, MEALS, set()), [])

    def test_sent_skipped(self):
        now = datetime(2026, 11, 1, 8, 31)
        self.assertEqual(scheduler.due_meals(now, MEALS, {"早餐"}), [])

    def test_next_run(self):
        now = datetime(2026, 11, 1, 19, 0)
        t, name = scheduler.next_run(now, MEALS)
        self.assertEqual(name, "早餐")
        self.assertEqual(t.day, 2)
