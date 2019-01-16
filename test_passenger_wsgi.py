import json
import logging
import time
from datetime import datetime

import pytest

import passenger_wsgi


def test_days_until():
    assert (
        passenger_wsgi.days_until(datetime(2018, 1, 13, 6, 0), datetime(2018, 1, 15)) ==
        2
    )


@pytest.fixture
def logger(tmpdir):
    logger = logging.getLogger("testlogger")
    handler = logging.FileHandler(str(tmpdir / "log.txt"))
    formatter = passenger_wsgi.JSONLogFormatter()
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)
    handler.close()


def test_jsonlogformatter(logger, tmpdir):
    logger.error("test %s", "yo")
    assert json.load(tmpdir / "log.txt")["message"] == "test yo"
