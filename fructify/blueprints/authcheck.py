from flask import Blueprint, session


bp = Blueprint("authcheck", __name__)


@bp.route("/api/v1/authcheck")
def authcheck():
    return {"loggedIn": bool(session.get("profile", {}).get("user_id"))}
