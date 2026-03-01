from contextlib import contextmanager
import os
from types import SimpleNamespace

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import wrapt

tracer = trace.get_tracer("fructify")

# OpenTelemetry uses globals, so need to keep track of tracing init globally.
tracing_inited_holder = SimpleNamespace(inited=False, processor=None)


class SanitizingSpanProcessor(SpanProcessor):
    """Replace secret env var values in all span attributes before export."""

    def __init__(self):
        self.secrets = {}
        for key, value in os.environ.items():
            if key.upper().endswith(("KEY", "TOKEN")) or key == "POSTGRES_DSN":
                if value:
                    self.secrets[key] = value

    def on_start(self, span, parent_context=None):
        pass

    def on_end(self, span):
        if not span._attributes:
            return
        for k in list(span._attributes.keys()):
            v = span._attributes[k]
            if isinstance(v, str):
                new_v = v
                for key, secret in self.secrets.items():
                    new_v = new_v.replace(secret, f"<{key}>")
                if new_v != v:
                    # span.attributes is a read-only MappingProxy once the span
                    # has ended, but span._attributes is still mutable at
                    # processor time (before BatchSpanProcessor serialises it).
                    span._attributes[k] = new_v

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=None):
        pass


def _flask_request_hook(span, environ):
    vercel_id = environ.get("HTTP_X_VERCEL_ID")
    if vercel_id and span and span.is_recording():
        span.set_attribute("vercel_id", vercel_id)


def init_tracing():
    """
    Init OTel tracing.

    This is a bit different to the OpenTelemetry Python examples because Vercel does
    some forking and it needs to be handled without knowing which app runner is being
    used.

    To be used with Flask's before_request.
    """
    if not tracing_inited_holder.inited:
        tracing_inited_holder.inited = True
        resource_attrs = {"service.name": "fructify"}
        for field in ["NOW_REGION", "VERCEL_REGION", "VERCEL_GITHUB_COMMIT_SHA"]:
            if field in os.environ:
                resource_attrs[field.lower()] = os.environ[field]
        provider = TracerProvider(resource=Resource(resource_attrs))
        provider.add_span_processor(SanitizingSpanProcessor())
        batch_processor = BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="https://api.honeycomb.io/v1/traces",
                headers={
                    "x-honeycomb-team": os.environ["HONEYCOMB_KEY"],
                    "x-honeycomb-dataset": "fructify",
                },
            )
        )
        provider.add_span_processor(batch_processor)
        trace.set_tracer_provider(provider)
        tracing_inited_holder.processor = batch_processor


def flush_tracing(exc):
    """
    Flush the OTel processor.

    To be used with Flask's teardown_request. Needed because Vercel can suspend the
    thread before flushing.
    """
    if tracing_inited_holder.processor:
        tracing_inited_holder.processor.force_flush()


def with_flask_tracing(app):
    FlaskInstrumentor().instrument_app(app, request_hook=_flask_request_hook)
    RequestsInstrumentor().instrument()
    app.before_request(init_tracing)
    app.teardown_request(flush_tracing)
    return app


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
