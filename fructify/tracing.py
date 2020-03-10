import atexit
import os
import threading

import beeline
from beeline.middleware.bottle import HoneyWSGIMiddleware


def with_tracing(app):
    """Add tracing to a WSGI app."""

    def traced_init_app(environ, start_response):
        # Import time could happen before forking, so init beeline just before first
        # response.
        with beeline_init_lock:
            if not with_tracing.beeline_inited:
                beeline.init(
                    writekey=os.environ["HONEYCOMB_KEY"],
                    dataset="IFTTT webhooks",
                    service_name="fructify",
                    debug=True,
                )
                atexit.register(beeline.close)
                with_tracing.beeline_inited = True

        return app(environ, start_response)
    return HoneyWSGIMiddleware(traced_init_app)


with_tracing.beeline_inited = False
beeline_init_lock = threading.Lock()
