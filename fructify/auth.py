import os

from authlib.integrations.flask_client import OAuth


def set_secret_key(app):
    """Set SECRET_KEY on Flask app from env so sessions can be used."""
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    else:
        assert app.config["SECRET_KEY"] == os.environ["FLASK_SECRET_KEY"]


def add_auth0(app):
    """Add auth0 handling to a Flask app and return the registered auth0 object."""
    set_secret_key(app)
    oauth = OAuth(app)
    auth0_domain = os.environ["AUTH0_DOMAIN"]
    return oauth.register(
        "auth0",
        client_id=os.environ["AUTH0_CLIENT_ID"],
        client_secret=os.environ["AUTH0_CLIENT_SECRET"],
        api_base_url=f"https://{auth0_domain}",
        access_token_url=f"https://{auth0_domain}/oauth/token",
        authorize_url=f"https://{auth0_domain}/authorize",
        client_kwargs={"scope": "openid profile email"},
    )
