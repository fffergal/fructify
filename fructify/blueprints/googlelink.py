from flask import Blueprint, request, session

from fructify.auth import oauth


bp = Blueprint("googlelink", __name__)


@bp.route("/api/v1/googlelink")
def googlelink():
    assert session.get("profile", {}).get("user_id")
    return oauth.google.authorize_redirect(
        redirect_uri=f"{request.url_root}api/v1/googlecallback"
    )
