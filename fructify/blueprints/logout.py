from urllib.parse import urlencode
import os

from flask import Blueprint, redirect, request, session

from fructify.auth import oauth


bp = Blueprint("logout", __name__)


@bp.route("/api/v1/logout")
def logout():
    session.clear()
    params = {
        "returnTo": f"{request.url_root}",
        "client_id": os.environ["AUTH0_CLIENT_ID"],
    }
    return redirect(oauth.auth0.api_base_url + "/v2/logout?" + urlencode(params))
