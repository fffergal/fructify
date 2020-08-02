import os
from datetime import datetime, timedelta

import psycopg2
import requests
from beeline import add_context_field, tracer
from flask import Blueprint, g, request

from fructify.auth import oauth


EASYCRON_IPS = ["198.27.83.222", "192.99.21.124", "167.114.64.88", "167.114.64.21"]


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
                    "maxResults": "250",
                    "orderBy": "startTime",
                    "singleEvents": "true",
                    "timeMin": f"{start_minus_1m:%Y-%m-%dT%H:%M:%SZ}",
                    "timeZone": "Etc/UTC",
                },
            )
            events = events_response.json()["items"]
            for event in events:
                if "date" in event["start"]:
                    start = datetime.strptime(event["start"]["date"], "%Y-%m-%d")
                else:
                    start = datetime.strptime(
                        event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%SZ"
                    )
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
                        },
                    )
                    cron_response.raise_for_status()
                    error = cron_response.json().get("error", {}).get("message")
                    if error:
                        raise Exception(error)
            events_to_send = []
            for event in events:
                if "date" in event["start"]:
                    start = datetime.strptime(event["start"]["date"], "%Y-%m-%d")
                else:
                    start = datetime.strptime(
                        event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%SZ"
                    )
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
                    add_context_field("event_count", len(events_to_send))
                    add_context_field("chat_count", cursor.rowcount)
                    for (chat_id,) in cursor:
                        for event in events_to_send:
                            telegram_response = requests.get(
                                (
                                    f"https://api.telegram.org/bot{telegram_key}"
                                    "/sendMessage"
                                ),
                                data={
                                    "chat_id": chat_id,
                                    "text": f"{event['summary']}",
                                },
                            )
                            assert telegram_response.json()["ok"]
        finally:
            connection.close()
    return ("", 204)
