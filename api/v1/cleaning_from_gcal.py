import datetime
import os

from flask import Flask, request
from fructify.tracing import with_flask_tracing, requests


GCAL_DATETIME_FORMAT = "%B %d, %Y at %I:%M%p"
TRELLO_USERS_TO_NAMES = {"@fffergal": "Fergal", "@annaarmstrong11": "Anna"}

app = with_flask_tracing(Flask(__name__))


@app.route("/api/v1/cleaning_from_gcal", methods=["POST"])
def cleaning_from_gcal():
    parsed_request = request.json
    gcal_datetime = parsed_request["datetime"]
    title = parsed_request["title"]
    trello_user = parsed_request["description"]
    parsed_datetime = datetime.datetime.strptime(gcal_datetime, GCAL_DATETIME_FORMAT)
    name = TRELLO_USERS_TO_NAMES.get(trello_user, "Someone")
    ifttt_key = os.environ["IFTTT_KEY"]
    telegram_response = requests.get(
        f"https://maker.ifttt.com/trigger/telegram_afb/with/key/{ifttt_key}",
        data={"value1": "{name}: {title}".format(name=name, title=title)},
    )
    telegram_response.raise_for_status()
    trello_response = requests.get(
        f"https://maker.ifttt.com/trigger/add_cleaning_trello/with/key/{ifttt_key}",
        data={
            "value1": "{title} ({parsed_datetime:%a %d %b})".format(
                title=title, parsed_datetime=parsed_datetime
            ),
            "value2": trello_user,
        },
    )
    trello_response.raise_for_status()
    return "\n".join(
        line
        for response in [telegram_response, trello_response]
        for line in response.iter_lines(decode_unicode=True)
    )
