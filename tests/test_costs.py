import unittest
from costs import estimate_cost


class CostTests(unittest.TestCase):
    def test_one_instance(self):
        self.assertAlmostEqual(estimate_cost(0.1, 10, 1), 1.0)

    def test_three_instances(self):
        self.assertAlmostEqual(estimate_cost(0.1, 10, 3), 3.0)

    def test_zero_instances(self):
        self.assertEqual(estimate_cost(0.1, 10, 0), 0)

    def test_zero_hours(self):
        self.assertEqual(estimate_cost(0.1, 0, 3), 0)

    def test_zero_rate(self):
        self.assertEqual(estimate_cost(0, 10, 3), 0)

    def test_fractional_hours(self):
        self.assertAlmostEqual(estimate_cost(0.2, 1.5, 2), 0.6)

    def test_negative_inputs(self):
        for args in [(-1, 10, 1), (1, -10, 1), (1, 10, -1)]:
            with self.assertRaises(ValueError):
                estimate_cost(*args)
