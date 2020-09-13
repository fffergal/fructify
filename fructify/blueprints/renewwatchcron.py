import os
from datetime import datetime

import beeline
import psycopg2
import requests
from flask import Blueprint, g, request, url_for

from fructify.auth import oauth
from fructify.constants import EASYCRON_IPS


bp = Blueprint("renewwatchcron", __name__)


@bp.route("/api/v1/renewwatchcron")
def renewwatchcron():
    assert request.remote_addr in EASYCRON_IPS
    external_id = request.args["external_id"]
    with beeline.tracer("db connection"):
        try:
            with beeline.tracer("open db connection"):
                connection = psycopg2.connect(os.environ["POSTGRES_DSN"])
            with beeline.tracer("find renewwatchcron transaction"), connection:
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("find renewwatchcron query"):
                        cursor.execute(
                            """
                            SELECT
                                sub, cron_id
                            FROM
                                renewwatchcron
                            WHERE
                                external_id = %s
                            """,
                            (external_id,),
                        )
                    assert cursor.rowcount
                    g.sub, cron_id = next(cursor)
            with beeline.tracer("find googlewatch transaction"):
                with beeline.tracer("cursor"), connection.cursor() as cursor:
                    with beeline.tracer("find googlewatch query"):
                        cursor.execute(
                            """
                            SELECT
                                resource_id,
                                calendar_id
                            FROM
                                googlewatch
                            WHERE
                                external_id = %s
                            """,
                            (external_id,),
                        )
                    resource_id, calendar_id = next(cursor)
        finally:
            connection.close()
    stop_response = oauth.google.post(
        "https://www.googleapis.com/calendar/v3/channels/stop",
        json={"id": external_id, "resourceId": resource_id},
    )
    assert stop_response.ok or stop_response.status_code == 404
    watch_response = oauth.google.post(
        (
            "https://www.googleapis.com/calendar/v3/calendars"
            f"/{calendar_id}/events/watch"
        ),
        json={
            "id": external_id,
            "type": "web_hook",
            "address": url_for(
                "googlecalendarwebhook.googlecalendarwebhook", _external=True
            ),
            # 28 days in milliseconds
            "expiration": 2_419_200_000,
        },
    )
    watch_response.raise_for_status()
    expiration = datetime.utcfromtimestamp(
        int(watch_response.json()["expiration"]) / 1000
    )
    cron_response = requests.get(
        "https://www.easycron.com/rest/edit",
        params={
            "token": os.environ["EASYCRON_KEY"],
            "id": cron_id,
            "cron_expression": f"{expiration:%M %H %d %m * %Y}",
            "url": url_for(
                "renewwatchcron.renewwatchcron",
                _external=True,
                external_id=external_id,
            ),
        },
    )
    cron_response.raise_for_status()
    error = cron_response.json().get("error", {}).get("message")
    if error:
        raise Exception(error)
    return ("", 204)
