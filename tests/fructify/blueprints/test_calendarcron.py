import unittest
from datetime import datetime

from fructify.blueprints import calendarcron


class CalendarcronTestCase(unittest.TestCase):
    def test_parse_event_time(self):
        self.assertEqual(
            calendarcron.parse_event_time({"date": "2020-08-09"}, "Europe/London"),
            datetime(2020, 8, 8, 23, 0),
        )

    def test_concat_unique(self):
        self.assertEqual(calendarcron.concat_unique([1, 2, 3], [2, 2, 4]), [1, 2, 3, 4])
