from flask import Flask, redirect, session
from fructify.auth import add_auth0
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
auth0 = add_auth0(app)


@app.route("/api/v1/auth0callback")
def auth0callback():
    auth0.authorize_access_token()
    resp = auth0.get("userinfo")
    userinfo = resp.json()
    session["jwt_payload"] = userinfo
    session["profile"] = {
        "user_id": userinfo["sub"],
        "name": userinfo["name"],
        "picture": userinfo["picture"],
    }
    return redirect("/dashboard.html")
