import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import document_manager, project_manager


class DocumentManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-TEST"
        project_dir = self.root / self.project_id
        (project_dir / "documentation").mkdir(parents=True)
        (project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.project_dir = project_dir

        self.docs_patch = patch.object(document_manager, "PROJECTS_DIR", self.root)
        self.docs_patch.start()
        self.addCleanup(self.docs_patch.stop)
        self.manager_patch = patch.object(project_manager, "PROJECTS_DIR", self.root)
        self.manager_patch.start()
        self.addCleanup(self.manager_patch.stop)

    def create(self, **overrides):
        args = {
            "project_id": self.project_id,
            "document_type": "UAT",
            "title": "UAT Test",
            "content": {"sections": [{"name": "Login", "status": "NEEDS_REVIEW"}]},
            "status": "DRAFT",
            "source_summary": {"report_url": "https://example.test/a?token=hidden"},
            "unverified_sections": [],
        }
        args.update(overrides)
        return document_manager.create_document(**args)

    def test_create_document_writes_first_version_and_manifest(self):
        result = self.create()
        manifest = result["manifest"]
        self.assertEqual(manifest["current_version"], 1)
        self.assertEqual(manifest["document_type"], "UAT")
        self.assertTrue((self.project_dir / "documentation" /
                         manifest["document_id"] / "v0001.json").is_file())

    def test_sensitive_values_are_redacted_and_urls_sanitized(self):
        result = self.create(content={
            "password": "dont-store",
            "access_token": "dont-store-either",
            "page_url": "https://example.test/path?token=secret#frag",
        })
        content = result["version"]["content"]
        self.assertEqual(content["password"], "[REDACTED]")
        self.assertEqual(content["access_token"], "[REDACTED]")
        self.assertEqual(content["page_url"], "https://example.test/path")

    def test_rejects_unserializable_content(self):
        with self.assertRaises(TypeError):
            self.create(content={"bad": object()})

    def test_rejects_invalid_project_and_document_type(self):
        with self.assertRaises(ValueError):
            document_manager.list_documents("../bad")
        with self.assertRaises(ValueError):
            self.create(document_type="OTHER")

    def test_approval_requires_no_unverified_sections(self):
        result = self.create(unverified_sections=["Login result"])
        with self.assertRaises(ValueError):
            document_manager.approve_document(
                self.project_id, result["manifest"]["document_id"]
            )

    def test_approval_marks_current_version(self):
        result = self.create()
        doc_id = result["manifest"]["document_id"]
        approved = document_manager.approve_document(self.project_id, doc_id)
        self.assertEqual(approved["version"]["status"], "APPROVED")
        self.assertTrue(approved["version"]["approved_at"])

    def test_blocked_document_cannot_be_approved(self):
        result = self.create(status="BLOCKED")
        with self.assertRaises(ValueError):
            document_manager.approve_document(
                self.project_id, result["manifest"]["document_id"]
            )

    def test_new_version_requires_approved_previous_version(self):
        result = self.create()
        doc_id = result["manifest"]["document_id"]
        with self.assertRaises(ValueError):
            document_manager.create_version(self.project_id, doc_id, {"new": True})

    def test_new_version_preserves_approved_version(self):
        result = self.create()
        doc_id = result["manifest"]["document_id"]
        document_manager.approve_document(self.project_id, doc_id)
        updated = document_manager.create_version(
            self.project_id, doc_id, {"sections": ["updated"]},
            unverified_sections=["Review needed"],
        )
        self.assertEqual(updated["manifest"]["current_version"], 2)
        self.assertEqual(updated["version"]["status"], "DRAFT")
        old_path = (self.project_dir / "documentation" / doc_id / "v0001.json")
        old = json.loads(old_path.read_text(encoding="utf-8"))
        self.assertEqual(old["status"], "APPROVED")

    def test_list_documents_is_project_scoped_and_filterable(self):
        self.create()
        self.create(document_type="User_Guide_Web", title="Web Guide")
        self.assertEqual(len(document_manager.list_documents(self.project_id)), 2)
        self.assertEqual(
            len(document_manager.list_documents(self.project_id, "UAT")), 1
        )

    def test_rejects_symlink_documentation_directory(self):
        if not hasattr(Path, "symlink_to"):
            self.skipTest("Symlink tidak didukung.")
        other = self.root / "outside"
        other.mkdir()
        docs = self.project_dir / "documentation"
        docs.rmdir()
        try:
            docs.symlink_to(other, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Pembuatan symlink memerlukan hak akses tambahan.")
        with self.assertRaises(ValueError):
            self.create()


if __name__ == "__main__":
    unittest.main()
