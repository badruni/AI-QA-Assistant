import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core import evidence_manager, project_manager, report_manager
from core.result_status import ResultStatus
from core.progress_tracking import ProgressReporter
from modules import qa_workflow
from modules.frontend_scanner import ScannerConfig


class UnifiedQAWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.project_dir = self.root / "UNIFIED_TEST"
        (self.project_dir / "evidence" / "screenshots").mkdir(parents=True)
        (self.project_dir / "reports").mkdir()
        (self.project_dir / "project_config.json").write_text(
            json.dumps({"project_id": "UNIFIED_TEST"}), encoding="utf-8"
        )
        self.config = ScannerConfig(
            "UNIFIED_TEST", "Unified Test", "http://127.0.0.1/",
            self.project_dir, False, False, 10, 3,
        )
        authorization_patcher = patch.object(
            qa_workflow, "validate_authorization",
            return_value=(True, "authorized"),
        )
        authorization_patcher.start()
        self.addCleanup(authorization_patcher.stop)

    def test_missing_authorization_blocks_before_any_network_stage(self):
        with (
            patch.object(
                qa_workflow, "validate_authorization",
                return_value=(False, "authorization_missing"),
            ) as validate,
            patch.object(qa_workflow, "run_frontend_qa_workflow") as frontend,
            patch.object(qa_workflow, "discover_website") as discovery,
            patch.object(qa_workflow, "inspect_generic_uat") as uat,
            patch.object(qa_workflow, "inspect_authentication") as auth,
        ):
            result = qa_workflow.run_unified_qa_workflow(self.config)

        validate.assert_called_once_with(
            "UNIFIED_TEST", "http://127.0.0.1/",
            required_scope=["frontend", "read_only"],
        )
        frontend.assert_not_called()
        discovery.assert_not_called()
        uat.assert_not_called()
        auth.assert_not_called()
        self.assertEqual(result.status, ResultStatus.BLOCKED)
        self.assertIsNone(result.frontend)
        self.assertEqual(result.evidence_ids, ())
        self.assertEqual(result.permission_check_status, "blocked")
        self.assertEqual(result.permission_check_message, "authorization_missing")
        self.assertEqual(result.stages[0].status, ResultStatus.BLOCKED)

    def test_authorization_validation_error_fails_closed(self):
        with (
            patch.object(
                qa_workflow, "validate_authorization",
                side_effect=OSError("synthetic storage error"),
            ),
            patch.object(qa_workflow, "run_frontend_qa_workflow") as frontend,
        ):
            result = qa_workflow.run_unified_qa_workflow(self.config)

        frontend.assert_not_called()
        self.assertEqual(result.status, ResultStatus.BLOCKED)
        self.assertEqual(
            result.permission_check_message, "authorization_check_failed"
        )

    def test_access_restricted_frontend_skips_every_advanced_stage(self):
        events = []
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.ACCESS_RESTRICTED,
            homepage=SimpleNamespace(screenshot_path=None),
            stopped_reason="CLOUDFLARE_CHALLENGE", evidence_ids=(),
        )
        with (
            patch.object(qa_workflow, "run_frontend_qa_workflow", return_value=frontend),
            patch.object(qa_workflow, "discover_website") as discovery,
            patch.object(qa_workflow, "inspect_generic_uat") as uat,
            patch.object(qa_workflow, "inspect_authentication") as auth,
            patch.object(qa_workflow, "list_evidence", return_value=()),
        ):
            result = qa_workflow.run_unified_qa_workflow(
                self.config, progress=ProgressReporter(events.append)
            )

        discovery.assert_not_called()
        uat.assert_not_called()
        auth.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertIsNone(result.website_discovery)
        self.assertEqual(result.stages[0].name, "authorization_preflight")
        self.assertEqual(result.stages[0].status, ResultStatus.PASSED)
        self.assertEqual(result.stages[1].status, ResultStatus.ACCESS_RESTRICTED)
        self.assertTrue(all(stage.status is None for stage in result.stages[2:]))
        terminal_by_stage = {}
        for event in events:
            if event.status in {"completed", "failed", "stopped"}:
                terminal_by_stage[event.stage] = event.status
        self.assertEqual(terminal_by_stage["Unified Inspection"], "stopped")
        self.assertEqual(terminal_by_stage["Website Discovery"], "stopped")
        self.assertEqual(terminal_by_stage["Generic UAT"], "stopped")
        self.assertEqual(terminal_by_stage["Authentication Discovery"], "stopped")

    def test_discovery_access_restriction_skips_uat_and_authentication(self):
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            homepage=SimpleNamespace(screenshot_path=None),
            stopped_reason="", evidence_ids=(),
        )
        discovery = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.ACCESS_RESTRICTED,
            stopped_reason="CLOUDFLARE_CHALLENGE", message="challenge",
            pages=(),
        )
        with (
            patch.object(qa_workflow, "run_frontend_qa_workflow", return_value=frontend),
            patch.object(qa_workflow, "discover_website", return_value=discovery),
            patch.object(qa_workflow, "inspect_generic_uat") as uat,
            patch.object(qa_workflow, "inspect_authentication") as auth,
            patch.object(qa_workflow, "list_evidence", return_value=()),
        ):
            result = qa_workflow.run_unified_qa_workflow(self.config)

        uat.assert_not_called()
        auth.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertIsNone(result.generic_uat)
        self.assertIsNone(result.authentication_discovery)

    def test_uat_access_restriction_skips_authentication(self):
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            homepage=SimpleNamespace(screenshot_path=None),
            stopped_reason="", evidence_ids=(),
        )
        discovery = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            stopped_reason="", message="discovered", pages=(),
        )
        uat = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.ACCESS_RESTRICTED,
            stopped_reason="HTTP 403 threshold", message="restricted", pages=(),
        )
        with (
            patch.object(qa_workflow, "run_frontend_qa_workflow", return_value=frontend),
            patch.object(qa_workflow, "discover_website", return_value=discovery),
            patch.object(qa_workflow, "inspect_generic_uat", return_value=uat),
            patch.object(qa_workflow, "inspect_authentication") as auth,
            patch.object(qa_workflow, "list_evidence", return_value=()),
        ):
            result = qa_workflow.run_unified_qa_workflow(self.config)

        auth.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertIsNone(result.authentication_discovery)

    def test_unverified_evidence_is_not_claimed_in_workflow_result(self):
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            homepage=SimpleNamespace(screenshot_path=self.project_dir / "evidence" / "screenshots" / "not-registered.png"),
            stopped_reason="", evidence_ids=(),
        )
        with (
            patch.object(qa_workflow, "list_evidence", return_value=({
                "evidence_id": "EV-UNVERIFIED",
                "file_path": "screenshots/not-registered.png",
            },)),
            patch.object(qa_workflow, "verify_evidence", return_value=False),
        ):
            self.assertEqual(qa_workflow._evidence_ids(self.config, frontend, None, None), ())

    def test_evidence_verification_failure_has_failed_progress_terminal(self):
        screenshot = self.project_dir / "evidence" / "screenshots" / "not-verified.png"
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            homepage=SimpleNamespace(
                screenshot_path=screenshot, status=ResultStatus.PASSED,
            ),
            image_results=(), link_results=(), evidence_ids=(), stopped_reason="",
        )
        events = []
        with (
            patch.object(qa_workflow, "list_evidence", return_value=({
                "evidence_id": "EV-CHANGED",
                "file_path": "screenshots/not-verified.png",
            },)),
            patch.object(qa_workflow, "verify_evidence", return_value=False),
        ):
            result = qa_workflow._make_result(
                self.config, frontend, None, None, None, (),
                ProgressReporter(events.append),
            )

        terminal = [event for event in events if event.status in {
            "completed", "failed", "stopped",
        }]
        evidence = next(
            event for event in terminal
            if event.stage == "Unified Evidence Collection"
        )
        inspection = next(
            event for event in terminal if event.stage == "Unified Inspection"
        )
        self.assertEqual(result.evidence_ids, ())
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.evidence_status, "failed")
        self.assertEqual(result.expected_evidence, 1)
        self.assertEqual(result.verified_evidence, 0)
        self.assertEqual(evidence.status, "failed")
        self.assertEqual(inspection.status, "failed")
    def test_all_stages_share_the_safety_controller(self):
        observed = []
        frontend = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            homepage=SimpleNamespace(screenshot_path=None),
            stopped_reason="", evidence_ids=(),
        )
        discovery = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            stopped_reason="", message="discovered", pages=(),
        )
        uat = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            stopped_reason="", message="uat", pages=(),
        )
        auth = SimpleNamespace(
            project_id="UNIFIED_TEST", status=ResultStatus.PASSED,
            stopped_reason="", message="auth", pages=(),
        )

        def frontend_call(_config, timeout_ms, controller):
            observed.append(controller)
            return frontend

        def discovery_call(_config, timeout_ms, controller):
            observed.append(controller)
            return discovery

        def uat_call(_config, _discovery, timeout_ms, controller):
            observed.append(controller)
            return uat

        def auth_call(_config, _discovery, timeout_ms, controller):
            observed.append(controller)
            return auth

        with (
            patch.object(qa_workflow, "run_frontend_qa_workflow", side_effect=frontend_call),
            patch.object(qa_workflow, "discover_website", side_effect=discovery_call),
            patch.object(qa_workflow, "inspect_generic_uat", side_effect=uat_call),
            patch.object(qa_workflow, "inspect_authentication", side_effect=auth_call),
            patch.object(qa_workflow, "list_evidence", return_value=()),
        ):
            result = qa_workflow.run_unified_qa_workflow(self.config)

        self.assertEqual(len(observed), 4)
        self.assertTrue(all(item is observed[0] for item in observed))
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.evidence_status, "not_required")
        self.assertEqual(result.expected_evidence, 0)
        self.assertEqual(result.verified_evidence, 0)

    def test_local_end_to_end_report_contains_all_results_and_verified_evidence(self):
        events = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = (
                    b"<html><head><title>Local QA</title></head><body>"
                    b"<nav>Home</nav><h1>Local test page</h1></body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        config = ScannerConfig(
            "UNIFIED_TEST", "Unified Test",
            f"http://127.0.0.1:{server.server_address[1]}/",
            self.project_dir, False, False, 10, 3,
        )

        with (
            patch.object(evidence_manager, "PROJECTS_DIR", self.root),
            patch.object(project_manager, "PROJECTS_DIR", self.root),
            patch.object(report_manager, "PROJECTS_DIR", self.root),
        ):
            result = qa_workflow.run_unified_qa_workflow(
                config, timeout_ms=10000,
                progress=ProgressReporter(events.append),
            )
            report = report_manager.save_inspection_report(
                "UNIFIED_TEST", "unified_qa", result
            )
            records = evidence_manager.list_evidence("UNIFIED_TEST")
            for evidence_id in result.evidence_ids:
                self.assertTrue(evidence_manager.verify_evidence(
                    "UNIFIED_TEST", evidence_id
                ))

        self.assertEqual(result.project_id, "UNIFIED_TEST")
        self.assertEqual(len(result.stages), 5)
        self.assertEqual(len(records), 3)
        self.assertEqual(len(result.evidence_ids), 3)
        self.assertEqual(result.evidence_status, "verified")
        self.assertEqual(result.expected_evidence, 3)
        self.assertEqual(result.verified_evidence, 3)
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["inspection_type"], "unified_qa")
        self.assertEqual(payload["result"]["project_id"], "UNIFIED_TEST")
        self.assertEqual(payload["result"]["permission_check_status"], "authorized")
        self.assertEqual(payload["result"]["evidence_status"], "verified")
        self.assertEqual(payload["result"]["expected_evidence"], 3)
        self.assertEqual(payload["result"]["verified_evidence"], 3)
        self.assertEqual(payload["result"]["status"], "Needs Review")
        self.assertEqual(payload["result"]["authentication_discovery"]["classification"],
                         "NO_LOGIN_DETECTED")
        terminal_events = [
            event for event in events
            if event.status in {"completed", "failed", "stopped"}
        ]
        terminal_stages = [event.stage for event in terminal_events]
        self.assertLess(terminal_stages.index("Website Discovery"),
                        terminal_stages.index("Generic UAT"))
        self.assertLess(terminal_stages.index("Generic UAT"),
                        terminal_stages.index("Authentication Discovery"))
        self.assertLess(terminal_stages.index("Authentication Discovery"),
                        terminal_stages.index("Unified Evidence Collection"))
        self.assertLess(terminal_stages.index("Unified Evidence Collection"),
                        terminal_stages.index("Unified Inspection"))
        self.assertEqual(
            next(event for event in terminal_events if event.stage == "Unified Evidence Collection").status,
            "completed",
        )
        self.assertEqual(
            next(event for event in terminal_events if event.stage == "Unified Inspection").status,
            "completed",
        )
        by_stage = {event.stage: event for event in terminal_events}
        self.assertEqual(
            (by_stage["Website Discovery"].current,
             by_stage["Website Discovery"].total),
            (1, None),
        )
        self.assertEqual(
            (by_stage["Generic UAT"].current, by_stage["Generic UAT"].total),
            (1, 1),
        )
        self.assertEqual(
            (by_stage["Authentication Discovery"].current,
             by_stage["Authentication Discovery"].total),
            (1, 1),
        )


if __name__ == "__main__":
    unittest.main()
