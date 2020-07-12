from flask import Flask, request, session
from fructify.auth import add_google, add_oauth, set_secret_key
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
set_secret_key(app)
oauth = add_oauth(app)
google = add_google(oauth)


@app.route("/api/v1/googlelink")
def googlelink():
    assert session.get("profile", {}).get("user_id")
    return google.authorize_redirect(
        redirect_uri=f"{request.url_root}api/v1/googlecallback"
    )
