import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import website_discovery, generic_uat_inspection


class EvidenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.screenshot = Path(self.temp.name) / "shot.png"
        self.screenshot.write_bytes(b"verified screenshot fixture")

    def test_discovery_registers_screenshot_metadata(self):
        with patch.object(website_discovery, "register_evidence") as register:
            result = website_discovery._register_screenshot_evidence(
                "PROJECT_A", self.screenshot, "https://example.test/",
                "Home", {"page_type": "homepage"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_A")
        self.assertEqual(kwargs["file_path"], self.screenshot)
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "website_discovery")
        self.assertEqual(kwargs["page_url"], "https://example.test/")
        self.assertEqual(kwargs["metadata"], {"page_type": "homepage"})

    def test_generic_uat_registers_screenshot_metadata(self):
        with patch.object(generic_uat_inspection, "register_evidence") as register:
            result = generic_uat_inspection._register_screenshot_evidence(
                "PROJECT_B", self.screenshot, "https://example.test/account",
                "Account", {"inspection": "generic_uat"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_B")
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "generic_uat_inspection")
        self.assertEqual(kwargs["page_url"], "https://example.test/account")

    def test_discovery_registration_failure_is_non_fatal(self):
        with patch.object(
            website_discovery, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            self.assertFalse(website_discovery._register_screenshot_evidence(
                "PROJECT_A", self.screenshot, "https://example.test/", "Home",
            ))

    def test_generic_uat_registration_failure_is_non_fatal(self):
        with patch.object(
            generic_uat_inspection, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            self.assertFalse(generic_uat_inspection._register_screenshot_evidence(
                "PROJECT_B", self.screenshot, "https://example.test/", "Home",
            ))


if __name__ == "__main__":
    unittest.main()
