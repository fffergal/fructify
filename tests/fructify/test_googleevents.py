import unittest
from datetime import datetime

from fructify import googleevents


class GoogleeventsTestCase(unittest.TestCase):
    def test_find_next_event_start(self):
        self.assertEqual(
            googleevents.find_next_event_start(
                {
                    "items": [
                        {"start": {"dateTime": "2021-01-10T23:40:00Z"}},
                        {"start": {"dateTime": "2021-01-11T09:00:00Z"}},
                    ],
                    "timeZone": "Etc/UTC",
                },
                datetime(2021, 1, 10, 23, 49, 0),
            ),
            datetime(2021, 1, 11, 9, 0, 0),
        )

    def test_find_event_summaries_starting(self):
        self.assertEqual(
            list(
                googleevents.find_event_summaries_starting(
                    {
                        "items": [
                            {
                                "start": {"dateTime": "2021-01-10T09:00:00Z"},
                                "summary": "Event 1",
                            },
                            {
                                "start": {"dateTime": "2021-01-10T10:00:00Z"},
                                "summary": "Event 2",
                            },
                            {
                                "start": {"dateTime": "2021-01-10T10:00:00Z"},
                                "summary": "Event 3",
                            },
                            {
                                "start": {"dateTime": "2021-01-10T11:00:00Z"},
                                "summary": "Event 4",
                            },
                        ],
                        "timeZone": "Etc/UTC",
                    },
                    datetime(2021, 1, 10, 10, 0, 0),
                )
            ),
            ["Event 2", "Event 3"],
        )

    def test_parse_event_time(self):
        self.assertEqual(
            googleevents.parse_event_time({"date": "2020-08-09"}, "Europe/London"),
            datetime(2020, 8, 8, 23, 0),
        )
