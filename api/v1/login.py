from flask import Flask, request
from fructify.auth import add_auth0, add_oauth
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
oauth = add_oauth(app)
auth0 = add_auth0(oauth)


@app.route("/api/v1/login")
def login():
    return auth0.authorize_redirect(
        redirect_uri=f"{request.url_root}api/v1/auth0callback"
    )
