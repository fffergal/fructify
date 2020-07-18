from flask import Blueprint, request

from fructify.auth import oauth


bp = Blueprint("login", __name__)


@bp.route("/api/v1/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=f"{request.url_root}api/v1/auth0callback"
    )
