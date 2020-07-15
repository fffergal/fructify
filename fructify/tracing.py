from contextlib import contextmanager
import os

from beeline.middleware.flask import HoneyMiddleware
from beeline.patch import requests  # noqa
import beeline
import wrapt


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
    if os.environ["TELEGRAM_KEY"] in fields.get("request.url", ""):
        fields["request.url"] = fields["request.url"].replace(
            os.environ["TELEGRAM_KEY"], "<telegram_key>"
        )
    if os.environ["TELEGRAM_BOT_WEBHOOK_TOKEN"] in fields.get("request.url", ""):
        fields["request.url"] = fields["request.url"].replace(
            os.environ["TELEGRAM_BOT_WEBHOOK_TOKEN"], "<telegram_bot_webhook_token>"
        )


@contextmanager
def trace_cm(cm, *args, **kwargs):
    """
    Add tracing around an existing context manager.

    The args and kwargs are passed to beeline.tracer.
    """
    with beeline.tracer(*args, **kwargs):
        with cm as cm_obj:
            yield cm_obj


def trace_call(*beeline_args, **beeline_kwargs):
    """
    Make a decorator which adds tracing around a function when called.

    Useful for functions that can take a long time to turn, like DB queries.
    beeline_args and beeline_kwargs are passed to beeline.tracer.
    """

    @wrapt.decorator
    def trace_and_call(wrapped, instance, args, kwargs):
        with beeline.tracer(*beeline_args, **beeline_kwargs):
            return wrapped(*args, **kwargs)

    return trace_and_call
