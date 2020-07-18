import datetime
import unittest

from fructify.blueprints import days_until


class DaysUntilTestCase(unittest.TestCase):
    def test_days_until(self):
        self.assertEqual(
            days_until.days_until(
                datetime.datetime(2018, 1, 13, 6, 0), datetime.datetime(2018, 1, 15)
            ),
            2,
        )
