import os

from flask import Flask, redirect, session
from fructify.auth import add_google, add_oauth
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
oauth = add_oauth(app)
google = add_google(oauth)


@app.route("/api/v1/googlecallback")
def googlecallback():
    token = google.authorize_access_token()
    google.parse_id_token(token)
    return redirect("/dashboard.html")
