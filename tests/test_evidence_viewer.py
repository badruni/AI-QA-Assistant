import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import evidence_viewer


class EvidenceViewerTests(unittest.TestCase):
    def test_list_project_evidence_returns_manager_records(self):
        expected = ({"evidence_id": "EV-1"},)
        with patch.object(evidence_viewer, "list_evidence", return_value=expected):
            self.assertEqual(evidence_viewer.list_project_evidence("PROJECT_A"), expected)

    def test_get_evidence_details_returns_matching_record(self):
        records = (
            {"evidence_id": "EV-1", "title": "Homepage"},
            {"evidence_id": "EV-2", "title": "Login"},
        )
        with patch.object(evidence_viewer, "list_evidence", return_value=records):
            self.assertEqual(
                evidence_viewer.get_evidence_details("PROJECT_A", "EV-2"),
                records[1],
            )

    def test_get_evidence_details_rejects_unknown_id(self):
        with patch.object(evidence_viewer, "list_evidence", return_value=()):
            with self.assertRaises(KeyError):
                evidence_viewer.get_evidence_details("PROJECT_A", "EV-MISSING")

    def test_resolve_evidence_path_stays_inside_project_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "PROJECT_A"
            screenshots = project_dir / "evidence" / "screenshots"
            screenshots.mkdir(parents=True)
            (project_dir / "project_config.json").write_text(
                json.dumps({"project_id": "PROJECT_A", "project_name": "Test", "base_url": "https://example.test/"}),
                encoding="utf-8",
            )
            screenshot = screenshots / "home.png"
            screenshot.write_bytes(b"image fixture")
            record = {"evidence_id": "EV-1", "file_path": "screenshots/home.png"}
            with (
                patch.object(evidence_viewer, "PROJECTS_DIR", root),
                patch.object(evidence_viewer, "list_evidence", return_value=(record,)),
            ):
                self.assertEqual(
                    evidence_viewer.resolve_evidence_path("PROJECT_A", "EV-1"),
                    screenshot.resolve(),
                )

    def test_resolve_evidence_path_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "PROJECT_A"
            evidence_dir = project_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            (project_dir / "project_config.json").write_text(
                json.dumps({"project_id": "PROJECT_A", "project_name": "Test", "base_url": "https://example.test/"}),
                encoding="utf-8",
            )
            (project_dir / "outside.png").write_bytes(b"outside")
            record = {"evidence_id": "EV-1", "file_path": "../outside.png"}
            with (
                patch.object(evidence_viewer, "PROJECTS_DIR", root),
                patch.object(evidence_viewer, "list_evidence", return_value=(record,)),
            ):
                with self.assertRaises(ValueError):
                    evidence_viewer.resolve_evidence_path("PROJECT_A", "EV-1")


if __name__ == "__main__":
    unittest.main()
