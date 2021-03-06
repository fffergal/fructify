import datetime
import os
from contextlib import suppress

import psycopg2
import requests
from beeline import add_context_field, tracer
from flask import Blueprint, g, request, url_for
from psycopg2.extras import execute_values

from fructify.auth import oauth
from fructify.blueprints.calendarcron import parse_event_time
from fructify.googleevents import find_event_summaries_starting, find_next_event_start


bp = Blueprint("googlecalendarwebhook", __name__)


@bp.route("/api/v1/googlecalendarwebhook", methods=["POST"])
def googlecalendarwebhook():
    external_id = request.headers["x-goog-channel-id"]
    add_context_field("goog_channel_id", external_id)
    add_context_field("goog_resource_id", request.headers["x-goog-resource-id"])
    expiry = datetime.datetime.strptime(
        request.headers["x-goog-channel-expiration"], "%a, %d %b %Y %H:%M:%S %Z"
    )
    add_context_field("goog_channel_expiration", f"{expiry:%Y-%m-%dT%H:%M:%SZ}")
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
                    if not cursor.rowcount:
                        # Google retries 500 errors, even for deleted channels. Return a
                        # 404 and it won't try again.
                        return ("", 404)
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

            # New code testing in prod so suppress any errors
            with suppress(Exception):
                try:
                    events_start = find_next_event_start(events_obj, now)
                except LookupError:
                    return ("", 204)
                summaries = find_event_summaries_starting(events_obj, events_start)
                with tracer("event_details table exists transaction"), connection:
                    with tracer("cursor"), connection.cursor() as cursor:
                        with tracer("event_details table exists query"):
                            cursor.execute(
                                """
                                SELECT
                                    table_name
                                FROM
                                    information_schema.tables
                                WHERE
                                    table_name = 'event_details'
                                """
                            )
                            if not cursor.rowcount:
                                with tracer("create event_details table query"):
                                    cursor.execute(
                                        """
                                        CREATE TABLE
                                            event_details (
                                                calendar_type text,
                                                calendar_id text,
                                                summary text
                                            )
                                        """
                                    )
                with tracer("update event_details transaction"), connection:
                    with tracer("cursor"), connection.cursor() as cursor:
                        with tracer("clear event_details query"):
                            cursor.execute(
                                """
                                DELETE FROM
                                    event_details
                                WHERE
                                    calendar_type = 'google'
                                    AND calendar_id = %s
                                """,
                                (google_calendar_id,),
                            )
                        with tracer("insert event_details query"):
                            execute_values(
                                cursor,
                                """
                                INSERT INTO
                                    event_details (
                                        calendar_type,
                                        calendar_id,
                                        summary
                                    )
                                VALUES %s
                                """,
                                [
                                    ("google", google_calendar_id, summary)
                                    for summary in summaries
                                ],
                            )

            return ("", 204)
        finally:
            connection.close()
