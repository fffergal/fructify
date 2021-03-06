import os

from flask import Blueprint, session
import beeline
import psycopg2

from fructify.tracing import trace_cm


bp = Blueprint("telegramchats", __name__)


@bp.route("/api/v1/telegramchats")
def telegramchats():
    sub = session.get("profile", {}).get("user_id")
    assert sub
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "lookup chats transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with beeline.tracer("lookup chats query"):
                        cursor.execute(
                            """
                            SELECT
                                telegram.issuer_sub, chat_title
                            FROM
                                link, telegram
                            WHERE
                                link.sub = %s
                                AND link.issuer_sub = telegram.issuer_sub
                            """,
                            (sub,),
                        )
                        return {
                            "telegramGroups": [
                                {"issuerSub": issuer_sub, "chatTitle": chat_title}
                                for issuer_sub, chat_title in cursor
                            ]
                        }
        finally:
            connection.close()
