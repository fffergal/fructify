from flask import Blueprint, url_for

from fructify.auth import oauth


bp = Blueprint("login", __name__)


@bp.route("/api/v1/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("auth0callback.auth0callback", _external=True)
    )
