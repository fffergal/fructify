import atexit
import os
import threading

import beeline
import libhoney
from beeline.middleware.bottle import HoneyWSGIMiddleware


def with_tracing(app):
    """Add tracing to a WSGI app."""
    app_with_honeycomb_middleware = HoneyWSGIMiddleware(app)

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

        # The app can be suspended so flush all traces.
        def flush_start_response(status, response_headers, exc_info=None):
            try:
                # WSGI args are always passed positionally.
                return start_response(status, response_headers, exc_info)
            finally:
                libhoney.flush()

        return app_with_honeycomb_middleware(environ, flush_start_response)

    return traced_init_app


with_tracing.beeline_inited = False
beeline_init_lock = threading.Lock()
