import builtins
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from core import docx_renderer
from core.document_content_model import create_document_content, make_section


class DocxRendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.project_id = "DOCX_TEST"
        self.document_id = "DOC-HANDOVER"
        self.project_dir = self.root / self.project_id
        self.project_dir.mkdir(parents=True)
        self.content = create_document_content(
            "UAT",
            "Synthetic UAT Export",
            [make_section("Overview", [{"type": "paragraph", "text": "Synthetic export fixture."}])],
        )
        self.patches = [
            patch.object(docx_renderer, "PROJECTS_DIR", self.root),
            patch.object(docx_renderer, "get_document", return_value={
                "manifest": {"current_version": 1},
                "version": {"status": "APPROVED", "content": self.content},
            }),
            patch.object(docx_renderer, "get_project", return_value={
                "project_name": "Synthetic Project",
            }),
            patch.object(docx_renderer, "list_evidence", return_value=()),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_renders_approved_document_to_valid_docx_without_overwrite(self):
        output = docx_renderer.render_approved_docx(
            self.project_id, self.document_id
        )
        self.assertEqual(
            output,
            (self.project_dir / "documentation" / self.document_id
             / f"{self.document_id}_v0001.docx").resolve(),
        )
        self.assertTrue(output.is_file())
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
        from docx import Document
        text = "\n".join(p.text for p in Document(output).paragraphs)
        self.assertIn("Synthetic UAT Export", text)
        self.assertIn("Synthetic export fixture.", text)
        with self.assertRaises(FileExistsError):
            docx_renderer.render_approved_docx(
                self.project_id, self.document_id
            )

    def test_missing_python_docx_has_clear_actionable_error(self):
        original_import = builtins.__import__

        def without_docx(name, *args, **kwargs):
            if name == "docx" or name.startswith("docx."):
                raise ImportError("synthetic missing optional dependency")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_docx):
            with self.assertRaises(RuntimeError) as caught:
                docx_renderer.render_approved_docx(
                    self.project_id, self.document_id
                )
        self.assertIn("python-docx belum terpasang", str(caught.exception))
        self.assertIn("pip install -r requirements.txt", str(caught.exception))

    def test_unapproved_document_is_not_exported(self):
        with patch.object(docx_renderer, "get_document", return_value={
            "manifest": {"current_version": 1},
            "version": {"status": "DRAFT", "content": self.content},
        }):
            with self.assertRaisesRegex(ValueError, "APPROVED"):
                docx_renderer.render_approved_docx(
                    self.project_id, self.document_id
                )
        self.assertFalse((self.project_dir / "documentation").exists())


if __name__ == "__main__":
    unittest.main()
