import json
import os

import beeline
import psycopg2
from authlib.integrations.flask_client import OAuth
from flask import g, session

from fructify.tracing import trace_cm


def fetch_google_token():
    sub = session.get("profile", {}).get("user_id") or getattr(g, "sub", None)
    assert sub
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "get google token transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with beeline.tracer("get google token query"):
                        cursor.execute(
                            """
                            SELECT
                                token
                            FROM
                                google, link
                            WHERE
                                link.sub = %s
                                AND link.link_name = 'google'
                                AND link.issuer_sub = google.issuer_sub
                            """,
                            (sub,),
                        )
                    if not cursor.rowcount:
                        raise LookupError
                    return json.loads(next(cursor)[0])
        finally:
            connection.close()


def update_google_token(token, refresh_token=None, access_token=None):
    userinfo = oauth.google.parse_id_token(token)
    with beeline.tracer("db connection"):
        with beeline.tracer("open db connection"):
            connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
        try:
            with trace_cm(connection, "google table maint transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with beeline.tracer("google table exists query"):
                        cursor.execute(
                            """
                            SELECT
                                table_name
                            FROM
                                information_schema.tables
                            WHERE
                                table_name = 'google'
                            """
                        )
                    if not cursor.rowcount:
                        with beeline.tracer("google table create query"):
                            cursor.execute(
                                "CREATE TABLE google (issuer_sub text, token text)"
                            )
            with trace_cm(connection, "save google token transaction"):
                with trace_cm(connection.cursor(), "cursor") as cursor:
                    with beeline.tracer("google token exists query"):
                        cursor.execute(
                            "SELECT issuer_sub FROM google WHERE issuer_sub = %s",
                            (userinfo["sub"],),
                        )
                    if cursor.rowcount:
                        with beeline.tracer("update google token query"):
                            cursor.execute(
                                "UPDATE google SET token = %s WHERE issuer_sub = %s",
                                (json.dumps(token), userinfo["sub"]),
                            )
                    else:
                        with beeline.tracer("insert google token query"):
                            cursor.execute(
                                """
                                INSERT INTO
                                    google (
                                        issuer_sub,
                                        token
                                    )
                                VALUES (%s, %s)
                                """,
                                (userinfo["sub"], json.dumps(token)),
                            )
        finally:
            connection.close()


oauth = OAuth()
oauth.register(
    "auth0",
    client_id=os.environ["AUTH0_CLIENT_ID"],
    client_secret=os.environ["AUTH0_CLIENT_SECRET"],
    api_base_url=f"https://{os.environ['AUTH0_DOMAIN']}",
    access_token_url=f"https://{os.environ['AUTH0_DOMAIN']}/oauth/token",
    authorize_url=f"https://{os.environ['AUTH0_DOMAIN']}/authorize",
    client_kwargs={"scope": "openid profile email"},
)
oauth.register(
    "google",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    authorize_params={"access_type": "offline"},
    client_kwargs={
        "scope": " ".join(
            [
                "openid",
                "profile",
                "email",
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/calendar.events.readonly",
            ]
        ),
        "prompt": "consent",
    },
    fetch_token=fetch_google_token,
    update_token=update_google_token,
)
