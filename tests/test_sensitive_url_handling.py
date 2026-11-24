import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import project_manager
from core.security import sanitize_url
from modules import frontend_scanner
from modules.frontend_scanner import _classify_link


class SensitiveURLHandlingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_patch = patch.object(project_manager, "PROJECTS_DIR", self.root)
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)
        self.scanner_patch = patch.object(frontend_scanner, "PROJECTS_DIR", self.root)
        self.scanner_patch.start()
        self.addCleanup(self.scanner_patch.stop)

    @staticmethod
    def _scan_config(project_id, base_url):
        return {
            "project_id": project_id,
            "project_name": "Synthetic test project",
            "base_url": base_url,
            "cms_url": "",
            "scan": {
                "frontend_enabled": True,
                "cms_enabled": False,
                "check_images": True,
                "check_links": True,
                "max_requests_per_minute": 10,
                "stop_after_consecutive_403": 3,
            },
        }

    def test_safe_query_config_remains_operational(self):
        url = "http://127.0.0.1:8765/catalog?lang=id&page=2"
        project_manager.create_project("SAFE_QUERY", "Synthetic", url)
        loaded = frontend_scanner.load_scanner_config("SAFE_QUERY")
        self.assertEqual(loaded.base_url, url)
        self.assertEqual(project_manager.get_project("SAFE_QUERY")["base_url"], url)

    def test_legacy_sensitive_config_can_be_read_but_not_scanned_or_rewritten(self):
        marker = "SYNTHETIC_SECRET_2026"
        project_id = "LEGACY_QUERY"
        project_dir = self.root / project_id
        project_dir.mkdir()
        raw_url = (
            "http://127.0.0.1:8765/?lang=id&page=2&token=" + marker
        )
        config_path = project_dir / "project_config.json"
        config_path.write_text(
            json.dumps(self._scan_config(project_id, raw_url)), encoding="utf-8"
        )
        original_bytes = config_path.read_bytes()

        legacy = project_manager.get_project(project_id)
        self.assertEqual(legacy["base_url"], raw_url)
        shown = sanitize_url(legacy["base_url"])
        self.assertNotIn(marker, shown)
        self.assertIn("lang=id", shown)
        self.assertIn("page=2", shown)
        self.assertIn("token=[REDACTED]", shown)
        with self.assertRaisesRegex(ValueError, "parameter query sensitif"):
            frontend_scanner.load_scanner_config(project_id)
        self.assertEqual(config_path.read_bytes(), original_bytes)

    def test_sensitive_same_origin_link_is_not_an_operational_target(self):
        link_type, link_url = _classify_link(
            "/reset?lang=id&signature=SYNTHETIC_SECRET_2026",
            "http://127.0.0.1:8765/home?lang=id",
        )
        self.assertEqual(link_type, "sensitive")
        self.assertNotIn("SYNTHETIC_SECRET_2026", link_url)
        self.assertIn("lang=id", link_url)
        self.assertIn("signature=[REDACTED]", link_url)

    def test_ordinary_query_link_remains_internal_and_unchanged(self):
        link_type, link_url = _classify_link(
            "/catalog?lang=id&page=2",
            "http://127.0.0.1:8765/home",
        )
        self.assertEqual(link_type, "internal")
        self.assertEqual(link_url, "http://127.0.0.1:8765/catalog?lang=id&page=2")


if __name__ == "__main__":
    unittest.main()
