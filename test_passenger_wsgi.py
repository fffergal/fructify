import passenger_wsgi
from datetime import datetime


def test_days_until():
    assert (
        passenger_wsgi.days_until(datetime(2018, 1, 13, 6, 0), datetime(2018, 1, 15)) ==
        2
    )
