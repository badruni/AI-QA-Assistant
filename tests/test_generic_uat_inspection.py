import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from core.result_status import ResultStatus
from core.progress_tracking import ProgressReporter
from modules.frontend_scanner import ScannerConfig
from modules.generic_uat_inspection import (
    _build_findings,
    inspect_generic_uat,
)
from modules.website_discovery import (
    DiscoveredPage,
    WebsiteDiscoveryResult,
)


class TestGenericUATFindings(unittest.TestCase):
    def test_creates_review_findings_from_dom_snapshot(self):
        snapshot = {
            "links_without_href": 1,
            "links_without_name": 2,
            "buttons_without_name": 1,
            "inputs_without_label": 1,
            "images_without_alt": 1,
        }
        findings = _build_findings("https://example.test/", snapshot)
        self.assertEqual(len(findings), 6)
        self.assertTrue(all(
            item.status == ResultStatus.NEEDS_REVIEW for item in findings
        ))

    def test_empty_snapshot_has_no_findings(self):
        self.assertEqual(_build_findings("https://example.test/", {}), [])

    def test_invalid_counts_are_ignored(self):
        findings = _build_findings(
            "https://example.test/",
            {"links_without_href": -1, "buttons_without_name": True},
        )
        self.assertEqual(findings, [])


class TestGenericUATIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hits = {}
        cls.lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                with TestGenericUATIntegration.lock:
                    TestGenericUATIntegration.hits[path] = (
                        TestGenericUATIntegration.hits.get(path, 0) + 1
                    )

                if path == "/forbidden":
                    status = 403
                    body = "<title>Forbidden</title><h1>Forbidden</h1>"
                elif path == "/rate-limit":
                    status = 429
                    body = "<title>Too Many Requests</title>"
                elif path == "/clean":
                    status = 200
                    body = (
                        "<title>Clean</title><nav><a href='/clean'>Home</a></nav>"
                        "<h1>Clean page</h1>"
                        "<img src='/pixel' alt='Small logo'>"
                        "<a href='/clean'><img src='/pixel' alt='Linked logo'></a>"
                        "<form><label for='email'>Email</label>"
                        "<input id='email' type='email'>"
                        "<input type='button' value='Cancel'>"
                        "<input type='submit' value='Send'></form>"
                    )
                elif path == "/cloudflare":
                    status = 200
                    body = (
                        "<title>Just a moment...</title>"
                        "<h1>Checking your browser before accessing this site.</h1>"
                    )
                elif path == "/pixel":
                    status = 200
                    body = ""
                else:
                    status = 200
                    body = (
                        "<title>Review</title><h1>Review page</h1>"
                        "<a>Missing href</a>"
                        "<a href='/clean'></a>"
                        "<button></button>"
                        "<input type='text'>"
                        "<img src='/pixel'>"
                        "<img src='http://127.0.0.1:1/external' alt='external'>"
                    )

                self.send_response(status)
                if path == "/pixel":
                    self.send_header("Content-Type", "image/gif")
                    self.end_headers()
                    self.wfile.write(b"GIF89a")
                    return
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

            def log_message(self, fmt, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        with self.lock:
            self.hits.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp.name)
        self.config = ScannerConfig(
            project_id="GENERIC_UAT_TEST",
            project_name="Generic UAT Test",
            base_url=self.origin + "/",
            project_dir=self.project_dir,
            check_images=False,
            check_links=False,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp.cleanup()

    def _discovery(
        self,
        path,
        status=ResultStatus.PASSED,
        discovery_status=ResultStatus.PASSED,
        stopped_reason="",
    ):
        url = self.origin + path
        discovered = DiscoveredPage(
            url=url,
            final_url=url,
            title="Test",
            http_status=200,
            status=status,
            page_type="unknown",
            component_counts={},
            internal_links=(),
            screenshot_path=None,
            message="Test fixture",
        )
        return WebsiteDiscoveryResult(
            project_id=self.config.project_id,
            start_url=self.config.base_url,
            status=discovery_status,
            pages=(discovered,),
            max_pages=20,
            completed=discovery_status == ResultStatus.PASSED,
            stopped_reason=stopped_reason,
            message="Test fixture",
        )

    def test_inspects_dom_and_creates_screenshot(self):
        events = []
        result = inspect_generic_uat(
            self.config, self._discovery("/review"),
            progress=ProgressReporter(events.append),
        )
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)
        self.assertTrue(result.completed)
        self.assertGreaterEqual(len(result.findings), 5)
        self.assertEqual(result.pages[0].status, ResultStatus.PASSED)
        self.assertIsNotNone(result.pages[0].screenshot_path)
        self.assertTrue(result.pages[0].screenshot_path.exists())
        terminal = [event for event in events if event.stage == "Generic UAT"][-1]
        self.assertEqual(terminal.status, "completed")
        self.assertEqual((terminal.current, terminal.total), (1, 1))

    def test_clean_page_passes_without_findings(self):
        result = inspect_generic_uat(self.config, self._discovery("/clean"))
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.pages[0].component_summary["inputs_without_label"], 0)
        self.assertEqual(result.pages[0].component_summary["links_without_name"], 0)

    def test_403_stops_inspection(self):
        config = ScannerConfig(
            project_id=self.config.project_id,
            project_name=self.config.project_name,
            base_url=self.config.base_url,
            project_dir=self.project_dir,
            check_images=False,
            check_links=False,
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )
        events = []
        result = inspect_generic_uat(
            config, self._discovery("/forbidden"),
            progress=ProgressReporter(events.append),
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)
        self.assertIn("403", result.stopped_reason)
        self.assertEqual(events[-1].status, "stopped")

    def test_429_stops_inspection_as_access_restricted(self):
        result = inspect_generic_uat(
            self.config, self._discovery("/rate-limit")
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)
        self.assertEqual(
            result.pages[0].access_classification.classification,
            "HTTP_RATE_LIMITED",
        )

    def test_cloudflare_challenge_stops_uat_and_is_classified(self):
        result = inspect_generic_uat(
            self.config, self._discovery("/cloudflare")
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(len(result.pages), 1)
        self.assertEqual(
            result.pages[0].access_classification.classification,
            "CLOUDFLARE_CHALLENGE",
        )
        self.assertEqual(result.findings, ())

    def test_skips_pages_not_passed_by_discovery(self):
        result = inspect_generic_uat(
            self.config,
            self._discovery("/review", status=ResultStatus.FAILED),
        )
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)
        self.assertEqual(result.pages, ())
        self.assertEqual(self.hits, {})

    def test_does_not_inspect_pages_when_discovery_was_access_restricted(self):
        result = inspect_generic_uat(
            self.config,
            self._discovery(
                "/review",
                discovery_status=ResultStatus.ACCESS_RESTRICTED,
                stopped_reason="Batas HTTP 403 tercapai.",
            ),
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)
        self.assertEqual(result.pages, ())
        self.assertEqual(result.findings, ())
        self.assertIn("403", result.stopped_reason)
        self.assertEqual(self.hits, {})

    def test_rejects_discovery_from_another_project(self):
        discovery = self._discovery("/review")
        discovery = WebsiteDiscoveryResult(
            project_id="OTHER_PROJECT",
            start_url=discovery.start_url,
            status=discovery.status,
            pages=discovery.pages,
            max_pages=discovery.max_pages,
            completed=discovery.completed,
            stopped_reason=discovery.stopped_reason,
            message=discovery.message,
        )
        with self.assertRaises(ValueError):
            inspect_generic_uat(self.config, discovery)


if __name__ == "__main__":
    unittest.main()
