import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import frontend_scanner


class FrontendScannerEvidenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.screenshot = Path(self.temp.name) / "homepage.png"
        self.screenshot.write_bytes(b"verified homepage screenshot")

    def test_registers_homepage_screenshot_metadata(self):
        with patch.object(frontend_scanner, "register_evidence") as register:
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/",
                "Example Home", {"inspection": "frontend_homepage"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_HOME")
        self.assertEqual(kwargs["file_path"], self.screenshot)
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "frontend_scanner")
        self.assertEqual(kwargs["page_url"], "https://example.test/")
        self.assertEqual(kwargs["title"], "Example Home")
        self.assertEqual(kwargs["metadata"], {"inspection": "frontend_homepage"})

    def test_registration_failure_is_non_fatal(self):
        with patch.object(
            frontend_scanner, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/",
                "Example Home",
            )
        self.assertFalse(result)

    def test_empty_title_and_metadata_use_safe_defaults(self):
        with patch.object(frontend_scanner, "register_evidence") as register:
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/", None,
            )
        self.assertTrue(result)
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["title"], "")
        self.assertEqual(kwargs["metadata"], {})


if __name__ == "__main__":
    unittest.main()
