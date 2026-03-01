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


def with_flask_tracing(app):
    # Be as lazy as possible because vercel does some forking.
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    original_wsgi_app = app.wsgi_app

    def inited_app(environ, start_response):
        if not with_flask_tracing.otel_inited:
            resource_attrs = {"service.name": "fructify"}
            for field in ["VERCEL_REGION", "VERCEL_GITHUB_COMMIT_SHA"]:
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
