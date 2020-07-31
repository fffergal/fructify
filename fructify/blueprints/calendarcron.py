from flask import Blueprint


bp = Blueprint("calendarcron", __name__)


@bp.route("/api/v1/calendarcron")
def calendarcron():
    return ("", 204)
