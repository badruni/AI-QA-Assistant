import threading
import unittest

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from unittest.mock import patch

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from core.request_safety import RequestSafetyController
from core.playwright_request_guard import PlaywrightRequestGuard


class TestPlaywrightIntegration(unittest.TestCase):

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

                    with TestPlaywrightIntegration.hits_lock:
                        hits = TestPlaywrightIntegration.hits
                        hits[server_name][path] = (
                            hits[server_name].get(path, 0) + 1
                        )

                    if path == "/redirect-external" and redirect_target:
                        self.send_response(302)
                        self.send_header(
                            "Location",
                            redirect_target + "/external",
                        )
                        self.end_headers()
                        return

                    if path == "/forbidden":
                        self.send_response(403)
                        self.send_header("Content-Type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"Forbidden")
                        return

                    if path == "/external":
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"External server")
                        return

                    if path == "/":
                        self.send_response(200)
                        self.send_header(
                            "Content-Type",
                            "text/html; charset=utf-8",
                        )
                        self.end_headers()
                        self.wfile.write(
                            b"<html><head><title>Local QA Test</title>"
                            b"</head><body>Homepage OK</body></html>"
                        )
                        return

                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"OK")

                def log_message(self, format, *args):
                    pass

            return LocalHandler

        cls.external_server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler("external"),
        )

        cls.external_origin = (
            f"http://127.0.0.1:{cls.external_server.server_port}"
        )

        cls.main_server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler("main", cls.external_origin),
        )

        cls.main_origin = (
            f"http://127.0.0.1:{cls.main_server.server_port}"
        )

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

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

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

        self.controller = RequestSafetyController(
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )

        self.guard = PlaywrightRequestGuard(
            self.controller,
            self.main_origin,
        )

        self.context = self.browser.new_context(
            service_workers="block",
        )

        self.guard.install(self.context)
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def get_hits(self, server_name, path):
        with self.hits_lock:
            return self.hits[server_name].get(path, 0)

    def test_local_homepage_loads(self):
        response = self.page.goto(self.main_origin + "/")

        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)
        self.assertEqual(self.page.title(), "Local QA Test")

        self.assertEqual(
            self.get_hits("main", "/"),
            1,
        )

    def test_external_redirect_is_blocked(self):
        try:
            self.page.goto(
                self.main_origin + "/redirect-external"
            )
        except PlaywrightError:
            pass

        self.assertEqual(
            self.get_hits("main", "/redirect-external"),
            1,
        )

        self.assertEqual(
            self.get_hits("external", "/external"),
            0,
            "Redirect ke origin eksternal tidak boleh mencapai server.",
        )

    def test_403_stops_subsequent_requests(self):
        response = self.page.goto(
            self.main_origin + "/forbidden"
        )

        self.assertIsNotNone(response)
        self.assertEqual(response.status, 403)
        self.assertTrue(self.controller.is_stopped)

        try:
            self.page.goto(
                self.main_origin + "/after-403"
            )
        except PlaywrightError:
            pass

        self.assertEqual(
            self.get_hits("main", "/after-403"),
            0,
            "Request setelah batas 403 tercapai masih mencapai server.",
        )


if __name__ == "__main__":
    unittest.main()
