import os

from authlib.integrations.flask_client import OAuth


def set_secret_key(app):
    """Set SECRET_KEY on Flask app from env so sessions can be used."""
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    else:
        assert app.config["SECRET_KEY"] == os.environ["FLASK_SECRET_KEY"]


def add_oauth(app):
    """
    Add authlib OAuth to an app and return the OAuth object.

    Also sets the Flask secret key for sessions.
    """
    set_secret_key(app)
    return OAuth(app)


def add_auth0(oauth):
    """
    Add auth0 handling to an OAuth object and return the registered auth0 object.

    You can get an OAuth object by passing a Flask app to add_oauth.
    """
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


def add_google(oauth):
    """
    Add google handling to an OAuth object and return the registered google object.

    You can get an OAuth object by passing a Flask app to add_oauth.
    """
    return oauth.register(
        "google",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        access_token_url="https://oauth2.googleapis.com/token",
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        authorize_params={"access_type": "offline"},
        client_kwargs={
            "scope": " ".join(
                [
                    "openid",
                    "profile",
                    "email",
                    "https://www.googleapis.com/auth/calendar.readonly",
                    "https://www.googleapis.com/auth/calendar.events.readonly",
                ]
            ),
            "prompt": "consent",
        },
    )
