import datetime
import os

from flask import Blueprint, request
import requests


bp = Blueprint("days_until", __name__)


@bp.route("/api/v1/days_until", methods=["POST"])
def days_until_route():
    parsed_request = request.json
    from_date = parsed_request["from_date"]
    target_date = parsed_request["target_date"]
    target_label = parsed_request["target_label"]
    parsed_from_date = datetime.datetime.strptime(from_date, "%B %d, %Y at %I:%M%p")
    parsed_target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    safe_target_label = target_label[:50]
    days = days_until(parsed_from_date, parsed_target_date)
    ifttt_key = os.environ["IFTTT_KEY"]
    response = requests.get(
        f"https://maker.ifttt.com/trigger/notify/with/key/{ifttt_key}",
        data={
            "value1": "{days} days until {safe_target_label}.".format(
                days=days, safe_target_label=safe_target_label
            )
        },
    )
    return response.text


def days_until(date_from, date_to):
    return (date_to - date_from).days + 1
