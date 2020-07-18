import os

from flask import Blueprint, session
import beeline
import psycopg2

from fructify.tracing import trace_cm


bp = Blueprint("googlecheck", __name__)


@bp.route("/api/v1/googlecheck")
def googlecheck():
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
                        has_google = cursor.rowcount == 1
        finally:
            connection.close()
    return {"hasGoogle": has_google}
