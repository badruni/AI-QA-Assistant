import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import evidence_manager, project_manager


class EvidenceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-TEST"
        self.project_dir = self.root / self.project_id
        (self.project_dir / "evidence" / "screenshots").mkdir(parents=True)
        (self.project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.project_patch = patch.object(
            evidence_manager, "PROJECTS_DIR", self.root
        )
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)
        self.manager_patch = patch.object(
            project_manager, "PROJECTS_DIR", self.root
        )
        self.manager_patch.start()
        self.addCleanup(self.manager_patch.stop)
        self.image = self.project_dir / "evidence" / "screenshots" / "shot.png"
        self.image.write_bytes(b"test-image-bytes")

    def test_registers_metadata_and_relative_path(self):
        record = evidence_manager.register_evidence(
            self.project_id,
            self.image,
            "screenshot",
            "generic_uat",
            page_url="https://example.test/a?token=secret#section",
            related_finding_ids=["F-001"],
            metadata={"password": "must-not-leak", "viewport": "1365x768"},
        )
        self.assertTrue(record["evidence_id"].startswith("EV-"))
        self.assertEqual(record["file_path"], "screenshots/shot.png")
        self.assertEqual(record["page_url"], "https://example.test/a")
        self.assertEqual(record["metadata"]["password"], "[REDACTED]")
        self.assertEqual(record["related_finding_ids"], ["F-001"])

    def test_index_is_written_and_listing_returns_record(self):
        record = evidence_manager.register_evidence(
            self.project_id, self.image, "screenshot", "website_discovery"
        )
        index = self.project_dir / "evidence" / "evidence_index.json"
        self.assertTrue(index.is_file())
        payload = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(payload["project_id"], self.project_id)
        self.assertEqual(len(evidence_manager.list_evidence(self.project_id)), 1)
        self.assertEqual(payload["evidence"][0]["evidence_id"], record["evidence_id"])

    def test_verifies_integrity_and_detects_modified_file(self):
        record = evidence_manager.register_evidence(
            self.project_id, self.image, "screenshot", "generic_uat"
        )
        self.assertTrue(evidence_manager.verify_evidence(
            self.project_id, record["evidence_id"]
        ))
        self.image.write_bytes(b"changed")
        self.assertFalse(evidence_manager.verify_evidence(
            self.project_id, record["evidence_id"]
        ))

    def test_rejects_file_outside_project_evidence(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"not evidence")
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, outside, "screenshot", "generic_uat"
            )

    def test_rejects_missing_file(self):
        missing = self.project_dir / "evidence" / "screenshots" / "missing.png"
        with self.assertRaises(FileNotFoundError):
            evidence_manager.register_evidence(
                self.project_id, missing, "screenshot", "generic_uat"
            )

    def test_rejects_unknown_evidence_type(self):
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, self.image, "video", "generic_uat"
            )

    def test_rejects_invalid_project_id(self):
        with self.assertRaises(ValueError):
            evidence_manager.list_evidence("../bad")

    def test_does_not_overwrite_corrupt_index(self):
        index = self.project_dir / "evidence" / "evidence_index.json"
        index.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, self.image, "screenshot", "generic_uat"
            )
        self.assertEqual(index.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
