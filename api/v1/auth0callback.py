from flask import Flask, redirect, session
from fructify.auth import add_auth0, add_oauth
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
oauth = add_oauth(app)
auth0 = add_auth0(oauth)


@app.route("/api/v1/auth0callback")
def auth0callback():
    auth0.authorize_access_token()
    resp = auth0.get("userinfo")
    userinfo = resp.json()
    session["profile"] = {
        "user_id": userinfo["sub"],
    }
    return redirect("/dashboard.html")
