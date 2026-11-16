from base64 import b64decode
import tempfile
import threading
import unittest

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from modules.frontend_scanner import (
    ScannerConfig,
    inspect_images,
)
from core.result_status import ResultStatus


class TestImageInspection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hits = {}
        cls.hits_lock = threading.Lock()

        # PNG valid berukuran 1 x 1 pixel.
        cls.valid_png = b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
            "/x8AAwMCAO+jWZ8AAAAASUVORK5CYII="
        )

        class LocalHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                path = urlsplit(self.path).path

                with TestImageInspection.hits_lock:
                    TestImageInspection.hits[path] = (
                        TestImageInspection.hits.get(path, 0) + 1
                    )

                if path == "/":
                    body = (
                        b"<html><head><title>Image Test</title></head>"
                        b"<body>"
                        b'<img src="/valid.png" alt="Valid">'
                        b'<img src="/missing.png" alt="Missing">'
                        b'<img src="/invalid.png" alt="Invalid">'
                        b"</body></html>"
                    )

                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "text/html; charset=utf-8",
                    )
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if path == "/valid.png":
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.end_headers()
                    self.wfile.write(TestImageInspection.valid_png)
                    return

                if path == "/missing.png":
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Not Found")
                    return

                if path == "/invalid.png":
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.end_headers()
                    self.wfile.write(b"This is not a valid PNG")
                    return

                self.send_response(404)
                self.end_headers()

            def log_message(self, format, *args):
                pass

        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            LocalHandler,
        )

        cls.origin = (
            f"http://127.0.0.1:{cls.server.server_port}"
        )

        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        with self.hits_lock:
            self.hits.clear()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

        self.config = ScannerConfig(
            project_id="IMAGE_TEST",
            project_name="Image Inspection Test",
            base_url=self.origin,
            project_dir=self.project_dir,
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_image_passes(self):
        results = inspect_images(self.config)

        valid = next(
            item for item in results
            if urlsplit(item.image_url).path == "/valid.png"
        )

        self.assertEqual(valid.http_status, 200)
        self.assertEqual(valid.status, ResultStatus.PASSED)

    def test_http_404_image_fails(self):
        results = inspect_images(self.config)

        missing = next(
            item for item in results
            if urlsplit(item.image_url).path == "/missing.png"
        )

        self.assertEqual(missing.http_status, 404)
        self.assertEqual(missing.status, ResultStatus.FAILED)

    def test_invalid_image_content_fails(self):
        results = inspect_images(self.config)

        invalid = next(
            item for item in results
            if urlsplit(item.image_url).path == "/invalid.png"
        )

        self.assertEqual(invalid.http_status, 200)
        self.assertEqual(invalid.status, ResultStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
