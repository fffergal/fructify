import json
import os

import beeline
import psycopg2

from flask import Flask, redirect, session
from fructify.auth import add_google, add_oauth
from fructify.tracing import with_flask_tracing, trace_call, trace_cm


app = with_flask_tracing(Flask(__name__))
oauth = add_oauth(app)
google = add_google(oauth)


@app.route("/api/v1/googlecallback")
def googlecallback():
    token = google.authorize_access_token()
    userinfo = google.parse_id_token(token)
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
            with trace_cm(connection, "google table maint transaction"):
                with trace_cm(
                    connection.cursor(), "google table maint cursor"
                ) as cursor:
                    with beeline.tracer("google table exists query"):
                        cursor.execute(
                            "SELECT table_name FROM information_schema.tables"
                        )
                    if ("google",) not in list(cursor):
                        trace_call("google table create query")(cursor.execute)(
                            "CREATE TABLE google (issuer_sub text, token text)"
                        )
            with trace_cm(connection, "save google token transaction"):
                with trace_cm(
                    connection.cursor(), "save google token cursor"
                ) as cursor:
                    trace_call("google token exists query")(cursor.execute)(
                        "SELECT issuer_sub FROM google WHERE issuer_sub = %s",
                        (userinfo["sub"],),
                    )
                    if cursor.rowcount:
                        trace_call("update google token query")(cursor.execute)(
                            "UPDATE google SET token = %s WHERE issuer_sub = %s",
                            (json.dumps(token), userinfo["sub"]),
                        )
                    else:
                        trace_call("insert google token query")(cursor.execute)(
                            "INSERT INTO google (issuer_sub, token) VALUES (%s, %s)",
                            (userinfo["sub"], json.dumps(token)),
                        )
        finally:
            connection.close()
    return redirect("/dashboard")
