import tempfile
import json
import threading
import unittest
from base64 import b64decode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from core import evidence_manager, project_manager, report_manager
from core.result_status import ResultStatus
from core.progress_tracking import ProgressReporter
from modules import frontend_scanner as scanner


class FrontendQAWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = scanner.ScannerConfig(
            project_id="WORKFLOW_TEST",
            project_name="Workflow Test",
            base_url="http://127.0.0.1/",
            project_dir=Path(self.temp.name),
            check_images=True,
            check_links=True,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )
        self.homepage = scanner.HomepageInspectionResult(
            project_id="WORKFLOW_TEST",
            requested_url=self.config.base_url,
            final_url=self.config.base_url,
            status=ResultStatus.PASSED,
            http_status=200,
            page_title="Local test",
            screenshot_path=None,
            message="Homepage berhasil diakses.",
        )

    def test_stages_share_controller_and_form_one_result(self):
        captured = {}

        def inspect_homepage(config, timeout, controller):
            captured["controller"] = controller
            return self.homepage

        def inspect_images(config, timeout, controller):
            self.assertIs(controller, captured["controller"])
            return [scanner.ImageInspectionResult(
                "http://127.0.0.1/image.png", 200,
                ResultStatus.PASSED, "Gambar berhasil dimuat.",
            )]

        def inspect_links(config, timeout, controller):
            self.assertIs(controller, captured["controller"])
            return [scanner.LinkInspectionResult(
                "http://127.0.0.1/page", "Page", "internal", 200,
                ResultStatus.PASSED, "Tautan berhasil.",
            )]

        with (
            patch.object(scanner, "inspect_homepage", side_effect=inspect_homepage),
            patch.object(scanner, "inspect_images", side_effect=inspect_images),
            patch.object(scanner, "inspect_links", side_effect=inspect_links),
        ):
            result = scanner.run_frontend_qa_workflow(self.config)

        self.assertEqual(result.project_id, "WORKFLOW_TEST")
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.image_status, ResultStatus.PASSED)
        self.assertEqual(result.link_status, ResultStatus.PASSED)
        self.assertEqual(len(result.image_results), 1)
        self.assertEqual(len(result.link_results), 1)

    def test_access_restricted_homepage_skips_downstream_requests(self):
        restricted = scanner.HomepageInspectionResult(
            project_id="WORKFLOW_TEST",
            requested_url=self.config.base_url,
            final_url=self.config.base_url,
            status=ResultStatus.ACCESS_RESTRICTED,
            http_status=403,
            page_title="",
            screenshot_path=None,
            message="Akses dibatasi.",
        )
        progress_events = []
        progress = ProgressReporter(progress_events.append)
        with (
            patch.object(scanner, "inspect_homepage", return_value=restricted),
            patch.object(scanner, "inspect_images") as images,
            patch.object(scanner, "inspect_links") as links,
        ):
            result = scanner.run_frontend_qa_workflow(
                self.config, progress=progress
            )

        images.assert_not_called()
        links.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.image_status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.link_status, ResultStatus.ACCESS_RESTRICTED)
        self.assertTrue(any(
            event.stage == "Image Inspection" and event.status == "stopped"
            for event in progress_events
        ))
        self.assertTrue(any(
            event.stage == "Link Inspection" and event.status == "stopped"
            for event in progress_events
        ))

    def test_blocked_homepage_skips_downstream_requests(self):
        blocked = scanner.HomepageInspectionResult(
            project_id="WORKFLOW_TEST",
            requested_url=self.config.base_url,
            final_url=self.config.base_url,
            status=ResultStatus.BLOCKED,
            http_status=None,
            page_title="",
            screenshot_path=None,
            message="Navigasi homepage diblokir.",
        )
        progress_events = []
        progress = ProgressReporter(progress_events.append)

        with (
            patch.object(scanner, "inspect_homepage", return_value=blocked),
            patch.object(scanner, "inspect_images") as images,
            patch.object(scanner, "inspect_links") as links,
        ):
            result = scanner.run_frontend_qa_workflow(
                self.config, progress=progress
            )

        images.assert_not_called()
        links.assert_not_called()
        self.assertEqual(result.status, ResultStatus.BLOCKED)
        self.assertEqual(result.image_status, ResultStatus.INCONCLUSIVE)
        self.assertEqual(result.link_status, ResultStatus.INCONCLUSIVE)
        self.assertTrue(any(
            event.stage == "Image Inspection" and event.status == "stopped"
            for event in progress_events
        ))
        self.assertTrue(any(
            event.stage == "Link Inspection" and event.status == "stopped"
            for event in progress_events
        ))

    def test_progress_reports_failed_homepage_stage(self):
        progress_events = []
        progress = ProgressReporter(progress_events.append)
        with patch.object(
            scanner, "inspect_homepage", side_effect=RuntimeError("local test failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "local test failure"):
                scanner.run_frontend_qa_workflow(self.config, progress=progress)

        self.assertEqual(progress_events[-1].stage, "Homepage")
        self.assertEqual(progress_events[-1].status, "failed")

    def test_terminal_progress_matches_homepage_outcome(self):
        cases = (
            (ResultStatus.PASSED, "completed"),
            (ResultStatus.INCONCLUSIVE, "completed"),
            (ResultStatus.FAILED, "failed"),
            (ResultStatus.BLOCKED, "failed"),
            (ResultStatus.TIMEOUT, "failed"),
            (ResultStatus.ACCESS_RESTRICTED, "stopped"),
        )
        config = scanner.ScannerConfig(
            self.config.project_id, self.config.project_name,
            self.config.base_url, self.config.project_dir,
            False, False, 10, 3,
        )

        for inspection_status, expected_terminal in cases:
            with self.subTest(status=inspection_status):
                homepage = scanner.HomepageInspectionResult(
                    self.config.project_id, self.config.base_url,
                    self.config.base_url, inspection_status,
                    200, "Synthetic", None, "Synthetic result",
                )
                events = []
                with (
                    patch.object(scanner, "inspect_homepage", return_value=homepage),
                    patch.object(scanner, "_workflow_evidence_ids", return_value=("EV-SYNTHETIC",)),
                ):
                    scanner.run_frontend_qa_workflow(
                        config, progress=ProgressReporter(events.append)
                    )

                homepage_event = [
                    event for event in events if event.stage == "Homepage"
                    and event.status in {"completed", "failed", "stopped"}
                ][-1]
                terminal_event = [
                    event for event in events
                    if event.stage == "Frontend Inspection"
                ][-1]
                self.assertEqual(homepage_event.status, expected_terminal)
                self.assertEqual(terminal_event.status, expected_terminal)
                self.assertIn(inspection_status.value, terminal_event.activity)

    def test_image_access_restriction_skips_link_requests(self):
        image = scanner.ImageInspectionResult(
            "http://127.0.0.1/image.png", 403,
            ResultStatus.ACCESS_RESTRICTED, "Akses dibatasi.",
        )
        with (
            patch.object(scanner, "inspect_homepage", return_value=self.homepage),
            patch.object(scanner, "inspect_images", return_value=[image]),
            patch.object(scanner, "inspect_links") as links,
        ):
            result = scanner.run_frontend_qa_workflow(self.config)

        links.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.link_status, ResultStatus.ACCESS_RESTRICTED)

    def test_local_end_to_end_workflow_collects_evidence_and_report(self):
        png = b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
            "/x8AAwMCAO+jWZ8AAAAASUVORK5CYII="
        )

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                if path == "/pixel.png":
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(png)))
                    self.end_headers()
                    self.wfile.write(png)
                    return
                body = (
                    b'<html><head><title>Local QA</title></head><body>'
                    b'<a href="/page">Local page</a>'
                    b'<img src="/pixel.png" alt="Pixel">'
                    b'</body></html>'
                ) if path == "/" else b"<html><title>Page</title></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(thread.join, 2)

        root = Path(self.temp.name) / "projects"
        project_dir = root / "WORKFLOW_TEST"
        (project_dir / "evidence" / "screenshots").mkdir(parents=True)
        (project_dir / "reports").mkdir()
        (project_dir / "project_config.json").write_text(
            json.dumps({"project_id": "WORKFLOW_TEST"}), encoding="utf-8"
        )
        config = scanner.ScannerConfig(
            "WORKFLOW_TEST", "Workflow Test",
            f"http://127.0.0.1:{server.server_address[1]}/", project_dir,
            True, True, 10, 3,
        )
        progress_events = []
        progress = ProgressReporter(progress_events.append)
        with (
            patch.object(evidence_manager, "PROJECTS_DIR", root),
            patch.object(project_manager, "PROJECTS_DIR", root),
            patch.object(report_manager, "PROJECTS_DIR", root),
        ):
            result = scanner.run_frontend_qa_workflow(
                config, timeout_ms=10000, progress=progress
            )
            report = report_manager.save_inspection_report(
                "WORKFLOW_TEST", "frontend_qa", result
            )
            records = evidence_manager.list_evidence("WORKFLOW_TEST")
            self.assertTrue(evidence_manager.verify_evidence(
                "WORKFLOW_TEST", records[0]["evidence_id"]
            ))

        self.assertTrue(result.homepage.screenshot_path.is_file())
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertTrue(result.image_results)
        self.assertTrue(result.link_results)
        self.assertEqual(result.evidence_ids, (records[0]["evidence_id"],))
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["inspection_type"], "frontend_qa")
        self.assertEqual(payload["result"]["project_id"], "WORKFLOW_TEST")
        self.assertEqual(payload["result"]["evidence_ids"], list(result.evidence_ids))
        self.assertEqual(len(records), 1)
        completed_stages = {
            event.stage for event in progress_events
            if event.status == "completed"
        }
        self.assertTrue({
            "Homepage", "Image Inspection", "Link Inspection",
            "Evidence Collection",
        }.issubset(completed_stages))
        self.assertTrue(any(
            event.stage == "Image Inspection"
            and event.current == 1 and event.total == 1
            for event in progress_events
        ))
        self.assertTrue(any(
            event.stage == "Link Inspection"
            and event.current == 1 and event.total == 1
            for event in progress_events
        ))


if __name__ == "__main__":
    unittest.main()
