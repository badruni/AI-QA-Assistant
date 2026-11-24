import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import evidence_manager, project_manager, report_manager
from core.path_safety import resolve_project_path


class ProjectDataIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.project_ids = ("ISOLATION_A", "ISOLATION_B")
        self.projects = {}
        for project_id in self.project_ids:
            project_dir = self.root / project_id
            (project_dir / "reports").mkdir(parents=True)
            (project_dir / "evidence" / "screenshots").mkdir(parents=True)
            (project_dir / "project_config.json").write_text(
                json.dumps({"project_id": project_id}), encoding="utf-8"
            )
            self.projects[project_id] = project_dir

        self.patches = []
        for module in (evidence_manager, project_manager, report_manager):
            patcher = patch.object(module, "PROJECTS_DIR", self.root)
            patcher.start()
            self.patches.append(patcher)
            self.addCleanup(patcher.stop)

    def test_reports_are_written_and_read_within_their_own_project(self):
        report_a = report_manager.save_inspection_report(
            "ISOLATION_A", "frontend_qa", {"marker": "only-project-a"}
        )
        report_b = report_manager.save_inspection_report(
            "ISOLATION_B", "frontend_qa", {"marker": "only-project-b"}
        )
        content_a = report_a.read_text(encoding="utf-8")
        content_b = report_b.read_text(encoding="utf-8")

        self.assertEqual(report_a.parent.resolve(), (self.projects["ISOLATION_A"] / "reports").resolve())
        self.assertEqual(report_b.parent.resolve(), (self.projects["ISOLATION_B"] / "reports").resolve())
        self.assertIn("only-project-a", content_a)
        self.assertNotIn("only-project-b", content_a)
        self.assertIn("only-project-b", content_b)
        self.assertNotIn("only-project-a", content_b)

    def test_evidence_indexes_and_ids_are_project_scoped(self):
        evidence_a = self.projects["ISOLATION_A"] / "evidence" / "screenshots" / "a.png"
        evidence_b = self.projects["ISOLATION_B"] / "evidence" / "screenshots" / "b.png"
        evidence_a.write_bytes(b"synthetic evidence A")
        evidence_b.write_bytes(b"synthetic evidence B")
        record_a = evidence_manager.register_evidence(
            "ISOLATION_A", evidence_a, "screenshot", "test_fixture"
        )
        record_b = evidence_manager.register_evidence(
            "ISOLATION_B", evidence_b, "screenshot", "test_fixture"
        )

        records_a = evidence_manager.list_evidence("ISOLATION_A")
        records_b = evidence_manager.list_evidence("ISOLATION_B")
        self.assertEqual([item["evidence_id"] for item in records_a], [record_a["evidence_id"]])
        self.assertEqual([item["evidence_id"] for item in records_b], [record_b["evidence_id"]])
        self.assertTrue(evidence_manager.verify_evidence("ISOLATION_A", record_a["evidence_id"]))
        self.assertTrue(evidence_manager.verify_evidence("ISOLATION_B", record_b["evidence_id"]))
        with self.assertRaises(KeyError):
            evidence_manager.verify_evidence("ISOLATION_B", record_a["evidence_id"])
        with self.assertRaises(KeyError):
            evidence_manager.verify_evidence("ISOLATION_A", record_b["evidence_id"])

    def test_project_id_and_report_path_cannot_escape_project_root(self):
        with self.assertRaises(ValueError):
            project_manager.get_project("../ISOLATION_B")
        with self.assertRaises(ValueError):
            resolve_project_path(
                self.projects["ISOLATION_A"], "../ISOLATION_B/reports"
            )


if __name__ == "__main__":
    unittest.main()
