import os
from datetime import datetime, timedelta, timezone

import psycopg2
import requests
from backports.zoneinfo import ZoneInfo
from beeline import tracer
from flask import Blueprint, g, request, url_for

from fructify.auth import oauth
from fructify.constants import EASYCRON_IPS


bp = Blueprint("calendarcron", __name__)


@bp.route("/api/v1/calendarcron")
def calendarcron():
    assert request.remote_addr in EASYCRON_IPS
    now = datetime.utcnow()
    telegram_key = os.environ["TELEGRAM_KEY"]
    calendar_id = request.args["calendar_id"]
    calendar_type = request.args["calendar_type"]
    cron_start_time = datetime.strptime(
        request.args["next_event_start_time"], "%Y-%m-%dT%H:%M:%S"
    )
    with tracer("db connection"):
        try:
            with tracer("open db connection"):
                connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
            with tracer("find calendar cron transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("find calendar cron query"):
                        cursor.execute(
                            """
                            SELECT
                                sub, cron_id
                            FROM
                                calendarcron
                            WHERE
                                calendar_id = %s
                                AND calendar_type = %s
                            """,
                            (calendar_id, calendar_type),
                        )
                    assert cursor.rowcount
                    g.sub, cron_id = next(cursor)
            start_minus_1m = cron_start_time - timedelta(minutes=1)
            events_response = oauth.google.get(
                (
                    "https://www.googleapis.com/calendar/v3/calendars"
                    f"/{calendar_id}/events"
                ),
                params={
                    "maxResults": "50",
                    "orderBy": "startTime",
                    "singleEvents": "true",
                    "timeMin": f"{start_minus_1m:%Y-%m-%dT%H:%M:%SZ}",
                    "timeZone": "Etc/UTC",
                },
            )
            events_obj = events_response.json()
            calendar_tz = events_obj["timeZone"]
            events = events_obj["items"]
            for event in events:
                start = parse_event_time(event["start"], calendar_tz)
                if start > now:
                    break
            else:  # no break
                return ("", 204)
            with tracer("update cron time transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("update cron time query"):
                        cursor.execute(
                            """
                            UPDATE
                                calendarcron
                            SET
                                next_event_start_time = %s
                            WHERE
                                sub = %s
                                AND calendar_id = %s
                                AND calendar_type = 'google'
                            """,
                            (start, g.sub, calendar_id),
                        )
                    cron_response = requests.get(
                        "https://www.easycron.com/rest/edit",
                        params={
                            "token": os.environ["EASYCRON_KEY"],
                            "id": cron_id,
                            "cron_expression": f"{start:%M %H %d %m * %Y}",
                            "url": url_for(
                                "calendarcron.calendarcron",
                                _external=True,
                                next_event_start_time=f"{start:%Y-%m-%dT%H:%M:%S}",
                                calendar_id=calendar_id,
                                calendar_type="google",
                            ),
                        },
                    )
                    cron_response.raise_for_status()
                    error = cron_response.json().get("error", {}).get("message")
                    if error:
                        raise Exception(error)
            events_to_send = []
            for event in events:
                start = parse_event_time(event["start"], calendar_tz)
                if cron_start_time <= start <= now:
                    events_to_send.append(event)
            with tracer("find calendar chats transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("find calendar chats query"):
                        cursor.execute(
                            """
                            SELECT
                                chat_id
                            FROM
                                calendarchatlink
                            WHERE
                                sub = %s
                                AND calendar_id = %s
                                AND calendar_type = 'google'
                                AND chat_type = 'telegram'
                            """,
                            (g.sub, calendar_id),
                        )
                    rows = list(cursor)
        finally:
            connection.close()
    summaries = concat_unique([e["summary"] for e in events_to_send], [])
    with tracer("telegram sends"):
        for (chat_id,) in rows:
            telegram_response = requests.get(
                f"https://api.telegram.org/bot{telegram_key}/sendMessage",
                data={"chat_id": chat_id, "text": "\n".join(summaries)},
            )
            assert telegram_response.json()["ok"]
    return ("", 204)


def parse_event_time(time_playload, calendar_tz):
    """
    Parse a Gcal event time and timezone and return a naive datetime in UTC.

    The payload has different fields for a full datetime or just a date. Datetimes are
    assumed to be in UTC already as that can be forced in the Gcal request. Dates are
    for all day events, so the day begins at 0000 in the calendar's timezone.
    """
    if "date" in time_playload:
        midnight = datetime.strptime(time_playload["date"], "%Y-%m-%d")
        aware_time = midnight.replace(tzinfo=ZoneInfo(calendar_tz))
        return aware_time.astimezone(timezone.utc).replace(tzinfo=None)
    return datetime.strptime(time_playload["dateTime"], "%Y-%m-%dT%H:%M:%SZ")


def concat_unique(original, new):
    """Copy original and append all unique items in new if not in original."""
    copy = list(original)
    for item in new:
        if item not in copy:
            copy.append(item)
    return copy
