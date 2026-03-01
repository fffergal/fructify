from contextlib import contextmanager
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import wrapt

tracer = trace.get_tracer("fructify")

# Env vars whose values should be redacted from span attributes.
ENV_SECRETS = [
    "HONEYCOMB_KEY",
    "TELEGRAM_KEY",
    "TELEGRAM_BOT_WEBHOOK_TOKEN",
    "IFTTT_KEY",
    "EASYCRON_KEY",
    "POSTGRES_DSN",
]


def _sanitize(secrets, value):
    """Replace secret values in a string with their env var name."""
    if not isinstance(value, str):
        return value
    for key, secret in secrets.items():
        if secret:
            value = value.replace(secret, f"<{key}>")
    return value


def _make_flask_request_hook(secrets):
    def request_hook(span, environ):
        vercel_id = environ.get("HTTP_X_VERCEL_ID")
        if vercel_id and span and span.is_recording():
            span.set_attribute("vercel_id", vercel_id)
        if span and span.is_recording():
            target = (span.attributes or {}).get("http.target")
            if isinstance(target, str):
                sanitized = _sanitize(secrets, target)
                if sanitized != target:
                    span.set_attribute("http.target", sanitized)

    return request_hook


def _make_requests_hook(secrets):
    def request_hook(span, request):
        if span and span.is_recording() and request.url:
            sanitized = _sanitize(secrets, request.url)
            if sanitized != request.url:
                span.set_attribute("http.url", sanitized)

    return request_hook


def with_flask_tracing(app):
    # Be as lazy as possible because vercel does some forking.
    secrets = {k: os.environ.get(k, "") for k in ENV_SECRETS}
    FlaskInstrumentor().instrument_app(
        app, request_hook=_make_flask_request_hook(secrets)
    )
    RequestsInstrumentor().instrument(request_hook=_make_requests_hook(secrets))
    original_wsgi_app = app.wsgi_app

    def inited_app(environ, start_response):
        if not with_flask_tracing.otel_inited:
            resource_attrs = {"service.name": "fructify"}
            for field in ["NOW_REGION", "VERCEL_REGION", "VERCEL_GITHUB_COMMIT_SHA"]:
                if field in os.environ:
                    resource_attrs[field.lower()] = os.environ[field]
            provider = TracerProvider(resource=Resource(resource_attrs))
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint="https://api.honeycomb.io/v1/traces",
                        headers={"x-honeycomb-team": os.environ["HONEYCOMB_KEY"]},
                    )
                )
            )
            trace.set_tracer_provider(provider)
            with_flask_tracing.provider = provider
            with_flask_tracing.otel_inited = True
        try:
            return original_wsgi_app(environ, start_response)
        finally:
            # Always flush because vercel can suspend the process.
            if with_flask_tracing.provider:
                with_flask_tracing.provider.force_flush()

    app.wsgi_app = inited_app
    return app


with_flask_tracing.otel_inited = False
with_flask_tracing.provider = None


@contextmanager
def trace_cm(cm, name):
    """
    Add tracing around an existing context manager.
    """
    with tracer.start_as_current_span(name):
        with cm as cm_obj:
            yield cm_obj


def trace_call(span_name):
    """
    Make a decorator which adds tracing around a function when called.

    Useful for functions that can take a long time to run, like DB queries.
    """

    @wrapt.decorator
    def trace_and_call(wrapped, instance, args, kwargs):
        with tracer.start_as_current_span(span_name):
            return wrapped(*args, **kwargs)

    return trace_and_call
