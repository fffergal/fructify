from flask import Blueprint, session, url_for

from fructify.auth import oauth


bp = Blueprint("googlelink", __name__)


@bp.route("/api/v1/googlelink")
def googlelink():
    assert session.get("profile", {}).get("user_id")
    return oauth.google.authorize_redirect(
        redirect_uri=url_for("googlecallback.googlecallback", _external=True)
    )
