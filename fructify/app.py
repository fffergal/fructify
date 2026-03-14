import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from fructify.auth import oauth
from fructify.blueprints import (
    auth0callback,
    authcheck,
    calendarcron,
    cleaning_from_gcal,
    days_until,
    debug,
    googlecalendars,
    googlecalendarwebhook,
    googlecallback,
    googlecheck,
    googlelink,
    googletelegramlinks,
    login,
    logout,
    renewwatchcron,
    telegramchats,
    telegramdeeplink,
    telegramwebhook,
)
from fructify.tracing import with_flask_tracing


def create_app():
    app = with_flask_tracing(Flask(__name__))
    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    auth0_domain = os.environ["AUTH0_DOMAIN"]
    auth0_metadata_url = f"https://{auth0_domain}/.well-known/openid-configuration"
    app.config.update(
        {
            "AUTH0_CLIENT_ID": os.environ["AUTH0_CLIENT_ID"],
            "AUTH0_CLIENT_SECRET": os.environ["AUTH0_CLIENT_SECRET"],
            "AUTH0_API_BASE_URL": f"https://{auth0_domain}",
            "AUTH0_ACCESS_TOKEN_URL": (f"https://{auth0_domain}/oauth/token"),
            "AUTH0_AUTHORIZE_URL": f"https://{auth0_domain}/authorize",
            "AUTH0_SERVER_METADATA_URL": auth0_metadata_url,
            "GOOGLE_CLIENT_ID": os.environ["GOOGLE_CLIENT_ID"],
            "GOOGLE_CLIENT_SECRET": os.environ["GOOGLE_CLIENT_SECRET"],
        }
    )
    oauth.init_app(app)

    app.register_blueprint(auth0callback.bp)
    app.register_blueprint(authcheck.bp)
    app.register_blueprint(calendarcron.bp)
    app.register_blueprint(cleaning_from_gcal.bp)
    app.register_blueprint(days_until.bp)
    app.register_blueprint(debug.bp)
    app.register_blueprint(googlecalendars.bp)
    app.register_blueprint(googlecalendarwebhook.bp)
    app.register_blueprint(googlecallback.bp)
    app.register_blueprint(googlecheck.bp)
    app.register_blueprint(googlelink.bp)
    app.register_blueprint(googletelegramlinks.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(logout.bp)
    app.register_blueprint(renewwatchcron.bp)
    app.register_blueprint(telegramchats.bp)
    app.register_blueprint(telegramdeeplink.bp)
    app.register_blueprint(telegramwebhook.bp)

    if os.environ.get("FLASK_PROXY_FIX") == "1":
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
        )
    return app
