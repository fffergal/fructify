from flask import Flask, session
from fructify.auth import set_secret_key
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))
set_secret_key(app)


@app.route("/api/v1/authcheck")
def authcheck():
    return {"loggedIn": bool(session.get("profile", {}).get("user_id"))}
