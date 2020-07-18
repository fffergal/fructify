import os

from authlib.integrations.flask_client import OAuth


oauth = OAuth()
oauth.register(
    "auth0",
    client_id=os.environ["AUTH0_CLIENT_ID"],
    client_secret=os.environ["AUTH0_CLIENT_SECRET"],
    api_base_url=f"https://{os.environ['AUTH0_DOMAIN']}",
    access_token_url=f"https://{os.environ['AUTH0_DOMAIN']}/oauth/token",
    authorize_url=f"https://{os.environ['AUTH0_DOMAIN']}/authorize",
    client_kwargs={"scope": "openid profile email"},
)
oauth.register(
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
