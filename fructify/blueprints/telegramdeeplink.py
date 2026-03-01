import datetime
import os
import secrets

from flask import Blueprint, session
from fructify.tracing import tracer
import psycopg2

from fructify.tracing import trace_cm

bp = Blueprint("telegramdeeplink", __name__)


@bp.route("/api/v1/telegramdeeplink")
def telegramdeeplink():
    sub = session.get("profile", {}).get("user_id")
    assert sub
    with tracer.start_as_current_span("db connection"):
        with tracer.start_as_current_span("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "secret table exists transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with tracer.start_as_current_span("secret table exists query"):
                        cursor.execute(
                            """
                            SELECT
                                table_name
                            FROM
                                information_schema.tables
                            WHERE
                                table_name = 'secret'
                            """
                        )
                    if not cursor.rowcount:
                        with tracer.start_as_current_span("create secret table query"):
                            cursor.execute(
                                """
                                CREATE TABLE
                                    secret (
                                        sub text,
                                        secret text,
                                        expires timestamp
                                    )
                                """
                            )
            with trace_cm(connection, "delete expired secrets transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with tracer.start_as_current_span("delete expired secrets query"):
                        cursor.execute(
                            "DELETE FROM secret WHERE expires < %s",
                            (datetime.datetime.utcnow(),),
                        )
            with trace_cm(connection, "create new secret transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    secret = secrets.token_urlsafe(16)
                    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                    with tracer.start_as_current_span("insert new secret query"):
                        cursor.execute(
                            """
                            INSERT INTO
                                secret (
                                    sub,
                                    secret,
                                    expires
                                )
                            VALUES
                                (%s, %s, %s)
                            """,
                            (sub, secret, expires),
                        )
        finally:
            connection.close()
    bot_name = os.environ["TELEGRAM_BOT_NAME"]
    return {"deeplinkUrl": f"https://t.me/{bot_name}?startgroup={secret}"}
