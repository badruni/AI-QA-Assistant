import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from modules.frontend_scanner import ScannerConfig
from modules.website_discovery import discover_website, _classify_page
from core.result_status import ResultStatus


class TestWebsiteDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hits = {}
        cls.lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                with TestWebsiteDiscovery.lock:
                    TestWebsiteDiscovery.hits[path] = TestWebsiteDiscovery.hits.get(path, 0) + 1
                pages = {
                    "/": "<title>Home</title><nav><a href='/about'>About</a></nav><h1>Home</h1><a href='/contact'>Contact</a><a href='https://example.invalid/x'>External</a>",
                    "/about": "<title>About</title><h1>About</h1><article>Text</article>",
                    "/contact": "<title>Contact</title><form><input><button>Send</button></form>",
                    "/forbidden": "<title>Forbidden</title>",
                    "/server-error": "<title>Error</title>",
                }
                status = 403 if path == "/forbidden" else 500 if path == "/server-error" else 200 if path in pages else 404
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(pages.get(path, "<title>Missing</title>").encode())

            def log_message(self, fmt, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
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
            project_id="DISCOVERY_TEST", project_name="Discovery Test",
            base_url=self.origin + "/", project_dir=self.project_dir,
            check_images=False, check_links=False,
            max_requests_per_minute=10, stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_discovers_pages_and_form_components(self):
        result = discover_website(self.config)
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertTrue(result.completed)
        self.assertEqual(len(result.pages), 3)
        contact = next(p for p in result.pages if urlsplit(p.url).path == "/contact")
        self.assertEqual(contact.component_counts["forms"], 1)
        self.assertEqual(contact.page_type, "form")

    def test_external_links_are_not_crawled(self):
        discover_website(self.config)
        self.assertNotIn("/x", self.hits)

    def test_max_pages_is_enforced(self):
        result = discover_website(self.config, max_pages=1)
        self.assertEqual(len(result.pages), 1)
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)
        self.assertFalse(result.completed)

    def test_max_pages_cannot_exceed_20(self):
        with self.assertRaises(ValueError):
            discover_website(self.config, max_pages=21)

    def test_403_is_access_restricted(self):
        config = ScannerConfig(
            project_id="DISCOVERY_403", project_name="403 Test",
            base_url=self.origin + "/forbidden", project_dir=self.project_dir,
            check_images=False, check_links=False,
            max_requests_per_minute=10, stop_after_consecutive_403=1,
        )
        result = discover_website(config)
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)

    def test_500_is_failed_and_needs_review(self):
        config = ScannerConfig(
            project_id="DISCOVERY_500", project_name="500 Test",
            base_url=self.origin + "/server-error", project_dir=self.project_dir,
            check_images=False, check_links=False,
            max_requests_per_minute=10, stop_after_consecutive_403=3,
        )
        result = discover_website(config)
        self.assertEqual(result.pages[0].status, ResultStatus.FAILED)
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)


class TestPageClassification(unittest.TestCase):
    def test_homepage(self):
        self.assertEqual(
            _classify_page("https://example.com/", {}),
            "homepage",
        )

    def test_product_tokens(self):
        for path in ("/product/123", "/products", "/produk/sepatu", "/items/123"):
            with self.subTest(path=path):
                self.assertEqual(
                    _classify_page("https://example.com" + path, {}),
                    "product",
                )

    def test_product_substring_is_not_enough(self):
        self.assertEqual(
            _classify_page("https://example.com/productivity", {}),
            "unknown",
        )

    def test_article_tokens(self):
        for path in ("/article/123", "/articles", "/artikel", "/blog", "/news", "/berita"):
            with self.subTest(path=path):
                self.assertEqual(
                    _classify_page("https://example.com" + path, {}),
                    "article",
                )

    def test_article_substring_is_not_enough(self):
        self.assertEqual(
            _classify_page("https://example.com/newsroom", {}),
            "unknown",
        )

    def test_form_classification_uses_dom_evidence(self):
        self.assertEqual(
            _classify_page("https://example.com/contact", {"forms": 1}),
            "form",
        )

    def test_listing_classification_uses_card_evidence(self):
        self.assertEqual(
            _classify_page("https://example.com/catalog", {"card_candidates": 2}),
            "listing",
        )


if __name__ == "__main__":
    unittest.main()
