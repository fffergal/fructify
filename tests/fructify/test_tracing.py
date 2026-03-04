import unittest
from unittest.mock import MagicMock, patch

from fructify.tracing import presend


class PresendTestCase(unittest.TestCase):
    def _mock_request(self, headers=None):
        mock_req = MagicMock()
        mock_req.headers = headers or {}
        return mock_req

    def test_redacts_non_empty_sensitive_value(self):
        fields = {"request.path": "/api/v1/authcheck?key=secretvalue"}
        with patch.dict("os.environ", {"SOME_KEY": "secretvalue"}, clear=True):
            with patch("fructify.tracing.request", self._mock_request()):
                presend(fields)
        self.assertNotIn("secretvalue", fields["request.path"])
        self.assertIn("<SOME_KEY>", fields["request.path"])

    def test_empty_sensitive_value_does_not_corrupt_fields(self):
        fields = {"request.path": "/api/v1/authcheck"}
        with patch.dict("os.environ", {"HONEYCOMB_KEY": ""}, clear=True):
            with patch("fructify.tracing.request", self._mock_request()):
                presend(fields)
        # Empty value should be skipped — field must not be corrupted
        self.assertEqual(fields["request.path"], "/api/v1/authcheck")

    def test_non_string_fields_are_not_modified(self):
        fields = {"duration_ms": 42}
        with patch.dict("os.environ", {"SOME_KEY": "secret"}, clear=True):
            with patch("fructify.tracing.request", self._mock_request()):
                presend(fields)
        self.assertEqual(fields["duration_ms"], 42)
