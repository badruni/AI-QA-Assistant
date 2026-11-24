import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

from core.result_status import ResultStatus
from core.progress_tracking import ProgressReporter
from modules.authentication_discovery import (
    _classify_auth_signals,
    inspect_authentication,
)


class AuthenticationClassificationTests(unittest.TestCase):
    def test_password_field_detects_login_with_high_confidence(self):
        result = _classify_auth_signals({"password_fields": 1})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_otp_field_detects_login(self):
        result = _classify_auth_signals({"otp_fields": 1})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_social_login_is_reported(self):
        result = _classify_auth_signals({"social_login": ["google"]})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_sso_hint_is_reported(self):
        result = _classify_auth_signals({"sso_hints": ["saml"]})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_login_text_is_medium_confidence(self):
        result = _classify_auth_signals({"login_text": True})
        self.assertEqual(result, ("LOGIN_DETECTED", "MEDIUM"))

    def test_no_signal_is_low_confidence(self):
        result = _classify_auth_signals({})
        self.assertEqual(result, ("NO_LOGIN_DETECTED", "LOW"))

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            _classify_auth_signals(None)


class AuthenticationSafetyTests(unittest.TestCase):
    def test_restricted_discovery_does_not_launch_browser(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            project_id="001",
            status=ResultStatus.ACCESS_RESTRICTED,
            stopped_reason="HTTP 403",
            pages=(),
        )
        with patch("modules.authentication_discovery.sync_playwright") as browser:
            result = inspect_authentication(config, discovery)
        browser.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.classification, "NEEDS_REVIEW")
        self.assertFalse(result.completed)

    def test_project_id_mismatch_is_rejected(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            project_id="002",
            status=ResultStatus.PASSED,
            stopped_reason="",
            pages=(),
        )
        with self.assertRaises(ValueError):
            inspect_authentication(config, discovery)

    def test_cloudflare_challenge_is_restricted_without_auth_interaction(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = (
                    b"<title>Just a moment...</title>"
                    b"<h1>Checking your browser before accessing this site.</h1>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        url = f"http://127.0.0.1:{server.server_address[1]}/"
        config = SimpleNamespace(
            project_id="AUTH_CF", base_url=url,
            max_requests_per_minute=10, stop_after_consecutive_403=3,
        )
        page = SimpleNamespace(url=url, status=ResultStatus.PASSED)
        discovery = SimpleNamespace(
            project_id="AUTH_CF", status=ResultStatus.PASSED,
            stopped_reason="", pages=(page,),
        )
        events = []
        result = inspect_authentication(
            config, discovery, progress=ProgressReporter(events.append)
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.classification, "NEEDS_REVIEW")
        self.assertEqual(
            result.pages[0].access_classification.classification,
            "CLOUDFLARE_CHALLENGE",
        )
        self.assertEqual(events[-1].status, "stopped")
        self.assertIn("read-only", events[-1].activity)


if __name__ == "__main__":
    unittest.main()
