import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import project_manager, report_manager


class ReportManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-TEST"
        project_dir = self.root / self.project_id
        (project_dir / "reports").mkdir(parents=True)
        (project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.project_dir = project_dir
        self.projects_patch = patch.object(report_manager, "PROJECTS_DIR", self.root)
        self.projects_patch.start()
        self.addCleanup(self.projects_patch.stop)

        self.project_manager_patch = patch.object(
            project_manager, "PROJECTS_DIR", self.root
        )
        self.project_manager_patch.start()
        self.addCleanup(self.project_manager_patch.stop)

    def test_writes_unique_json_report_and_sanitizes_url(self):
        result = {
            "status": "PASSED",
            "pages": [{
                "page_url": "https://example.test/a?token=secret#part",
                "access_token": "should-not-leak",
                "signals": {
                    "password_fields": 1,
                    "password": "should-not-leak-either",
                },
            }],
        }
        first = report_manager.save_inspection_report(
            self.project_id, "generic_uat", result
        )
        second = report_manager.save_inspection_report(
            self.project_id, "generic_uat", result
        )
        self.assertTrue(first.is_file())
        self.assertTrue(second.is_file())
        self.assertNotEqual(first, second)
        payload = json.loads(first.read_text(encoding="utf-8"))
        page = payload["result"]["pages"][0]
        self.assertEqual(page["page_url"], "https://example.test/a")
        self.assertEqual(page["access_token"], "[REDACTED]")
        self.assertEqual(page["signals"]["password_fields"], 1)
        self.assertEqual(page["signals"]["password"], "[REDACTED]")

    def test_path_is_stored_relative_to_project(self):
        evidence = self.project_dir / "evidence" / "screenshots" / "shot.png"
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b"image")
        path = report_manager.save_inspection_report(
            self.project_id,
            "authentication_discovery",
            {"evidence_path": evidence},
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["result"]["evidence_path"],
            "evidence/screenshots/shot.png",
        )

    def test_only_known_inspection_metrics_bypass_sensitive_redaction(self):
        self.assertFalse(report_manager._is_sensitive_key("password_fields"))
        self.assertFalse(report_manager._is_sensitive_key("form_count"))
        self.assertTrue(report_manager._is_sensitive_key("access_token_fields"))
        self.assertTrue(report_manager._is_sensitive_key("password_count"))

        result = {
            "signals": {
                "password_fields": 1,
                "access_token_fields": "must-not-leak",
                "password_count": "must-not-leak-either",
            }
        }
        path = report_manager.save_inspection_report(
            self.project_id, "authentication_discovery", result
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        signals = payload["result"]["signals"]
        self.assertEqual(signals["password_fields"], 1)
        self.assertEqual(signals["access_token_fields"], "[REDACTED]")
        self.assertEqual(signals["password_count"], "[REDACTED]")

    def test_rejects_unknown_inspection_type(self):
        with self.assertRaises(ValueError):
            report_manager.save_inspection_report(
                self.project_id, "other", {}
            )

    def test_rejects_invalid_project_id(self):
        with self.assertRaises(ValueError):
            report_manager.save_inspection_report("../bad", "generic_uat", {})


if __name__ == "__main__":
    unittest.main()
