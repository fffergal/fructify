import unittest

from fructify.blueprints import calendarcron


class CalendarcronTestCase(unittest.TestCase):
    def test_concat_unique(self):
        self.assertEqual(calendarcron.concat_unique([1, 2, 3], [2, 2, 4]), [1, 2, 3, 4])
