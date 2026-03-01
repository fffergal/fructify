from flask import Blueprint, request


bp = Blueprint("debug", __name__)


@bp.route("/api/v1/debug", methods=["DELETE", "GET", "POST"])
def debug():
    if request.method == "DELETE":
        raise Exception
    if request.method != "POST":
        return request.args
    return request.get_data()
