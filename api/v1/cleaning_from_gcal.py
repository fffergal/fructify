import contextlib
import datetime
import json
import os
import urllib.request

from fructify.tracing import with_tracing


GCAL_DATETIME_FORMAT = "%B %d, %Y at %I:%M%p"
TRELLO_USERS_TO_NAMES = {"@fffergal": "Fergal", "@annaarmstrong11": "Anna"}


@with_tracing
def app(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return ["POST only please"]
    with contextlib.closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    parsed_request = json.loads(request_body)
    gcal_datetime = parsed_request["datetime"]
    title = parsed_request["title"]
    trello_user = parsed_request["description"]
    parsed_datetime = datetime.datetime.strptime(gcal_datetime, GCAL_DATETIME_FORMAT)
    name = TRELLO_USERS_TO_NAMES.get(trello_user, "Someone")
    ifttt_key = os.environ["IFTTT_KEY"]
    telegram_request = urllib.request.Request(
        f"https://maker.ifttt.com/trigger/telegram_afb/with/key/{ifttt_key}",
        bytes(
            json.dumps({"value1": "{name}: {title}".format(name=name, title=title)}),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with contextlib.closing(urllib.request.urlopen(telegram_request)) as response:
        lines = list(response.readlines())
    trello_request = urllib.request.Request(
        f"https://maker.ifttt.com/trigger/add_cleaning_trello/with/key/{ifttt_key}",
        bytes(
            json.dumps(
                {
                    "value1": "{title} ({parsed_datetime:%a %d %b})".format(
                        title=title, parsed_datetime=parsed_datetime
                    ),
                    "value2": trello_user,
                }
            ),
            "utf-8",
        ),
        {"Content-type": "application/json"},
    )
    with contextlib.closing(urllib.request.urlopen(trello_request)) as response:
        lines.extend(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines
