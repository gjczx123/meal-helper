import unittest
from datetime import date

from app import plan as planmod
from app.config import load_plan
from tests.helpers import use_temp_home


class PlanTest(unittest.TestCase):
    def setUp(self):
        use_temp_home()
        self.plan = load_plan()

    def test_rotation(self):
        start = date(2026, 11, 1)
        self.assertEqual(planmod.day_index(start, date(2026, 11, 1)), 1)
        self.assertEqual(planmod.day_index(start, date(2026, 11, 3)), 3)
        self.assertEqual(planmod.day_index(start, date(2026, 11, 8)), 1)

    def test_day_plan_has_meals(self):
        d = planmod.day_plan(self.plan, date(2026, 11, 1))
        self.assertEqual(d["day"], 1)
        self.assertTrue(planmod.meal_items(d, "早餐"))

    def test_light_days(self):
        d2 = planmod.day_plan(self.plan, date(2026, 11, 2))
        self.assertEqual(d2["type"], "light")
