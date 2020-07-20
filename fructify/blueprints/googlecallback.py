import os

import beeline
import psycopg2

from flask import Blueprint, redirect, session
from fructify.auth import oauth, update_google_token
from fructify.tracing import trace_call, trace_cm


bp = Blueprint("googlecallback", __name__)


@bp.route("/api/v1/googlecallback")
def googlecallback():
    token = oauth.google.authorize_access_token()
    update_google_token(token)
    userinfo = oauth.google.parse_id_token(token)
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "link table maint transaction"):
                with trace_cm(connection.cursor(), "link table maint cursor") as cursor:
                    with beeline.tracer("link table exists query"):
                        cursor.execute(
                            "SELECT table_name FROM information_schema.tables"
                        )
                    if ("link",) not in list(cursor):
                        with beeline.tracer("link table create query"):
                            cursor.execute(
                                """
                                CREATE TABLE
                                    link (sub text, link_name text, issuer_sub text)
                                """
                            )
            with trace_cm(connection, "link google transaction"):
                with trace_cm(connection.cursor(), "link google cursor") as cursor:
                    trace_call("google link exists query")(cursor.execute)(
                        "SELECT sub FROM link WHERE sub = %s AND link_name = 'google'",
                        (session["profile"]["user_id"],),
                    )
                    if cursor.rowcount:
                        trace_call("update google link query")(cursor.execute)(
                            """
                            UPDATE
                                link
                            SET
                                issuer_sub = %s
                            WHERE
                                sub = %s
                                AND link_name = 'google'
                            """,
                            (userinfo["sub"], session["profile"]["user_id"]),
                        )
                    else:
                        trace_call("insert google link query")(cursor.execute)(
                            """
                            INSERT INTO
                                link (sub, link_name, issuer_sub)
                            VALUES
                                (%s, 'google', %s)
                            """,
                            (session["profile"]["user_id"], userinfo["sub"]),
                        )
        finally:
            connection.close()
    return redirect("/dashboard")
