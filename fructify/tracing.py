import os

import beeline
from beeline.middleware.bottle import HoneyWSGIMiddleware


def with_tracing(app):
    """Add tracing to a WSGI app."""
    beeline.init(
        writekey=os.environ["HONEYCOMB_KEY"],
        dataset="IFTTT webhooks",
        service_name="fructify",
    )
    return HoneyWSGIMiddleware(app)
