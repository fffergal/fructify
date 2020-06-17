import os

from beeline.middleware.flask import HoneyMiddleware
from beeline.patch import requests
import beeline
import requests  # noqa


__all__ = ["with_flask_tracing", "requests"]


def with_flask_tracing(app):
    # Be as lazy as possible because vercel does some forking.
    HoneyMiddleware(app)
    original_wsgi_app = app.wsgi_app

    def inited_app(environ, start_response):
        if not with_flask_tracing.beeline_inited:
            beeline.init(
                writekey=os.environ["HONEYCOMB_KEY"],
                dataset="IFTTT webhooks",
                service_name="fructify",
                presend_hook=presend,
            )
            with_flask_tracing.beeline_inited = True
        try:
            return original_wsgi_app(environ, start_response)
        finally:
            # Always flush because vercel can suspend the process.
            beeline.get_beeline().client.flush()

    app.wsgi_app = inited_app
    return app


with_flask_tracing.beeline_inited = False


def presend(fields):
    if os.environ["IFTTT_KEY"] in fields.get("request.url", ""):
        fields["request.url"] = fields["request.url"].replace(
            os.environ["IFTTT_KEY"], "<ifttt_key>"
        )
