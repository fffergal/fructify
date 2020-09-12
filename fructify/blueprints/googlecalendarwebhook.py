import datetime
import os

import psycopg2
import requests
from beeline import tracer
from flask import Blueprint, g, request, url_for

from fructify.auth import oauth
from fructify.blueprints.calendarcron import parse_event_time


bp = Blueprint("googlecalendarwebhook", __name__)


@bp.route("/api/v1/googlecalendarwebhook", methods=["POST"])
def googlecalendarwebhook():
    external_id = request.headers["x-goog-channel-id"]
    now = datetime.datetime.utcnow()
    with tracer("db connection"):
        try:
            with tracer("open db connection"):
                connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
            with tracer("find google issuer_sub transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("find google issuer_sub query"):
                        cursor.execute(
                            """
                            SELECT
                                sub, calendar_id
                            FROM
                                calendarchatlink
                            WHERE
                                external_id = %s
                                AND calendar_type = 'google'
                            """,
                            (external_id,),
                        )
                    assert cursor.rowcount == 1
                    g.sub, google_calendar_id = next(cursor)
            events_response = oauth.google.get(
                (
                    "https://www.googleapis.com/calendar/v3/calendars"
                    f"/{google_calendar_id}/events"
                ),
                params={
                    "maxResults": "50",
                    "orderBy": "startTime",
                    "singleEvents": "true",
                    "timeMin": f"{now:%Y-%m-%dT%H:%M:%SZ}",
                    "timeZone": "Etc/UTC",
                },
            )
            events_obj = events_response.json()
            events = events_obj["items"]
            calendar_tz = events_obj["timeZone"]
            for event in events:
                start = parse_event_time(event["start"], calendar_tz)
                if start > now:
                    break
            else:  # no break
                return ("", 204)

            with tracer("calendarcron table exists transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("calendarcron table exists query"):
                        cursor.execute(
                            """
                            SELECT
                                table_name
                            FROM
                                information_schema.tables
                            WHERE
                                table_name = 'calendarcron'
                            """
                        )
                    if not cursor.rowcount:
                        with tracer("create calendarcron table query"):
                            cursor.execute(
                                """
                                CREATE TABLE
                                    calendarcron (
                                        sub text,
                                        calendar_id text,
                                        calendar_type text,
                                        cron_id text,
                                        next_event_start_time timestamp
                                    )
                                """
                            )
            with tracer("check next cron transaction"), connection:
                with tracer("cursor"), connection.cursor() as cursor:
                    with tracer("check next cron query"):
                        cursor.execute(
                            """
                            SELECT
                                cron_id,
                                next_event_start_time
                            FROM
                                calendarcron
                            WHERE
                                sub = %s
                                AND calendar_id = %s
                                AND calendar_type = 'google'
                            """,
                            (g.sub, google_calendar_id),
                        )
                    if cursor.rowcount:
                        cron_id, existing_next_start_time = next(cursor)
                        new_is_earlier = start < existing_next_start_time
                        old_has_passed = existing_next_start_time < now
                        if new_is_earlier or old_has_passed:
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
                                    (start, g.sub, google_calendar_id),
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
                                        next_event_start_time=(
                                            f"{start:%Y-%m-%dT%H:%M:%S}"
                                        ),
                                        calendar_id=google_calendar_id,
                                        calendar_type="google",
                                    ),
                                },
                            )
                            cron_response.raise_for_status()
                            error = cron_response.json().get("error", {}).get("message")
                            if error:
                                raise Exception(error)
                        return ("", 204)
                    else:
                        cron_response = requests.get(
                            "https://www.easycron.com/rest/add",
                            params={
                                "token": os.environ["EASYCRON_KEY"],
                                "url": url_for(
                                    "calendarcron.calendarcron",
                                    _external=True,
                                    next_event_start_time=(
                                        f"{start:%Y-%m-%dT%H:%M:%S}"
                                    ),
                                    calendar_id=google_calendar_id,
                                    calendar_type="google",
                                ),
                                "cron_expression": f"{start:%M %H %d %m * %Y}",
                                "timezone_from": "2",
                                "timezone": "UTC",
                            },
                        )
                        cron_response.raise_for_status()
                        error = cron_response.json().get("error", {}).get("message")
                        if error:
                            raise Exception(error)
                        with tracer("insert cron query"):
                            cursor.execute(
                                """
                                INSERT INTO
                                    calendarcron (
                                        sub,
                                        calendar_id,
                                        calendar_type,
                                        cron_id,
                                        next_event_start_time
                                    )
                                VALUES
                                    (%s, %s, 'google', %s, %s)
                                """,
                                (
                                    g.sub,
                                    google_calendar_id,
                                    cron_response.json()["cron_job_id"],
                                    start,
                                ),
                            )
                        return ("", 204)
        finally:
            connection.close()
