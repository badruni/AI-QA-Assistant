import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_test_site" / "playground" / "assets" / "app.js"


class ScenarioEngineIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")

        catalog = re.search(
            r"const qaComponents\s*=\s*(\[.*?\]);\s*\n\s*const qaSelectorOwners",
            cls.source,
            re.S
        )
        if not catalog:
            raise AssertionError("Component catalog not found")

        cls.components = json.loads(catalog.group(1))

        scenario_start = cls.source.index("const qaScenarios = [")
        scenario_end = cls.source.index("\n ].map(", scenario_start)

        rows = re.findall(
            r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*'
            r'(?:"([^"]+)"|(null))\s*,\s*"([^"]+)"\s*\]',
            cls.source[scenario_start:scenario_end]
        )

        cls.fixed = [
            (row[0], row[1], row[2], row[3] if row[4] == "" else "null", row[5])
            for row in rows
        ]

    def test_component_catalog_remains_57_unique_records(self):
        ids = [c["id"] for c in self.components]
        self.assertEqual(len(ids), 57)
        self.assertEqual(len(ids), len(set(ids)))

    def test_inventory_distribution_is_preserved(self):
        statuses = [c["source_status"] for c in self.components]
        self.assertEqual(statuses.count("implemented"), 21)
        self.assertEqual(statuses.count("partial"), 19)
        self.assertEqual(statuses.count("not_implemented"), 17)

    def test_scenario_registry_has_72_unique_ids(self):
        ids = [r[0] for r in self.fixed]
        self.assertEqual(len(ids), 15, f"Fixed scenarios found: {ids}")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("qaScenarios.push", self.source)
        self.assertIn("component_scan:true", self.source.replace(" ", ""))
        self.assertIn("qaValidateScenarioRegistry()", self.source)
        self.assertIn("const qaScenarioRegistryValidation", self.source)

    def test_system_scenarios_do_not_claim_unrelated_component_ids(self):
        by_id = {r[0]: r[3] for r in self.fixed}

        self.assertEqual(by_id["SCN-N-002"], "null")
        self.assertEqual(by_id["SCN-N-003"], "null")
        self.assertEqual(by_id["SCN-N-004"], "null")
        self.assertEqual(by_id["SCN-N-005"], "CMP-039")
        self.assertEqual(by_id["SCN-X-001"], "null")
        self.assertEqual(by_id["SCN-X-002"], "null")
        self.assertEqual(by_id["SCN-S-001"], "null")
        self.assertEqual(by_id["SCN-S-002"], "null")

    def test_execution_contract_and_unique_ids_exist(self):
        self.assertIn("session_id:qaSessionId", self.source)
        self.assertIn("execution_id:qaCreateExecutionId()", self.source)
        self.assertIn("result_kind:scenario.component_scan?", self.source)
        self.assertIn("qaSanitizePageUrl(location.href)", self.source)

    def test_export_contract_is_version_3_and_separates_definitions(self):
        compact = re.sub(r"\s+", "", self.source)

        self.assertIn('schema_version:"3.0"', compact)
        self.assertIn("definitions:{components:", compact)
        self.assertIn("execution_results:", self.source)
        self.assertIn("qaValidateExportPayload(payload)", self.source)
        self.assertIn("URL.revokeObjectURL(url)", self.source)

    def test_reset_restores_component_baseline_and_session_state(self):
        self.assertIn("qaInitialComponentState", self.source)
        self.assertIn("qaResetComponentState()", self.source)
        self.assertIn("qa403Output", self.source)
        self.assertIn("qaResults.length=0", self.source)

    def test_security_scenario_remains_local_simulation(self):
        self.assertIn("simulation_only:true", self.source)
        self.assertIn("network_requests:0", self.source)
        self.assertIn("No network requests", self.source)

    def test_executor_restores_search_and_active_pane(self):
        self.assertIn("const qaUiSnapshot=qaCaptureUiState()", self.source)
        self.assertIn("qaRestoreUiState(qaUiSnapshot)", self.source)

    def test_registry_validation_checks_component_references(self):
        self.assertIn("unknown component reference", self.source)
        self.assertIn("duplicate scenario id", self.source)
        self.assertIn("component scan coverage", self.source)


if __name__ == "__main__":
    unittest.main()
