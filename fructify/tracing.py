import atexit
import logging
import os
import threading
import traceback

import beeline
from beeline.middleware.bottle import HoneyWSGIMiddleware
from beeline.middleware.flask import HoneyMiddleware


def with_tracing(app):
    """Add tracing to a WSGI app."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(fmt="%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)

    # Error catching needs to be done close to the original app, after start_response
    # has been replaced with the honeycomb version.
    def end_trace_error_app(environ, start_response):
        try:
            return app(environ, start_response)
        except Exception as e:
            # If there is an exception, try sending 500 which will finish the trace. If
            # start_response has already been called, it should raise the original
            # exception but won't finish the trace.
            # There's no reference to the trace at this point so can't end without using
            # start_response. Could alternatively try something with
            # beeline.finish_trace and
            # beeline.get_beeline().tracer_impl.get_active_trace_id().
            exc_info = (type(e), e, e.__traceback__)
            beeline.add_context(
                {
                    "request.error": str(type(e).__name__),
                    "request.error_detail": "".join(
                        traceback.format_exception(*exc_info)
                    ),
                }
            )
            start_response("500 Server error", [], exc_info)
            raise e

    honeyed_app = HoneyWSGIMiddleware(end_trace_error_app)

    # Flushing app has to go outside the honeyed_app so the trace is finished before
    # flush is called.
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
                logger.debug("Flushing honeycomb")
                beeline.get_beeline().client.flush()
                logger.debug("Flushed honeycomb")

        return honeyed_app(environ, flush_start_response)

    return traced_init_app


with_tracing.beeline_inited = False
beeline_init_lock = threading.Lock()


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
