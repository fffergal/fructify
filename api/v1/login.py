from flask import Flask, request
from fructify.auth import add_auth0
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
auth0 = add_auth0(app)


@app.route("/api/v1/login")
def login():
    return auth0.authorize_redirect(
        redirect_uri=f"{request.url_root}api/v1/auth0callback"
    )
