import os

from flask import Flask, request
import requests

from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))


@app.route("/api/v1/telegramwebhook", methods=["POST"])
def telegramwebhook():
    assert (
        request.args["telegram_bot_webhook_token"]
        == os.environ["TELEGRAM_BOT_WEBHOOK_TOKEN"]
    )
    chat_id = request.json["message"]["chat"]["id"]
    telegram_key = os.environ["TELEGRAM_KEY"]
    telegram_response = requests.get(
        f"https://api.telegram.org/bot{telegram_key}/sendMessage",
        data={"chat_id": chat_id, "text": f"Received {request.data}"},
    )
    telegram_response.raise_for_status()
    return ("", 204)
