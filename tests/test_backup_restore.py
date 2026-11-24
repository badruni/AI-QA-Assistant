import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path


class SyntheticBackupRestoreTests(unittest.TestCase):
    def test_project_backup_restore_preserves_report_and_evidence_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "source" / "projects" / "SYNTHETIC"
            evidence_dir = project / "evidence" / "screenshots"
            reports_dir = project / "reports"
            evidence_dir.mkdir(parents=True)
            reports_dir.mkdir()
            evidence = evidence_dir / "fixture.png"
            evidence.write_bytes(b"synthetic image fixture")
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
            (project / "evidence" / "evidence_index.json").write_text(
                json.dumps({"sha256": digest}), encoding="utf-8"
            )
            report = reports_dir / "unified_qa_fixture.json"
            report.write_text('{"synthetic": true}', encoding="utf-8")

            backup = root / "backup"
            restored = root / "restored"
            shutil.copytree(project, backup / "projects" / "SYNTHETIC")
            shutil.copytree(backup / "projects" / "SYNTHETIC", restored)

            restored_evidence = restored / "evidence" / "screenshots" / "fixture.png"
            restored_index = json.loads(
                (restored / "evidence" / "evidence_index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(restored_index["sha256"], digest)
            self.assertEqual(hashlib.sha256(restored_evidence.read_bytes()).hexdigest(), restored_index["sha256"])
            self.assertEqual(
                (restored / "reports" / report.name).read_text(encoding="utf-8"),
                '{"synthetic": true}',
            )

    def test_rollback_restores_prior_source_into_staging_and_keeps_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "application"
            source.mkdir()
            marker = source / "version.txt"
            marker.write_text("version 1", encoding="utf-8")
            backup = root / "backup"
            shutil.copytree(source, backup / "application")

            data = root / "projects" / "SYNTHETIC"
            evidence = data / "evidence" / "screenshots" / "shot.bin"
            evidence.parent.mkdir(parents=True)
            evidence.write_bytes(b"keep project data")
            before_hash = hashlib.sha256(evidence.read_bytes()).hexdigest()

            marker.write_text("version 2", encoding="utf-8")
            rollback_stage = root / "rollback-stage"
            shutil.copytree(backup / "application", rollback_stage)

            self.assertEqual(
                (rollback_stage / "version.txt").read_text(encoding="utf-8"),
                "version 1",
            )
            self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), before_hash)
            self.assertEqual(marker.read_text(encoding="utf-8"), "version 2")


if __name__ == "__main__":
    unittest.main()
