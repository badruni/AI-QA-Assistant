import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from core.project_manager import create_project
from core.result_status import ResultStatus
from modules.frontend_scanner import (
    ScannerConfig,
    inspect_homepage,
)


class TestHomepageInspection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hits = {
            "main": {},
            "external": {},
        }
        cls.hits_lock = threading.Lock()

        def make_handler(server_name, redirect_target=None):

            class LocalHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    path = urlsplit(self.path).path

                    with TestHomepageInspection.hits_lock:
                        hits = TestHomepageInspection.hits
                        hits[server_name][path] = hits[server_name].get(path, 0) + 1

                    if path == "/redirect-external":
                        self.send_response(302)
                        self.send_header(
                            "Location",
                            redirect_target + "/external",
                        )
                        self.end_headers()
                        return

                    if path == "/forbidden":
                        self.send_response(403)
                        self.send_header(
                            "Content-Type",
                            "text/plain",
                        )
                        self.end_headers()
                        self.wfile.write(b"Forbidden")
                        return

                    if path == "/error":
                        self.send_response(500)
                        self.send_header(
                            "Content-Type",
                            "text/plain",
                        )
                        self.end_headers()
                        self.wfile.write(b"Internal Server Error")
                        return

                    if path == "/bad-gateway":
                        self.send_response(502)
                        self.send_header(
                            "Content-Type",
                            "text/plain",
                        )
                        self.end_headers()
                        self.wfile.write(b"Bad Gateway")
                        return

                    if path == "/unknown-error":
                        self.send_response(520, "Unknown Error")
                        self.send_header(
                            "Content-Type",
                            "text/plain",
                        )
                        self.end_headers()
                        self.wfile.write(b"Origin returned an unknown error")
                        return

                    if path == "/waf-block":
                        self.send_response(200)
                        self.send_header(
                            "Content-Type",
                            "text/html; charset=utf-8",
                        )
                        self.end_headers()
                        self.wfile.write(
                            b"<html><head>"
                            b"<title>Request Blocked</title>"
                            b"</head><body>"
                            b"<h1>Request Blocked</h1>"
                            b"<p>bot detected: BOT_HEADLESS</p>"
                            b"</body></html>"
                        )
                        return

                    if path == "/external":
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"External")
                        return

                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "text/html; charset=utf-8",
                    )
                    self.end_headers()
                    self.wfile.write(
                        b"<html><head>"
                        b"<title>Homepage QA Test</title>"
                        b"</head><body>"
                        b"<h1>Homepage OK</h1>"
                        b"</body></html>"
                    )

                def log_message(self, format, *args):
                    pass

            return LocalHandler

        cls.external_server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler("external"),
        )

        cls.external_origin = f"http://127.0.0.1:{cls.external_server.server_port}"

        cls.main_server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler("main", cls.external_origin),
        )

        cls.main_origin = f"http://127.0.0.1:{cls.main_server.server_port}"

        cls.external_thread = threading.Thread(
            target=cls.external_server.serve_forever,
            daemon=True,
        )

        cls.main_thread = threading.Thread(
            target=cls.main_server.serve_forever,
            daemon=True,
        )

        cls.external_thread.start()
        cls.main_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.main_server.shutdown()
        cls.external_server.shutdown()

        cls.main_server.server_close()
        cls.external_server.server_close()

        cls.main_thread.join(timeout=2)
        cls.external_thread.join(timeout=2)

    def setUp(self):
        with self.hits_lock:
            self.hits["main"].clear()
            self.hits["external"].clear()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.projects_root = Path(self.temp_dir.name) / "projects"

        project_manager_patch = patch(
            "core.project_manager.PROJECTS_DIR",
            self.projects_root,
        )
        evidence_manager_patch = patch(
            "core.evidence_manager.PROJECTS_DIR",
            self.projects_root,
        )

        project_manager_patch.start()
        self.addCleanup(project_manager_patch.stop)

        evidence_manager_patch.start()
        self.addCleanup(evidence_manager_patch.stop)

        self.project_dir = create_project(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin,
        )

        self.config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin,
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def get_hits(self, server_name, path):
        with self.hits_lock:
            return self.hits[server_name].get(path, 0)

    def test_homepage_http_200(self):
        result = inspect_homepage(self.config)

        self.assertEqual(
            result.status,
            ResultStatus.PASSED,
        )

        self.assertEqual(result.http_status, 200)

        self.assertEqual(
            result.page_title,
            "Homepage QA Test",
        )

        self.assertIsNotNone(result.screenshot_path)
        self.assertTrue(result.screenshot_path.is_file())

        self.assertEqual(
            result.screenshot_path.parent,
            (self.project_dir / "evidence" / "screenshots").resolve(),
        )

    def test_waf_block_page_with_http_200(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/waf-block",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(result.http_status, 200)
        self.assertEqual(
            result.status,
            ResultStatus.ACCESS_RESTRICTED,
            "Halaman blokir WAF tidak boleh dianggap Passed.",
        )
        self.assertIsNotNone(result.screenshot_path)
        self.assertTrue(result.screenshot_path.is_file())

    def test_homepage_http_403(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/forbidden",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(
            result.status,
            ResultStatus.ACCESS_RESTRICTED,
        )

        self.assertEqual(result.http_status, 403)

    def test_homepage_http_500(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/error",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(
            result.status,
            ResultStatus.FAILED,
        )

        self.assertEqual(result.http_status, 500)

    def test_homepage_http_502(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/bad-gateway",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.http_status, 502)
        self.assertEqual(
            result.http_status_text,
            "Bad Gateway",
        )
        self.assertIn(
            "Bad Gateway",
            result.response_preview,
        )

    def test_homepage_http_520(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/unknown-error",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.http_status, 520)
        self.assertEqual(
            result.http_status_text,
            "Unknown Error",
        )
        self.assertIn(
            "Origin returned an unknown error",
            result.response_preview,
        )

    def test_external_redirect_is_blocked(self):
        config = ScannerConfig(
            project_id="HOMEPAGE_TEST",
            project_name="Homepage Inspection Test",
            base_url=self.main_origin + "/redirect-external",
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        result = inspect_homepage(config)

        self.assertEqual(
            result.status,
            ResultStatus.BLOCKED,
        )
        self.assertIsNone(
            result.screenshot_path,
            "Navigasi yang diblokir tidak boleh menghasilkan evidence screenshot.",
        )

        self.assertEqual(
            self.get_hits("external", "/external"),
            0,
            "Server eksternal tidak boleh menerima request.",
        )


if __name__ == "__main__":
    unittest.main()
