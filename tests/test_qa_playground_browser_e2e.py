import json
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND = ROOT / "local_test_site" / "playground"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class QAPlaygroundBrowserE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sync_playwright is None:
            raise unittest.SkipTest(
                "Playwright Python package is not installed in this environment."
            )
        handler = lambda *args, **kwargs: QuietHandler(
            *args, directory=str(PLAYGROUND), **kwargs
        )
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(headless=True)
        except Exception as exc:
            cls.playwright.stop()
            cls.server.shutdown()
            cls.server.server_close()
            raise unittest.SkipTest(f"Chromium executable is unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        browser = getattr(cls, "browser", None)
        if browser:
            browser.close()
        playwright = getattr(cls, "playwright", None)
        if playwright:
            playwright.stop()
        server = getattr(cls, "server", None)
        if server:
            server.shutdown()
            server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.goto(self.base_url + "/", wait_until="networkidle")

    def tearDown(self):
        self.context.close()

    def open_qa_lab(self):
        self.page.goto(self.base_url + "/#qa-lab", wait_until="networkidle")
        self.page.locator("#qaWorkbench").wait_for(state="visible")

    def test_footer_hash_target_and_internal_hash_links(self):
        missing = self.page.locator('a[href^="#"]').evaluate_all(
            "(links) => links.map(a => a.getAttribute('href')).filter(h => h && h.length > 1 && !document.getElementById(h.slice(1)))"
        )
        self.assertEqual(missing, [], f"Broken internal hash targets: {missing}")
        self.assertIsNotNone(self.page.locator("#footer").element_handle())

    def test_theme_toggle_persists_and_restores(self):
        before = self.page.locator("html").get_attribute("data-theme")
        self.page.locator("#themeToggle").click()
        after = self.page.locator("html").get_attribute("data-theme")
        self.assertNotEqual(before, after)
        self.assertEqual(self.page.evaluate("localStorage.getItem('mdz-theme')"), after)
        self.page.locator("#themeToggle").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-theme"), before)

    def test_hero_carousel_next_and_dot_state(self):
        dots = self.page.locator("#heroCarousel .dot")
        self.assertEqual(dots.count(), 4)
        before = self.page.locator(
            "#heroCarousel .dot[aria-current='true']"
        ).get_attribute("aria-label")
        self.page.locator(".hero-arrow-next").click()
        self.page.wait_for_function(
            "before => document.querySelector('#heroCarousel .dot[aria-current=true]')?.getAttribute('aria-label') !== before",
            arg=before,
        )
        after = self.page.locator(
            "#heroCarousel .dot[aria-current='true']"
        ).get_attribute("aria-label")
        self.assertNotEqual(before, after)

    def test_gallery_dialog_focus_and_restore(self):
        opener = self.page.locator(".media-open").first
        opener.scroll_into_view_if_needed()
        opener.focus()
        opener.click()
        dialog = self.page.locator("#imageModal")
        self.assertTrue(dialog.evaluate("(e) => e.classList.contains('open')"))
        self.assertEqual(self.page.evaluate("document.activeElement.id"), "modalClose")
        self.page.keyboard.press("Escape")
        self.assertFalse(dialog.evaluate("(e) => e.classList.contains('open')"))
        self.assertTrue(opener.evaluate("(el) => el === document.activeElement"))

    def test_mobile_drawer_focus_escape_and_restore(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        opener = self.page.locator("#menuOpen")
        opener.click()
        self.assertEqual(opener.get_attribute("aria-expanded"), "true")
        self.assertEqual(self.page.evaluate("document.activeElement.id"), "menuClose")
        self.page.locator("#mobileDrawer a").last.focus()
        self.page.keyboard.press("Tab")
        self.assertEqual(self.page.evaluate("document.activeElement.id"), "menuClose")
        self.page.keyboard.press("Escape")
        self.assertEqual(opener.get_attribute("aria-expanded"), "false")
        self.assertEqual(self.page.evaluate("document.activeElement.id"), "menuOpen")
        self.assertEqual(
            self.page.locator("#mobileDrawer").get_attribute("aria-hidden"), "true"
        )
        self.assertTrue(self.page.locator("#mobileDrawer").evaluate("(el) => el.inert"))

    def test_workbench_tabs_support_arrow_keyboard(self):
        self.open_qa_lab()
        overview = self.page.locator('[data-qa-tab="overview"]')
        overview.focus()
        self.page.keyboard.press("ArrowRight")
        catalog = self.page.locator('[data-qa-tab="catalog"]')
        self.assertEqual(
            self.page.evaluate("document.activeElement.id"), "qaTabCatalog"
        )
        self.assertEqual(catalog.get_attribute("aria-selected"), "true")
        self.assertEqual(catalog.get_attribute("tabindex"), "0")
        self.assertTrue(self.page.locator("#qaPaneCatalog").is_visible())

    def test_threshold_scenario_checks_boundary_values(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="negative"]').click()
        card = self.page.locator("#qaNegativeList .qa-record").filter(
            has_text="SCN-X-002"
        )
        card.wait_for()
        card.get_by_role("button", name="Run scenario").click()
        self.page.locator('[data-qa-tab="results"]').click()
        result = self.page.locator("#qaResultsList .qa-record").filter(
            has_text="SCN-X-002"
        )
        result.first.wait_for(state="visible")
        self.assertIn("passed", result.first.inner_text().lower())
        self.assertIn("observed: 1, 10, 3, 3", result.first.inner_text().lower())

    def test_safe_checks_and_export_schema(self):
        self.open_qa_lab()
        self.page.locator("#qaRunAll").click()
        self.page.wait_for_function(
            "document.querySelector('#qaExecutedCount')?.textContent === '70'",
            timeout=30000,
        )
        self.assertEqual(self.page.locator("#qaExecutedCount").inner_text(), "70")
        with self.page.expect_download() as download_info:
            self.page.locator("#qaExport").click()
        download = download_info.value
        payload = json.loads(Path(download.path()).read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "3.0")
        self.assertEqual(len(payload["definitions"]["components"]), 57)
        self.assertEqual(len(payload["definitions"]["scenarios"]), 72)
        self.assertEqual(len(payload["execution_results"]), 70)

    def test_responsive_viewport_matrix_records_geometry(self):
        measurements = []
        viewports = [
            (1440, 900),
            (1024, 768),
            (768, 1024),
            (390, 844),
            (360, 800),
            (320, 700),
        ]
        for width, height in viewports:
            self.page.set_viewport_size({"width": width, "height": height})
            self.page.goto(self.base_url + "/#qa-lab", wait_until="networkidle")
            measurement = self.page.evaluate("""() => {
              const w=document.querySelector('#qaWorkbench');
              const r=w.getBoundingClientRect();
              const root=document.documentElement;
              return {
                viewport_width:root.clientWidth,
                document_width:root.scrollWidth,
                horizontal_overflow_px:Math.max(0,root.scrollWidth-root.clientWidth),
                workbench_left:Math.round(r.left),
                workbench_right:Math.round(r.right),
                workbench_width:Math.round(r.width)
              };
            }""")
            measurement["requested_viewport"] = [width, height]
            measurements.append(measurement)
            self.assertEqual(measurement["viewport_width"], width)
            self.assertGreater(measurement["workbench_width"], 0)
            self.assertGreaterEqual(
                measurement["workbench_left"],
                0,
                f"QA Workbench begins outside the left viewport edge: {measurement}",
            )
            self.assertLessEqual(
                measurement["workbench_right"],
                width + 1,
                f"QA Workbench extends beyond the right viewport edge: {measurement}",
            )
            self.assertEqual(
                measurement["horizontal_overflow_px"],
                0,
                f"Unexpected document horizontal overflow: {measurement}",
            )
        self.assertEqual(len(measurements), len(viewports))
        print("RESPONSIVE_MATRIX=" + json.dumps(measurements, sort_keys=True))

    def test_homepage_and_qa_lab_hash_navigation(self):
        self.page.goto(self.base_url + "/#qa-lab", wait_until="networkidle")
        self.page.locator(".qa-back-link").first.click()
        self.page.wait_for_url("**/#home")
        self.page.locator("[data-qa-nav]").first.click()
        self.page.wait_for_url("**/#qa-lab")
        self.assertTrue(self.page.locator("#qaWorkbench").is_visible())

    def test_catalog_search_scan_and_clear_lifecycle(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="catalog"]').click()
        search = self.page.locator("#qaCatalogSearch")
        search.fill("Accordion")
        self.assertEqual(self.page.locator("#qaCatalogList .qa-record").count(), 1)
        search.fill("")
        self.assertEqual(self.page.locator("#qaCatalogList .qa-record").count(), 57)
        self.page.locator("#qaScanCatalog").click()
        self.page.wait_for_function(
            "document.querySelector('#qaExecutedCount')?.textContent === '57'",
            timeout=30000,
        )
        self.page.locator('[data-qa-tab="results"]').click()
        self.page.locator("#qaClearResults").click()
        self.page.wait_for_function(
            "document.querySelector('#qaExecutedCount')?.textContent === '0'",
            timeout=5000,
        )
        self.assertEqual(self.page.locator("#qaExecutedCount").inner_text(), "0")
        self.assertEqual(self.page.locator("#qaPassedCount").inner_text(), "0")
        self.assertEqual(self.page.locator("#qaResultsList .qa-record").count(), 0)
        self.assertEqual(
            self.page.locator("#qaResultStatus").inner_text(),
            "Belum ada skenario dijalankan.",
        )
        self.assertEqual(
            self.page_errors,
            [],
            f"Uncaught page errors during Clear: {self.page_errors}",
        )

    def test_403_simulation_stays_local_and_reports_limit(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="security"]').click()
        cases = [("-5", 1), ("11", 10), ("3", 3), ("", 3)]
        for raw_value, expected in cases:
            self.page.locator("#qa403Limit").fill(raw_value)
            self.page.locator("#qaRun403").click()
            output = self.page.locator("#qa403Output").inner_text()
            self.assertIn(f"{expected} simulated 403", output)

    def test_reduced_motion_preference_is_respected(self):
        self.page.emulate_media(reduced_motion="reduce")
        behavior = self.page.locator("html").evaluate(
            "el => getComputedStyle(el).scrollBehavior"
        )
        self.assertEqual(behavior, "auto")

    def test_no_uncaught_page_errors_during_core_flows(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="catalog"]').click()
        self.page.locator("#qaCatalogSearch").fill("Accordion")
        self.page.locator("#qaCatalogSearch").fill("")
        self.page.locator('[data-qa-tab="overview"]').click()
        self.assertEqual(
            self.page_errors, [], f"Uncaught page errors: {self.page_errors}"
        )


    def test_checkpoint_e_accessibility_scenario_and_export_metadata(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="accessibility"]').click()
        self.page.locator("#qaAccessibilityList button").nth(2).click()
        self.page.locator('[data-qa-tab="results"]').click()
        with self.page.expect_download() as info: self.page.locator("#qaExport").click()
        with open(info.value.path(),"r",encoding="utf-8") as handle: payload=json.load(handle)
        record=next(x for x in payload["execution_results"] if x["scenario_id"]=="SCN-A-003")
        self.assertEqual(record["evidence_type"],"browser_assertion_metadata"); self.assertIs(record["screenshot_captured"],False)
        self.assertGreater(record["viewport"]["device_scale_factor"],0); self.assertIn("landmarks",record["evidence"])
        self.assertIn("heading_outline",record["evidence"]); self.assertEqual(payload["summary"]["execution_records"],len(payload["execution_results"]))

    def test_checkpoint_e_functional_tab_scenario_exports_as_behavioral(self):
        self.open_qa_lab()
        self.page.locator('[data-qa-tab="normal"]').click()
        self.page.locator("#qaNormalList button").nth(2).click()
        self.page.locator('[data-qa-tab="results"]').click()
        with self.page.expect_download() as info: self.page.locator("#qaExport").click()
        with open(info.value.path(),"r",encoding="utf-8") as handle: payload=json.load(handle)
        record=next(x for x in payload["execution_results"] if x["scenario_id"]=="SCN-N-003")
        self.assertEqual(record["result_kind"],"scenario_execution"); self.assertEqual(record["status"],"passed")
        self.assertEqual(record["evidence_type"],"browser_assertion_metadata")


if __name__ == "__main__":
    unittest.main(verbosity=2)
