import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import documentation_generator as generator
from core import project_manager, document_manager, evidence_manager


class DocumentationGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-GEN-001"
        self.project_dir = self.root / self.project_id
        (self.project_dir / "reports").mkdir(parents=True)
        (self.project_dir / "evidence").mkdir()
        (self.project_dir / "project_config.json").write_text(json.dumps({
            "project_id": self.project_id, "project_name": "Generator Test", "cms_url": ""
        }), encoding="utf-8")
        for module in (generator, project_manager, document_manager, evidence_manager):
            patcher = patch.object(module, "PROJECTS_DIR", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_report(self, kind, result):
        path = self.project_dir / "reports" / f"{kind}.json"
        path.write_text(json.dumps({"project_id": self.project_id, "inspection_type": kind, "result": result}), encoding="utf-8")

    def test_uat_draft_uses_observations_without_pass_fail_inference(self):
        self.write_report("generic_uat", {"status": "Passed", "pages": [{
            "page_url": "https://example.test/", "http_status": 200,
            "status": "Passed", "component_summary": {"buttons": 2}
        }], "findings": []})
        result = generator.generate_document_draft(self.project_id, "UAT")
        self.assertEqual(result["version"]["status"], "NEEDS_REVIEW")
        content = result["version"]["content"]
        serialized = json.dumps(content)
        self.assertIn("Needs Review", serialized)
        self.assertNotIn('"status": "Passed"', serialized)

    def test_web_guide_requires_generic_uat_source(self):
        with self.assertRaisesRegex(ValueError, "BLOCKED"):
            generator.generate_document_draft(self.project_id, "User_Guide_Web")

    def test_cms_guide_is_blocked_without_cms_exploration(self):
        result = generator.generate_document_draft(self.project_id, "User_Guide_CMS")
        self.assertEqual(result["version"]["status"], "BLOCKED")
        self.assertTrue(result["version"]["unverified_sections"])

    def test_invalid_document_type_rejected(self):
        with self.assertRaises(ValueError):
            generator.generate_document_draft(self.project_id, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
