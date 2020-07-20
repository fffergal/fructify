from flask import Blueprint

from fructify.auth import oauth


bp = Blueprint("googlecalendars", __name__)


@bp.route("/api/v1/googlecalendars")
def googlecalendars():
    response = oauth.google.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    )
    response.raise_for_status()
    return {
        "googleCalendars": [
            {"id": calendar["id"], "summary": calendar["summary"]}
            for calendar in response.json()["items"]
        ]
    }
