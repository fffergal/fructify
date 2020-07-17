import json
import os

from authlib.integrations.requests_client import OAuth2Session
from flask import Flask, session
import beeline
import psycopg2

from fructify.auth import set_secret_key
from fructify.tracing import trace_cm, with_flask_tracing


app = with_flask_tracing(Flask(__name__))
set_secret_key(app)


@app.route("/api/v1/googlecalendars")
def googlecalendars():
    sub = session.get("profile", {}).get("user_id")
    assert sub
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "lookup google transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with beeline.tracer("lookup google query"):
                        cursor.execute(
                            """
                            SELECT
                                google.token
                            FROM
                                link, google
                            WHERE
                                link.sub = %s
                                AND link.issuer_sub = google.issuer_sub
                            """,
                            (sub,),
                        )
                        assert cursor.rowcount == 1
                        (token_txt,) = next(cursor)

            def update_token(token, access_token=None, refresh_token=None):
                with trace_cm(connection, "update google transaction"):
                    with trace_cm(connection.cursor(), "cursor") as cursor:
                        with beeline.tracer("update google query"):
                            cursor.execute(
                                """
                                UPDATE
                                    google
                                SET
                                    token = %s
                                FROM
                                    link
                                WHERE
                                    link.sub = %s
                                    AND link.link_name = 'google'
                                    AND link.issuer_sub = google.issuer_sub
                                """,
                                (json.dumps(token), sub),
                            )

            google = OAuth2Session(
                client_id=os.environ["GOOGLE_CLIENT_ID"],
                client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
                token_endpoint="https://oauth2.googleapis.com/token",
                token=json.loads(token_txt),
                update_token=update_token,
            )
            response = google.get(
                "https://www.googleapis.com/calendar/v3/users/me/calendarList"
            )
            response.raise_for_status()
            return {
                "googleCalendars": [
                    {"id": calendar["id"], "summary": calendar["summary"]}
                    for calendar in response.json()["items"]
                ]
            }
        finally:
            connection.close()
