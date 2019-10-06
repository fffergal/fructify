import contextlib
import datetime
import json
import os
import urllib


def app(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return ["POST only please"]
    with contextlib.closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    parsed_request = json.loads(request_body)
    from_date = parsed_request["from_date"]
    target_date = parsed_request["target_date"]
    target_label = parsed_request["target_label"]
    parsed_from_date = datetime.datetime.strptime(from_date, "%B %d, %Y at %I:%M%p")
    parsed_target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
    safe_target_label = target_label[:50]
    days = days_until(parsed_from_date, parsed_target_date)
    ifttt_key = os.environ["IFTTT_KEY"]
    request = urllib.request.Request(
        f"https://maker.ifttt.com/trigger/notify/with/key/{ifttt_key}",
        bytes(
            json.dumps(
                {
                    "value1": "{days} days until {safe_target_label}.".format(
                        days=days, safe_target_label=safe_target_label
                    )
                }
            ),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with contextlib.closing(urllib.request.urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def days_until(date_from, date_to):
    return (date_to - date_from).days + 1
