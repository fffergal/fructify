import os
import uuid
from datetime import datetime, timedelta

import beeline
import psycopg2
import requests
from flask import Blueprint, request, session, url_for

from fructify.auth import oauth


bp = Blueprint("googletelegramlinks", __name__)


@bp.route("/api/v1/googletelegramlinks", methods=["PUT"])
def googletelegramlinks_put():
    """Link a calendar and chat in the database, and add a webhook for edits."""
    sub = session.get("profile", {}).get("user_id")
    assert sub
    google_calendar_id = request.json["googleCalendarId"]
    telegram_chat_id = request.json["telegramChatId"]
    calendar_list_response = oauth.google.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    )
    calendar_list_response.raise_for_status()
    calendar_ids = [
        calendar["id"] for calendar in calendar_list_response.json()["items"]
    ]
    assert google_calendar_id in calendar_ids
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with beeline.tracer("check chat ownership transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("check chat ownership query"):
                        cursor.execute(
                            """
                            SELECT
                                issuer_sub
                            FROM
                                link
                            WHERE
                                link_name = 'telegram'
                                AND sub = %s
                                AND issuer_sub = %s
                            """,
                            (sub, telegram_chat_id),
                        )
                    assert cursor.rowcount

            with beeline.tracer("calendarchatlink maintenance transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("calendarchatlink exists query"):
                        cursor.execute(
                            """
                            SELECT
                                table_name
                            FROM
                                information_schema.tables
                            WHERE
                                table_name = 'calendarchatlink'
                            """
                        )
                    if not cursor.rowcount:
                        with beeline.tracer("create calendatchatlink table query"):
                            cursor.execute(
                                """
                                CREATE TABLE
                                    calendarchatlink (
                                        external_id text,
                                        sub text,
                                        calendar_id text,
                                        calendar_type text,
                                        chat_id text,
                                        chat_type text
                                    )
                                """
                            )

            with beeline.tracer("googlewatch maintenance transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("googlewatch exists query"):
                        cursor.execute(
                            """
                            SELECT
                                table_name
                            FROM
                                information_schema.tables
                            WHERE
                                table_name = 'googlewatch'
                            """
                        )
                    if not cursor.rowcount:
                        with beeline.tracer("create googlewatch table query"):
                            cursor.execute(
                                """
                                CREATE TABLE
                                    googlewatch (
                                        external_id text,
                                        resource_id text,
                                        sub text,
                                        calendar_id text
                                    )
                                """
                            )

            with beeline.tracer("google telegram link exists transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("google telegram link exists query"):
                        cursor.execute(
                            """
                            SELECT
                                sub
                            FROM
                                calendarchatlink
                            WHERE
                                sub = %s
                                AND calendar_id = %s
                                AND calendar_type = 'google'
                                AND chat_id = %s
                                AND chat_type = 'telegram'
                            """,
                            (sub, google_calendar_id, telegram_chat_id),
                        )
                    if cursor.rowcount:
                        return ({"error": "link exists already"}, 400)

            with beeline.tracer("find googlewatch transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("googlewatch exists query"):
                        cursor.execute(
                            """
                            SELECT
                                external_id,
                                resource_id
                            FROM
                                googlewatch
                            WHERE
                                calendar_id = %s
                                AND sub = %s
                            """,
                            (google_calendar_id, sub),
                        )
                    if cursor.rowcount:
                        external_id, resource_id = next(cursor)
                    else:
                        external_id = str(uuid.uuid4())
                        resource_id = None

            with beeline.tracer("insert google telegram link transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("insert google telegram link query"):
                        cursor.execute(
                            """
                            INSERT INTO
                                calendarchatlink (
                                    external_id,
                                    sub,
                                    calendar_id,
                                    calendar_type,
                                    chat_id,
                                    chat_type
                                )
                            VALUES (%s, %s, %s, 'google', %s, 'telegram')
                            """,
                            (external_id, sub, google_calendar_id, telegram_chat_id),
                        )

            if not resource_id:
                request_expiration = datetime.utcnow() + timedelta(days=28)
                watch_response = oauth.google.post(
                    (
                        "https://www.googleapis.com/calendar/v3/calendars"
                        f"/{google_calendar_id}/events/watch"
                    ),
                    json={
                        "id": external_id,
                        "type": "web_hook",
                        "address": url_for(
                            "googlecalendarwebhook.googlecalendarwebhook",
                            _external=True,
                        ),
                        "expiration": int(request_expiration.timestamp() * 1000),
                    },
                )
                watch_response.raise_for_status()
                watch_json = watch_response.json()
                resource_id = watch_json["resourceId"]
                response_expiration = datetime.utcfromtimestamp(
                    int(watch_json["expiration"]) / 1000
                )
                with beeline.tracer("insert googlewatch transaction"), connection:
                    with beeline.tracer("cursor"), connection.cursor() as cursor:
                        with beeline.tracer("insert googlewatch query"):
                            cursor.execute(
                                """
                                INSERT INTO
                                    googlewatch (
                                        external_id,
                                        resource_id,
                                        sub,
                                        calendar_id
                                    )
                                VALUES
                                    (%s, %s, %s, %s)
                                """,
                                (external_id, resource_id, sub, google_calendar_id),
                            )

                with beeline.tracer(
                    "renewwatchcron maintenance transaction"
                ), connection:
                    with beeline.tracer("cursor"), connection.cursor() as cursor:
                        with beeline.tracer("renewwatchcron exists query"):
                            cursor.execute(
                                """
                                SELECT
                                    table_name
                                FROM
                                    information_schema.tables
                                WHERE
                                    table_name = 'renewwatchcron'
                                """
                            )
                        if not cursor.rowcount:
                            with beeline.tracer("renewwatchcron create query"):
                                cursor.execute(
                                    """
                                    CREATE TABLE
                                        renewwatchcron (
                                            sub text,
                                            external_id text,
                                            cron_id text
                                        )
                                    """
                                )

                cron_response = requests.get(
                    "https://www.easycron.com/rest/add",
                    params={
                        "token": os.environ["EASYCRON_KEY"],
                        "url": url_for(
                            "renewwatchcron.renewwatchcron",
                            _external=True,
                            external_id=external_id,
                        ),
                        "cron_expression": f"{response_expiration:%M %H %d %m * %Y}",
                        "timezone_from": "2",
                        "timezone": "UTC",
                    },
                )
                cron_response.raise_for_status()
                error = cron_response.json().get("error", {}).get("message")
                if error:
                    raise Exception(error)

                with beeline.tracer("insert renewwatchcron transaction"), connection:
                    with beeline.tracer("cursor"), connection.cursor() as cursor:
                        with beeline.tracer("insert renewwatchcron query"):
                            cursor.execute(
                                """
                                INSERT INTO
                                    renewwatchcron (
                                        sub,
                                        external_id,
                                        cron_id
                                    )
                                VALUES
                                    (%s, %s, %s)
                                """,
                                (sub, external_id, cron_response.json()["cron_job_id"]),
                            )
        finally:
            connection.close()
    return ({"message": "link created"}, 201)


@bp.route("/api/v1/googletelegramlinks")
def googletelegramlinks_get():
    """List calendar chat links for the user."""
    sub = session.get("profile", {}).get("user_id")
    assert sub
    response = oauth.google.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    )
    response.raise_for_status()
    calendars_by_id = {
        calendar["id"]: calendar["summary"] for calendar in response.json()["items"]
    }
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with beeline.tracer("calendar chat link transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("calendar chat link query"):
                        cursor.execute(
                            """
                            SELECT
                                calendarchatlink.external_id,
                                calendarchatlink.calendar_id,
                                telegram.chat_title
                            FROM
                                calendarchatlink,
                                telegram
                            WHERE
                                calendarchatlink.sub = %s
                                AND telegram.issuer_sub = calendarchatlink.chat_id
                                AND calendarchatlink.chat_type = 'telegram'
                                AND calendarchatlink.calendar_type = 'google'
                            """,
                            (sub,),
                        )
                    rows = list(cursor)
        finally:
            connection.close()
    return {
        "googleTelegramLinks": [
            {
                "externalId": row[0],
                "googleCalendarSummary": calendars_by_id[row[1]],
                "telegramChatTitle": row[2],
            }
            for row in rows
        ]
    }
