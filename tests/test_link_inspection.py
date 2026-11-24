import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from modules.frontend_scanner import ScannerConfig, inspect_links
from core.result_status import ResultStatus


class TestLinkInspection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hits = {}
        cls.cookies = {}
        cls.lock = threading.Lock()

        class LocalHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                path = urlsplit(self.path).path

                with TestLinkInspection.lock:
                    TestLinkInspection.hits[path] = (
                        TestLinkInspection.hits.get(path, 0) + 1
                    )
                    TestLinkInspection.cookies[path] = (
                        self.headers.get("Cookie")
                    )

                if path in ("/", "/stop-page", "/timeout-page", "/rate-limit-page"):
                    if path == "/stop-page":
                        html = (
                            '<a href="/forbidden">Forbidden</a>'
                            '<a href="/ok">Should not run</a>'
                        )
                    elif path == "/timeout-page":
                        html = '<a href="/slow">Slow</a>'
                    elif path == "/rate-limit-page":
                        html = (
                            '<a href="/rate-limit">Rate limited</a>'
                            '<a href="/ok">Must not run</a>'
                        )
                    else:
                        html = (
                            '<a href="/ok">OK</a>'
                            '<a href="/missing">Missing</a>'
                            '<a href="/error">Server error</a>'
                            '<a href="/redirect">Redirect</a>'
                            '<a href="/forbidden">Forbidden</a>'
                            '<a href="/ok">Duplicate OK</a>'
                            '<a href="#present">Present anchor</a>'
                            '<a href="#missing-anchor">Missing anchor</a>'
                            '<a href="https://example.invalid/outside">'
                            'External</a>'
                            '<div id="present"></div>'
                        )

                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Set-Cookie", "browser_session=local")
                    self.end_headers()
                    self.wfile.write(
                        f"<html><body>{html}</body></html>".encode()
                    )
                    return

                if path == "/ok":
                    status = 200
                elif path == "/missing":
                    status = 404
                elif path == "/error":
                    status = 500
                elif path == "/forbidden":
                    status = 403
                elif path == "/rate-limit":
                    status = 429
                elif path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/ok")
                    self.end_headers()
                    return
                elif path == "/slow":
                    time.sleep(1.5)
                    status = 200
                else:
                    status = 404

                self.send_response(status)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, format, *args):
                pass

        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            LocalHandler,
        )
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()

        cls.origin = (
            f"http://127.0.0.1:{cls.server.server_address[1]}"
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        with self.lock:
            self.hits.clear()
            self.cookies.clear()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

        self.config = ScannerConfig(
            project_id="LINK_TEST",
            project_name="Link Inspection Test",
            base_url=self.origin + "/",
            project_dir=self.project_dir,
            check_images=False,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def result_for(self, results, path):
        return next(
            item for item in results
            if urlsplit(item.link_url).path == path
        )

    def test_http_status_classification(self):
        results = inspect_links(self.config)

        expected = {
            "/ok": (200, ResultStatus.PASSED),
            "/missing": (404, ResultStatus.FAILED),
            "/error": (500, ResultStatus.FAILED),
            "/forbidden": (
                403,
                ResultStatus.ACCESS_RESTRICTED,
            ),
            "/redirect": (
                302,
                ResultStatus.INCONCLUSIVE,
            ),
        }

        for path, (http_status, status) in expected.items():
            with self.subTest(path=path):
                result = self.result_for(results, path)
                self.assertEqual(result.http_status, http_status)
                self.assertEqual(result.status, status)

    def test_duplicate_internal_link_checked_once(self):
        inspect_links(self.config)

        self.assertEqual(self.hits.get("/ok"), 1)

    def test_redirect_is_not_followed(self):
        inspect_links(self.config)

        self.assertEqual(self.hits.get("/redirect"), 1)
        self.assertEqual(self.hits.get("/ok"), 1)

    def test_anchor_exists_and_missing(self):
        results = inspect_links(self.config)

        present = next(
            item for item in results
            if item.link_url == "#present"
        )
        missing = next(
            item for item in results
            if item.link_url == "#missing-anchor"
        )

        self.assertEqual(present.status, ResultStatus.PASSED)
        self.assertEqual(missing.status, ResultStatus.FAILED)

    def test_external_link_is_not_checked(self):
        results = inspect_links(self.config)

        external = next(
            item for item in results
            if item.link_type == "external"
        )

        self.assertEqual(
            external.status,
            ResultStatus.INCONCLUSIVE,
        )

    def test_api_request_does_not_inherit_browser_cookie(self):
        inspect_links(self.config)

        self.assertIsNone(self.cookies.get("/ok"))

    def test_timeout_is_classified(self):
        config = ScannerConfig(
            project_id="LINK_TIMEOUT_TEST",
            project_name="Link Timeout Test",
            base_url=self.origin + "/timeout-page",
            project_dir=self.project_dir,
            check_images=False,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        results = inspect_links(config, timeout_ms=1000)

        slow = self.result_for(results, "/slow")
        self.assertEqual(slow.status, ResultStatus.TIMEOUT)

    def test_scanner_stops_after_403_threshold(self):
        config = ScannerConfig(
            project_id="LINK_403_TEST",
            project_name="Link 403 Test",
            base_url=self.origin + "/stop-page",
            project_dir=self.project_dir,
            check_images=False,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )

        results = inspect_links(config)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].status,
            ResultStatus.ACCESS_RESTRICTED,
        )
        self.assertEqual(self.hits.get("/ok", 0), 0)

    def test_scanner_stops_after_http_429(self):
        config = ScannerConfig(
            project_id="LINK_429_TEST",
            project_name="Link Rate Limit Test",
            base_url=self.origin + "/rate-limit-page",
            project_dir=self.project_dir,
            check_images=False,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )
        results = inspect_links(config)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].http_status, 429)
        self.assertEqual(results[0].status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(self.hits.get("/ok", 0), 0)


if __name__ == "__main__":
    unittest.main()
