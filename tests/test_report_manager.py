import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import project_manager, report_manager
from core.result_status import ResultStatus
from modules.frontend_scanner import HomepageInspectionResult


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
                "page_url": "https://example.test/a?lang=id&page=2&token=secret#part",
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
        self.assertEqual(
            page["page_url"],
            "https://example.test/a?lang=id&page=2&token=[REDACTED]",
        )
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

    def test_outside_path_is_redacted_without_leaking_basename(self):
        outside = self.root / "outside-sensitive-name.txt"
        path = report_manager.save_inspection_report(
            self.project_id, "generic_uat", {"artifact": outside}
        )
        content = path.read_text(encoding="utf-8")
        self.assertIn("[PATH_REDACTED]", content)
        self.assertNotIn("outside-sensitive-name", content)

    def test_reports_symlink_is_rejected_and_existing_reports_are_preserved(self):
        prior = self.project_dir / "reports" / "prior.json"
        prior.write_text('{"keep": true}', encoding="utf-8")
        outside = self.root / "outside"
        outside.mkdir()
        reports = self.project_dir / "reports"
        reports.rename(self.project_dir / "reports_original")
        try:
            reports.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            (self.project_dir / "reports_original").rename(reports)
            self.skipTest(f"Symlink creation unavailable: {exc}")
        try:
            with self.assertRaises(ValueError):
                report_manager.save_inspection_report(
                    self.project_id, "generic_uat", {"status": "Passed"}
                )
            self.assertEqual(list(outside.iterdir()), [])
            prior_original = (
                self.project_dir / "reports_original" / "prior.json"
            )
            self.assertTrue(prior_original.is_file())
            self.assertEqual(
                prior_original.read_text(encoding="utf-8"),
                '{"keep": true}',
            )
        finally:
            reports.unlink()
            (self.project_dir / "reports_original").rename(reports)

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

    def test_writes_frontend_homepage_report(self):
        screenshot = self.project_dir / "evidence" / "screenshots" / "homepage.png"
        result = HomepageInspectionResult(
            project_id=self.project_id,
            requested_url="https://example.test/?token=must-not-leak",
            final_url="https://example.test/home?session=must-not-leak#section",
            status=ResultStatus.PASSED,
            http_status=200,
            page_title="QA Test Homepage",
            screenshot_path=screenshot,
            message="Homepage berhasil diperiksa.",
        )
        path = report_manager.save_inspection_report(
            self.project_id, "frontend_homepage", result
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["inspection_type"], "frontend_homepage")
        self.assertEqual(payload["result"]["project_id"], self.project_id)
        self.assertEqual(
            payload["result"]["requested_url"],
            "https://example.test/?token=[REDACTED]",
        )
        self.assertEqual(
            payload["result"]["final_url"],
            "https://example.test/home?session=[REDACTED]",
        )
        self.assertEqual(payload["result"]["screenshot_path"], "evidence/screenshots/homepage.png")
        self.assertEqual(payload["result"]["status"], "Passed")

    def test_free_text_sensitive_patterns_are_redacted_without_hiding_qa_text(self):
        result = {
            "page_title": "QA overview password=synthetic-pass",
            "link_text": "Documentation token: synthetic-token",
            "metadata": {
                "api_key": "synthetic-api-key",
                "note": "credential=synthetic-credential; public label preserved",
            },
            "exception_message": "request failed password=synthetic-exception",
            "response_preview": "cookie=synthetic-cookie",
        }
        path = report_manager.save_inspection_report(
            self.project_id, "frontend_qa", result
        )
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)["result"]

        for secret in (
            "synthetic-pass", "synthetic-token", "synthetic-api-key",
            "synthetic-credential", "synthetic-exception", "synthetic-cookie",
        ):
            self.assertNotIn(secret, content)
        self.assertIn("QA overview", payload["page_title"])
        self.assertIn("Documentation", payload["link_text"])
        self.assertIn("public label preserved", payload["metadata"]["note"])
        self.assertEqual(payload["response_preview"], "[REDACTED]")

    def test_frontend_report_redacts_response_preview(self):
        path = report_manager.save_inspection_report(
            self.project_id,
            "frontend_qa",
            {
                "status": ResultStatus.ACCESS_RESTRICTED,
                "homepage": {
                    "response_preview": "password=client-secret and session data",
                },
                "images": [],
                "links": [],
            },
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["result"]["homepage"]["response_preview"], "[REDACTED]"
        )

    def test_report_redacts_multiple_sensitive_query_keys_but_keeps_safe_query(self):
        marker = "SYNTHETIC_SECRET_2026"
        path = report_manager.save_inspection_report(
            self.project_id,
            "generic_uat",
            {
                "page_url": (
                    "https://example.test/a?lang=id&page=2&token=" + marker
                    + "&signature=" + marker
                ),
                "note": "Observed page 2 in Indonesian.",
            },
        )
        content = path.read_text(encoding="utf-8")
        self.assertNotIn(marker, content)
        self.assertIn("lang=id", content)
        self.assertIn("page=2", content)
        self.assertIn("[REDACTED]", content)
        self.assertIn("Observed page 2", content)
        self.assertNotIn("client-secret", path.read_text(encoding="utf-8"))

    def test_unified_report_preserves_existing_frontend_report(self):
        frontend = report_manager.save_inspection_report(
            self.project_id, "frontend_qa",
            {"status": ResultStatus.PASSED, "result_marker": "m1-kept"},
        )
        unified = report_manager.save_inspection_report(
            self.project_id, "unified_qa",
            {
                "status": ResultStatus.NEEDS_REVIEW,
                "frontend": {
                    "homepage": {"response_preview": "raw response secret"},
                },
                "website_discovery": {"status": ResultStatus.PASSED},
            },
        )
        self.assertTrue(frontend.is_file())
        self.assertTrue(unified.is_file())
        self.assertEqual(
            json.loads(frontend.read_text(encoding="utf-8"))["result"]["result_marker"],
            "m1-kept",
        )
        payload = json.loads(unified.read_text(encoding="utf-8"))
        self.assertEqual(payload["inspection_type"], "unified_qa")
        self.assertEqual(
            payload["result"]["frontend"]["homepage"]["response_preview"],
            "[REDACTED]",
        )
        self.assertNotIn("raw response secret", unified.read_text(encoding="utf-8"))

    def test_failed_report_serialization_preserves_prior_report(self):
        prior = self.project_dir / "reports" / "prior.json"
        prior.write_text('{"prior": true}', encoding="utf-8")
        with patch.object(report_manager.json, "dump", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError):
                report_manager.save_inspection_report(
                    self.project_id, "generic_uat", {"new": True}
                )
        self.assertEqual(prior.read_text(encoding="utf-8"), '{"prior": true}')
        self.assertEqual(
            [item.name for item in (self.project_dir / "reports").iterdir()],
            ["prior.json"],
        )

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
