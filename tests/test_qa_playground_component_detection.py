import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_JS = PROJECT_ROOT / "local_test_site" / "playground" / "assets" / "app.js"


class PlaygroundComponentDetectionStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8")
        match = re.search(
            r"const qaComponents\s*=\s*(\[.*?\]);\s*\n\s*const qaSelectorOwners",
            cls.source,
            re.S,
        )
        if not match:
            raise AssertionError("Component catalog block was not found.")
        cls.components = json.loads(match.group(1))

    def test_catalog_has_57_unique_component_records(self):
        self.assertEqual(len(self.components), 57)
        ids = [component["id"] for component in self.components]
        self.assertEqual(len(ids), len(set(ids)))

    def test_source_inventory_distribution_is_preserved(self):
        statuses = [component["source_status"] for component in self.components]
        self.assertEqual(statuses.count("implemented"), 21)
        self.assertEqual(statuses.count("partial"), 19)
        self.assertEqual(statuses.count("not_implemented"), 17)

    def test_every_component_has_nonempty_selector_candidates(self):
        for component in self.components:
            candidates = component.get("selector_candidates", [])
            self.assertTrue(candidates, component["id"])
            self.assertTrue(all(isinstance(item, str) and item.strip() for item in candidates),
                            component["id"])

    def test_shared_selector_ownership_is_recorded(self):
        self.assertIn("const qaSelectorOwners=new Map()", self.source)
        self.assertIn("ambiguous:owners.length>1", self.source)
        self.assertIn("matches.length&&!hasUnambiguousMatch", self.source)

    def test_hover_selector_normalization_uses_word_boundary(self):
        self.assertIn(r'raw.replace(/:hover\b/g,"").trim()', self.source)
        self.assertNotIn(r'raw.replace(/:hover\\b/g,"").trim()', self.source)

    def test_catalog_button_does_not_run_detection_twice(self):
        self.assertNotIn(
            "qaComponents.forEach(qaDetectComponent);qaRenderCatalog",
            self.source,
        )
        self.assertIn(
            'qaRunScenario(qaScenarios.find(s=>s.component_scan&&s.component_id===c.id))',
            self.source,
        )

    def test_expectation_and_behavior_remain_separate(self):
        self.assertIn('component.behavior_status=component.behavior_status||"not_tested"', self.source)
        self.assertIn('behavior_status:component.behavior_status||"not_tested"', self.source)
        self.assertIn("expectation_status", self.source)


if __name__ == "__main__":
    unittest.main()