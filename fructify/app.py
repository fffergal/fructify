import os

from flask import Flask

from fructify.auth import oauth
from fructify.blueprints import (
    auth0callback,
    authcheck,
    cleaning_from_gcal,
    days_until,
    debug,
    googlecalendars,
    googlecallback,
    googlecheck,
    googlelink,
    login,
    logout,
    telegramchats,
    telegramdeeplink,
    telegramwebhook,
)
from fructify.tracing import with_flask_tracing


def create_app():
    app = with_flask_tracing(Flask(__name__))
    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    oauth.init_app(app)

    app.register_blueprint(auth0callback.bp)
    app.register_blueprint(authcheck.bp)
    app.register_blueprint(cleaning_from_gcal.bp)
    app.register_blueprint(days_until.bp)
    app.register_blueprint(debug.bp)
    app.register_blueprint(googlecalendars.bp)
    app.register_blueprint(googlecallback.bp)
    app.register_blueprint(googlecheck.bp)
    app.register_blueprint(googlelink.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(logout.bp)
    app.register_blueprint(telegramchats.bp)
    app.register_blueprint(telegramdeeplink.bp)
    app.register_blueprint(telegramwebhook.bp)

    return app
