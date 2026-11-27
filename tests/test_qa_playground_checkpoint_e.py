import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"local_test_site"/"playground"/"assets"/"app.js").read_text(encoding="utf-8")
class CheckpointEContractTests(unittest.TestCase):
 def test_registry_contract(self):
  block=SOURCE[SOURCE.index("const qaValidateScenarioRegistry=()=>{"):SOURCE.index("const qaScenarioRegistryValidation=")]
  for token in ("validComponentStatuses","selector_candidates","preconditions","expected_result","validSeverities","validStatuses","component_scan"): self.assertIn(token,block)
 def test_export_integrity(self):
  block=SOURCE[SOURCE.index("const qaValidateExportPayload=payload=>{"):SOURCE.index('document.getElementById("qaRun403")')]
  for token in ("executionIds","scenarioIds.has","result_kind","executed_at","device_scale_factor","summary.scenario_passed","screenshots_included"): self.assertIn(token,block)
 def test_evidence_metadata(self):
  self.assertIn('evidence_type:"browser_assertion_metadata"',SOURCE); self.assertIn("screenshot_captured:false",SOURCE); self.assertIn("device_scale_factor:window.devicePixelRatio||1",SOURCE)
 def test_accessibility_evidence(self):
  block=SOURCE[SOURCE.index('case "SCN-A-003":'):SOURCE.index('case "SCN-R-001":')]
  for token in ("aria-labelledby","duplicateIds","landmarks","heading_outline","accessibility_smoke_not_wcag_conformance"): self.assertIn(token,block)
if __name__=="__main__": unittest.main()
