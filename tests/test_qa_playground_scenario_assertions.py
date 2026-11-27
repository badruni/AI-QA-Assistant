import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "local_test_site" / "playground" / "assets" / "app.js"
TEXT = APP.read_text(encoding="utf-8")

class ScenarioAssertionEvidenceTests(unittest.TestCase):
    def test_tab_scenario_uses_real_click_and_selected_state(self):
        block = TEXT[TEXT.index('case "SCN-N-003":'):TEXT.index('case "SCN-N-004":')]
        self.assertIn('tab.click()', block)
        self.assertIn('aria-selected', block)
        self.assertIn('catalog_pane_active', block)

    def test_theme_scenario_checks_change_and_restores_storage(self):
        block = TEXT[TEXT.index('case "SCN-N-004":'):TEXT.index('case "SCN-N-005":')]
        self.assertIn('button.click()', block)
        self.assertIn('after!==before', block)
        self.assertIn('localStorage.setItem("mdz-theme",savedBefore)', block)

    def test_gallery_scenario_opens_and_closes_dialog(self):
        block = TEXT[TEXT.index('case "SCN-N-005":'):TEXT.index('case "SCN-X-001":')]
        self.assertIn('opener.click()', block)
        self.assertIn('closeButton.click()', block)
        self.assertIn('dialog_closed', block)

    def test_empty_search_dispatches_input_and_records_evidence(self):
        block = TEXT[TEXT.index('case "SCN-X-001":'):TEXT.index('case "SCN-X-002":')]
        self.assertIn('dispatchEvent(new Event("input"', block)
        self.assertIn('original_visible_items', block)
        self.assertIn('empty_query_visible_items', block)

    def test_uninstrumented_network_claim_is_blocked(self):
        block = TEXT[TEXT.index('case "SCN-X-003":'):TEXT.index('case "SCN-A-001":')]
        self.assertIn('executionStatus="blocked"', block)
        self.assertNotIn('pass=true', block)

    def test_responsive_checks_are_scoped_and_evidenced(self):
        self.assertIn('scope:"current_viewport_only"', TEXT)
        self.assertIn('horizontal_overflow_px', TEXT)
        self.assertIn('viewport_width:viewport', TEXT)

    def test_export_schema_three_is_preserved(self):
        self.assertIn('schema_version:"3.0"', TEXT)
        self.assertIn('execution_results:qaClone(qaResults)', TEXT)

if __name__ == "__main__":
    unittest.main()
