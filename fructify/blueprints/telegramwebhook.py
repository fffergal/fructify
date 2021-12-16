import datetime
import os

from flask import Blueprint, request
import beeline
import psycopg2
import requests

from fructify.help import unwrap_heredoc
from fructify.tracing import trace_cm


bp = Blueprint("telegramwebhook", __name__)


@bp.route("/api/v1/telegramwebhook", methods=["POST"])
def telegramwebhook():
    if not request.json.get("message"):
        return ("", 204)
    assert (
        request.args["telegram_bot_webhook_token"]
        == os.environ["TELEGRAM_BOT_WEBHOOK_TOKEN"]
    )
    telegram_key = os.environ["TELEGRAM_KEY"]
    send_message_url = f"https://api.telegram.org/bot{telegram_key}/sendMessage"
    text = request.json["message"].get("text", "")
    chat_id = request.json["message"]["chat"]["id"]
    if text.startswith("/start"):
        secret = text.rsplit(" ", 1)[1]
        with beeline.tracer("db connection"):
            with beeline.tracer("open db connection"):
                connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
            try:
                with trace_cm(connection, "delete expired secrets transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("delete expired secrets query"):
                            cursor.execute(
                                "DELETE FROM secret WHERE expires < %s",
                                (datetime.datetime.utcnow(),),
                            )
                with trace_cm(connection, "lookup secret transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("lookup secret query"):
                            cursor.execute(
                                "SELECT sub FROM secret WHERE secret = %s", (secret,)
                            )
                            if cursor.rowcount:
                                (sub,) = next(cursor)
                            else:
                                telegram_response = requests.get(
                                    send_message_url,
                                    data={
                                        "chat_id": chat_id,
                                        "text": unwrap_heredoc(
                                            f"""
                                            Could not link this group to your Fructify
                                            account. Please go to <a
                                            href="{request.base_url}/dashboard">your
                                            Fructify dashboard</a> to link a Telegram
                                            group to your account.
                                            """
                                        ),
                                        "parse_mode": "HTML",
                                    },
                                )
                                telegram_response.raise_for_status()
                                return ("", 204)
                with trace_cm(connection, "link table exists transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("link table exists query"):
                            cursor.execute(
                                """
                                SELECT
                                    table_name
                                FROM
                                    information_schema.tables
                                WHERE
                                    table_name = 'link'
                                """
                            )
                        if not cursor.rowcount:
                            with beeline.tracer("create link table query"):
                                cursor.execute(
                                    """
                                    CREATE TABLE
                                        link (sub text, link_name text, issuer_sub text)
                                    """
                                )
                with trace_cm(connection, "link telegram transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("telegram link exists query"):
                            cursor.execute(
                                """
                                SELECT
                                    sub
                                FROM
                                    link
                                WHERE
                                    sub = %s
                                    AND link_name = 'telegram'
                                    AND issuer_sub = %s
                                """,
                                (sub, str(chat_id)),
                            )
                        if not cursor.rowcount:
                            with beeline.tracer("insert telegram link query"):
                                cursor.execute(
                                    """
                                    INSERT INTO
                                        link (sub, link_name, issuer_sub)
                                    VALUES
                                        (%s, 'telegram', %s)
                                    """,
                                    (sub, str(chat_id)),
                                )
                with trace_cm(connection, "telegram table exists transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("telegram table exists query"):
                            cursor.execute(
                                """
                                SELECT
                                    table_name
                                FROM
                                    information_schema.tables
                                WHERE
                                    table_name = 'telegram'
                                """
                            )
                        if not cursor.rowcount:
                            with beeline.tracer("create telegram table query"):
                                cursor.execute(
                                    """
                                    CREATE TABLE
                                        telegram (issuer_sub text, chat_title text)
                                    """
                                )
                with trace_cm(connection, "save telegram transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("telegram exists query"):
                            cursor.execute(
                                "SELECT issuer_sub FROM telegram WHERE issuer_sub = %s",
                                (str(chat_id),),
                            )
                        chat_title = request.json["message"]["chat"]["title"]
                        if cursor.rowcount:
                            with beeline.tracer("update telegram query"):
                                cursor.execute(
                                    """
                                    UPDATE
                                        telegram
                                    SET
                                        chat_title = %s
                                    WHERE
                                        issuer_sub = %s
                                    """,
                                    (chat_title, str(chat_id)),
                                )
                        else:
                            with beeline.tracer("insert telegram query"):
                                cursor.execute(
                                    """
                                    INSERT INTO
                                        telegram (
                                            issuer_sub,
                                            chat_title
                                        )
                                    VALUES
                                        (%s, %s)
                                    """,
                                    (str(chat_id), chat_title),
                                )
                with trace_cm(connection, "delete secret transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("delete secret query"):
                            cursor.execute(
                                "DELETE FROM secret WHERE secret = %s", (secret,)
                            )
                telegram_response = requests.get(
                    send_message_url,
                    data={
                        "chat_id": chat_id,
                        "text": "This group has been linked to your Fructify account.",
                    },
                )
                telegram_response.raise_for_status()
                return ("", 204)
            finally:
                connection.close()
    telegram_response = requests.get(
        send_message_url, data={"chat_id": chat_id, "text": f"Received {text}"}
    )
    telegram_response.raise_for_status()
    return ("", 204)
