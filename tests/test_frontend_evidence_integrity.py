import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core import evidence_manager, project_manager, report_manager
from core.progress_tracking import ProgressReporter
from modules import frontend_scanner
from core.result_status import ResultStatus


class FrontendEvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.project_id = "EVIDENCE_AUDIT"
        self.project_dir = self.root / self.project_id
        self.evidence_dir = self.project_dir / "evidence"
        self.screenshot_dir = self.evidence_dir / "screenshots"
        self.screenshot_dir.mkdir(parents=True)
        (self.project_dir / "reports").mkdir()
        (self.project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.screenshot = self.screenshot_dir / "homepage.png"
        self.screenshot.write_bytes(b"synthetic screenshot bytes")
        self.config = frontend_scanner.ScannerConfig(
            self.project_id, "Synthetic Evidence Project",
            "http://127.0.0.1/", self.project_dir,
            False, False, 10, 3,
        )
        for module in (evidence_manager, project_manager, report_manager):
            patcher = patch.object(module, "PROJECTS_DIR", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)

    def homepage_result(self):
        return frontend_scanner.HomepageInspectionResult(
            project_id=self.project_id,
            requested_url=self.config.base_url,
            final_url=self.config.base_url,
            status=ResultStatus.PASSED,
            http_status=200,
            page_title="Synthetic homepage",
            screenshot_path=self.screenshot,
            message="Local fixture",
        )

    def register(self):
        return evidence_manager.register_evidence(
            self.project_id, self.screenshot, "screenshot", "frontend_scanner",
            title="Synthetic homepage",
        )

    def test_valid_evidence_is_returned_only_after_hash_verification(self):
        record = self.register()
        self.assertEqual(
            frontend_scanner._workflow_evidence_ids(
                self.config, self.homepage_result()
            ),
            (record["evidence_id"],),
        )

    def test_missing_file_is_not_returned_as_verified(self):
        self.register()
        self.screenshot.unlink()
        self.assertEqual(
            frontend_scanner._workflow_evidence_ids(
                self.config, self.homepage_result()
            ),
            (),
        )

    def test_modified_file_is_not_returned_as_verified(self):
        self.register()
        self.screenshot.write_bytes(b"modified synthetic screenshot")
        self.assertEqual(
            frontend_scanner._workflow_evidence_ids(
                self.config, self.homepage_result()
            ),
            (),
        )

    def test_registry_hash_mismatch_is_not_returned_as_verified(self):
        self.register()
        index = self.evidence_dir / "evidence_index.json"
        payload = json.loads(index.read_text(encoding="utf-8"))
        payload["evidence"][0]["sha256"] = "0" * 64
        index.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(
            frontend_scanner._workflow_evidence_ids(
                self.config, self.homepage_result()
            ),
            (),
        )

    def test_unregistered_evidence_is_not_returned(self):
        self.assertEqual(
            frontend_scanner._workflow_evidence_ids(
                self.config, self.homepage_result()
            ),
            (),
        )

    def test_unverified_evidence_is_absent_from_report_and_progress_failed(self):
        self.register()
        self.screenshot.write_bytes(b"modified after registration")
        events = []
        reporter = ProgressReporter(events.append)

        with patch.object(
            frontend_scanner, "inspect_homepage",
            return_value=self.homepage_result(),
        ):
            result = frontend_scanner.run_frontend_qa_workflow(
                self.config, progress=reporter
            )
        report = report_manager.save_inspection_report(
            self.project_id, "frontend_qa", result
        )
        payload = json.loads(report.read_text(encoding="utf-8"))

        evidence_event = [
            item for item in events if item.stage == "Evidence Collection"
        ][-1]
        self.assertEqual(evidence_event.status, "failed")
        self.assertEqual(evidence_event.current, 0)
        self.assertEqual(result.evidence_ids, ())
        self.assertEqual(payload["result"]["evidence_ids"], [])


if __name__ == "__main__":
    unittest.main()
