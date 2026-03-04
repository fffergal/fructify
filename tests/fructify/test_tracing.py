import io
import json
import os
import unittest
from unittest.mock import patch

from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from fructify.tracing import SanitizingExporter


def _make_exporter(env=None):
    """Return a SanitizingExporter built with the given env (default: empty)."""
    env = env or {}
    with patch.dict(os.environ, env, clear=True):
        return SanitizingExporter(delegate=None)


def _make_span(attributes=None):
    return ReadableSpan(name="test-span", attributes=attributes or {})


class SanitizeValueTestCase(unittest.TestCase):
    def test_replaces_secret_in_string(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        self.assertEqual(
            exporter._sanitize("url had supersecret in it"),
            "url had <MY_KEY> in it",
        )

    def test_leaves_clean_string_unchanged(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        self.assertEqual(
            exporter._sanitize("nothing to see here"), "nothing to see here"
        )

    def test_leaves_non_string_unchanged(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        self.assertEqual(exporter._sanitize(42), 42)

    def test_replaces_multiple_secrets(self):
        exporter = _make_exporter({"MY_KEY": "key123", "MY_TOKEN": "tok456"})
        self.assertEqual(
            exporter._sanitize("key123 and tok456"),
            "<MY_KEY> and <MY_TOKEN>",
        )

    def test_postgres_dsn_env_name_collected(self):
        exporter = _make_exporter({"POSTGRES_DSN": "postgres://user:pw@host/db"})
        self.assertIn("POSTGRES_DSN", exporter.secrets)

    def test_empty_env_value_not_collected(self):
        exporter = _make_exporter({"MY_KEY": ""})
        self.assertNotIn("MY_KEY", exporter.secrets)

    def test_non_secret_env_not_collected(self):
        exporter = _make_exporter({"SOME_VAR": "value"})
        self.assertNotIn("SOME_VAR", exporter.secrets)


class SanitizeSpanTestCase(unittest.TestCase):
    def test_returns_same_object_when_no_secrets(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        span = _make_span({"url": "http://example.com"})
        self.assertIs(exporter._sanitize_span(span), span)

    def test_returns_new_span_when_secret_found(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        span = _make_span({"url": "http://supersecret.example.com"})
        sanitized = exporter._sanitize_span(span)
        self.assertIsNot(sanitized, span)
        self.assertEqual(
            dict(sanitized.attributes), {"url": "http://<MY_KEY>.example.com"}
        )

    def test_sanitized_span_preserves_name(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        span = _make_span({"url": "supersecret"})
        sanitized = exporter._sanitize_span(span)
        self.assertEqual(sanitized.name, "test-span")

    def test_returns_same_object_when_no_attributes(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        span = _make_span({})
        self.assertIs(exporter._sanitize_span(span), span)

    def test_non_string_attribute_preserved(self):
        exporter = _make_exporter({"MY_KEY": "supersecret"})
        span = _make_span({"url": "supersecret", "count": 5})
        sanitized = exporter._sanitize_span(span)
        self.assertEqual(sanitized.attributes["count"], 5)


class SanitizingExporterEndToEndTestCase(unittest.TestCase):
    def _run_span(self, secret, attribute_value, env_name="MY_KEY"):
        buf = io.StringIO()
        with patch.dict(os.environ, {env_name: secret}, clear=True):
            exporter = SanitizingExporter(ConsoleSpanExporter(out=buf))
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer("test")
        with tracer.start_as_current_span("myspan") as span:
            span.set_attribute("the_attr", attribute_value)
        return buf.getvalue()

    def test_secret_replaced_in_console_output(self):
        output = self._run_span("supersecret", "url had supersecret in it")
        self.assertNotIn("supersecret", output)
        self.assertIn("<MY_KEY>", output)

    def test_clean_value_unchanged_in_console_output(self):
        output = self._run_span("supersecret", "nothing special here")
        self.assertIn("nothing special here", output)

    def test_output_is_valid_json(self):
        output = self._run_span("supersecret", "url had supersecret in it")
        # ConsoleSpanExporter emits one JSON object per line
        parsed = json.loads(output.strip())
        self.assertEqual(parsed["name"], "myspan")
