from flask import Blueprint, redirect, session
from fructify.auth import oauth


bp = Blueprint("auth0callback", __name__)


@bp.route("/api/v1/auth0callback")
def auth0callback():
    oauth.auth0.authorize_access_token()
    resp = oauth.auth0.get("userinfo")
    userinfo = resp.json()
    session["profile"] = {
        "user_id": userinfo["sub"],
    }
    return redirect("/dashboard")
