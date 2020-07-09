from urllib.parse import urlencode
import os

from flask import Flask, redirect, request, session
from fructify.auth import add_auth0
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
auth0 = add_auth0(app)


@app.route("/api/v1/logout")
def logout():
    session.clear()
    params = {
        "returnTo": f"{request.url_root}api/v1/login",
        "client_id": os.environ["AUTH0_CLIENT_ID"],
    }
    return redirect(auth0.api_base_url + "/v2/logout?" + urlencode(params))
