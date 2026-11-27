import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "local_test_site" / "playground" / "assets" / "app.js"
SOURCE = APP.read_text(encoding="utf-8")


class CheckpointC21EvidenceIntegrityTests(unittest.TestCase):
    def test_homepage_records_explicit_container_evidence(self):
        self.assertIn('evidence={selector:"#home",found:pass,ready_state:document.readyState}', SOURCE)

    def test_tabs_record_before_and_after_restore(self):
        for token in ("pane_before:", "tab_selected_before:", "pane_after_click:", "evidence.tab_selected_after_restore=", "evidence.pane_after_restore=", "restore_matches_initial:"):
            self.assertIn(token, SOURCE)

    def test_theme_records_root_storage_and_meta_restoration(self):
        for token in ("theme_before:", "theme_after:", "theme_after_restore:", "storage_before:", "storage_after_restore:", "restore_matches_initial:"):
            self.assertIn(token, SOURCE)

    def test_gallery_records_focus_return(self):
        self.assertIn("focus_returned_to_opener", SOURCE)
        self.assertIn("document.activeElement===opener", SOURCE)

    def test_search_uses_nonempty_probe_and_verifies_restore(self):
        self.assertIn('input.value="Accordion"', SOURCE)
        self.assertIn("probe_visible_items:", SOURCE)
        self.assertIn("empty_query_visible_items:", SOURCE)
        self.assertIn("probe_restored_visible_items:", SOURCE)
        self.assertIn("restore_matches_probe:", SOURCE)

    def test_global_ui_restore_is_verified_in_evidence(self):
        self.assertIn("ui_state_restoration", SOURCE)
        self.assertIn("search_matches_initial", SOURCE)
        self.assertIn("pane_matches_initial", SOURCE)

    def test_export_schema_three_and_catalog_size_unchanged(self):
        self.assertIn('schema_version:"3.0"', SOURCE)
        self.assertIn("payload.definitions.components.length===57", SOURCE)
        self.assertIn("payload.definitions.scenarios.length===72", SOURCE)

    def test_network_simulation_remains_blocked_without_instrumentation(self):
        self.assertIn('case "SCN-X-003": executionStatus="blocked"', SOURCE)
        self.assertIn('verification:"not_instrumented"', SOURCE)


if __name__ == "__main__":
    unittest.main()
