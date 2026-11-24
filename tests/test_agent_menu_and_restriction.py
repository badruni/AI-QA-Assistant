import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import agent
from core.result_status import ResultStatus


class AgentMenuIntegrationTests(unittest.TestCase):
    def test_menu_labels_match_authentication_and_exit_handlers(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            agent.show_menu("001")

        menu = output.getvalue()
        self.assertIn("4. Jalankan Frontend QA Workflow", menu)
        self.assertIn("6. Jalankan Authentication Discovery", menu)
        self.assertIn("8. Evidence Viewer", menu)
        self.assertIn("9. Keluar", menu)
        self.assertIn("10. Unified QA Workflow", menu)
        self.assertIn("11. Kelola Otorisasi QA", menu)
        self.assertNotIn("7. Keluar", menu)

    def test_project_detail_redacts_legacy_sensitive_url_but_keeps_safe_query(self):
        secret_url = (
            "https://example.test/home?lang=id&page=2&"
            "X-Amz-Signature=SYNTHETIC_SECRET_2026"
        )
        with (
            patch.object(agent, "get_project", return_value={
                "project_id": "001", "project_name": "Test",
                "base_url": secret_url, "cms_url": "",
            }),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.show_active_project("001")
        shown = output.getvalue()
        self.assertNotIn("SYNTHETIC_SECRET_2026", shown)
        self.assertIn("lang=id", shown)
        self.assertIn("page=2", shown)
        self.assertIn("X-Amz-Signature=[REDACTED]", shown)


class AuthorizationMenuIntegrationTests(unittest.TestCase):
    def test_create_authorization_uses_project_target_and_read_only_scopes(self):
        config = SimpleNamespace(
            project_id="001", base_url="https://example.test/"
        )
        answers = iter(("2", "YA", "QA Owner", "31-12-2026", "23:59", "y", "0"))
        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "create_authorization", return_value={
                "authorization_id": "AUTH-SYNTHETIC",
                "expires_at": "2026-12-31T16:59:00+00:00",
            }) as create,
            patch("builtins.input", side_effect=lambda _prompt="": next(answers)),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            returned = agent.manage_project_authorization("001")

        self.assertEqual(returned, "001")
        create.assert_called_once_with(
            "001", "https://example.test/", "QA Owner",
            ["frontend", "read_only"],
            "2026-12-31T23:59:00+07:00",
            admin_access_confirmed=True,
        )
        self.assertIn("Otorisasi tersimpan", output.getvalue())
        self.assertIn("31 Desember 2026, 23:59 WIB", output.getvalue())

    def test_authorization_creation_requires_explicit_confirmation(self):
        config = SimpleNamespace(
            project_id="001", base_url="https://example.test/"
        )
        answers = iter(("2", "TIDAK", "0"))
        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "create_authorization") as create,
            patch("builtins.input", side_effect=lambda _prompt="": next(answers)),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            agent.manage_project_authorization("001")
        create.assert_not_called()

    def test_friendly_expiry_input_converts_wib_to_iso8601(self):
        value = agent._parse_authorization_expiry_input(
            "31-12-2099", "23:59"
        )
        self.assertEqual(value, "2099-12-31T23:59:00+07:00")

    def test_friendly_expiry_input_rejects_invalid_date(self):
        with self.assertRaises(ValueError):
            agent._parse_authorization_expiry_input("31-02-2099", "23:59")

    def test_friendly_expiry_input_rejects_invalid_time(self):
        with self.assertRaises(ValueError):
            agent._parse_authorization_expiry_input("31-12-2099", "25:61")

    def test_expiry_display_uses_indonesian_month_and_wib(self):
        self.assertEqual(
            agent._format_authorization_expiry("2099-12-31T16:59:00+00:00"),
            "31 Desember 2099, 23:59 WIB",
        )

class StandaloneAuthorizationGuardTests(unittest.TestCase):
    def test_frontend_scanner_does_not_run_without_authorization(self):
        config = SimpleNamespace(project_id="001", base_url="https://example.test/")
        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "_project_authorization_allowed", return_value=False),
            patch.object(agent, "run_frontend_qa_workflow") as scanner,
            patch.object(agent, "log_warning"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            returned = agent.run_frontend_homepage_scanner("001")
        self.assertEqual(returned, "001")
        scanner.assert_not_called()
        self.assertNotIn("[ERROR]", output.getvalue())

    def test_generic_uat_does_not_discover_without_authorization(self):
        config = SimpleNamespace(project_id="001", base_url="https://example.test/")
        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "_project_authorization_allowed", return_value=False),
            patch.object(agent, "discover_website") as discovery,
            patch.object(agent, "log_warning"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            agent.run_generic_uat_inspection("001")
        discovery.assert_not_called()

    def test_authentication_discovery_does_not_discover_without_authorization(self):
        config = SimpleNamespace(project_id="001", base_url="https://example.test/")
        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "_project_authorization_allowed", return_value=False),
            patch.object(agent, "discover_website") as discovery,
            patch.object(agent, "log_warning"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            agent.run_authentication_discovery("001")
        discovery.assert_not_called()


class GenericUATRestrictedIntegrationTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(
            agent, "_project_authorization_allowed", return_value=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_access_restricted_stops_before_generic_uat_inspection(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            status=ResultStatus.ACCESS_RESTRICTED,
            pages=(object(),),
            stopped_reason="HTTP 403",
        )

        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "discover_website", return_value=discovery),
            patch.object(agent, "inspect_generic_uat") as inspect_mock,
            patch.object(agent, "log_warning") as warning_mock,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            returned_project = agent.run_generic_uat_inspection("001")

        self.assertEqual(returned_project, "001")
        inspect_mock.assert_not_called()
        warning_mock.assert_called_once()
        self.assertIn("dihentikan", output.getvalue().lower())


class AdvancedInspectionURLDisplayTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(
            agent, "_project_authorization_allowed", return_value=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.marker = "SYNTHETIC_SECRET_2026"
        self.secret_url = (
            "https://example.test/page?lang=id&page=2&token=" + self.marker
        )
        self.config = SimpleNamespace(project_id="001")
        self.discovery = SimpleNamespace(
            status=ResultStatus.PASSED, pages=(object(),),
        )

    def test_authentication_discovery_terminal_url_is_sanitized(self):
        page = SimpleNamespace(
            page_url=self.secret_url, http_status=200,
            status=ResultStatus.PASSED, signals=(), message="Observed.",
        )
        result = SimpleNamespace(
            project_id="001", status=ResultStatus.PASSED,
            classification="NO_AUTH_SIGNAL", confidence="LOW",
            pages=(page,), completed=True, message="Completed.",
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=self.config),
            patch.object(agent, "discover_website", return_value=self.discovery),
            patch.object(agent, "inspect_authentication", return_value=result),
            patch.object(agent, "save_inspection_report", return_value="report.json"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_authentication_discovery("001")
        shown = output.getvalue()
        self.assertNotIn(self.marker, shown)
        self.assertIn("lang=id", shown)
        self.assertIn("page=2", shown)
        self.assertIn("token=[REDACTED]", shown)

    def test_generic_uat_terminal_url_is_sanitized(self):
        page = SimpleNamespace(
            page_url=self.secret_url, http_status=200,
            status=ResultStatus.PASSED, component_summary="one page",
            screenshot_path=None,
        )
        result = SimpleNamespace(
            project_id="001", status=ResultStatus.PASSED, pages=(page,),
            findings=(), completed=True, message="Completed.",
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=self.config),
            patch.object(agent, "discover_website", return_value=self.discovery),
            patch.object(agent, "inspect_generic_uat", return_value=result),
            patch.object(agent, "save_inspection_report", return_value="report.json"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_generic_uat_inspection("001")
        shown = output.getvalue()
        self.assertNotIn(self.marker, shown)
        self.assertIn("lang=id", shown)
        self.assertIn("page=2", shown)
        self.assertIn("token=[REDACTED]", shown)


class FrontendQAWorkflowMenuIntegrationTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(
            agent, "_project_authorization_allowed", return_value=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_homepage_menu_runs_and_persists_unified_report(self):
        homepage = SimpleNamespace(
            http_status=200, page_title="Homepage", final_url="https://example.test/",
            status=ResultStatus.PASSED, message="Homepage OK", screenshot_path=None,
        )
        result = SimpleNamespace(
            project_id="001", homepage=homepage, status=ResultStatus.PASSED,
            image_status=ResultStatus.PASSED, image_results=(object(),),
            image_message="Images checked", link_status=ResultStatus.PASSED,
            link_results=(object(),), link_message="Links checked", stopped_reason="",
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_frontend_qa_workflow", return_value=result) as run,
            patch.object(agent, "save_inspection_report", return_value="report.json") as save,
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_frontend_homepage_scanner("001")

        run.assert_called_once()
        save.assert_called_once_with("001", "frontend_qa", result)
        self.assertIn("Gambar", output.getvalue())
        self.assertIn("Tautan", output.getvalue())

    def test_homepage_terminal_output_redacts_sensitive_url_and_title(self):
        marker = "SYNTHETIC_SECRET_2026"
        homepage = SimpleNamespace(
            http_status=200, page_title=f"Home access_token={marker}",
            final_url=f"https://example.test/?lang=id&token={marker}",
            status=ResultStatus.PASSED, message="Homepage OK", screenshot_path=None,
        )
        result = SimpleNamespace(
            project_id="001", homepage=homepage, status=ResultStatus.PASSED,
            image_status=None, image_results=(), image_message="Skipped",
            link_status=None, link_results=(), link_message="Skipped",
            stopped_reason="", evidence_ids=("EV-SYNTHETIC",),
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_frontend_qa_workflow", return_value=result),
            patch.object(agent, "save_inspection_report", return_value="report.json"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_frontend_homepage_scanner("001")
        shown = output.getvalue()
        self.assertNotIn(marker, shown)
        self.assertIn("lang=id", shown)
        self.assertIn("token=[REDACTED]", shown)


    def test_frontend_final_status_maps_results_report_and_evidence(self):
        cases = (
            (ResultStatus.PASSED, ("EV-SYNTHETIC",), None, "completed"),
            (ResultStatus.INCONCLUSIVE, ("EV-SYNTHETIC",), None, "completed"),
            (ResultStatus.NEEDS_REVIEW, ("EV-SYNTHETIC",), None, "completed"),
            (ResultStatus.FAILED, ("EV-SYNTHETIC",), None, "failed"),
            (ResultStatus.BLOCKED, ("EV-SYNTHETIC",), None, "failed"),
            (ResultStatus.TIMEOUT, ("EV-SYNTHETIC",), None, "failed"),
            (ResultStatus.ACCESS_RESTRICTED, (), None, "stopped"),
            (ResultStatus.PASSED, (), None, "failed"),
            (ResultStatus.PASSED, ("EV-SYNTHETIC",), OSError("write failed"), "failed"),
        )
        for status, evidence_ids, report_error, expected in cases:
            with self.subTest(status=status, evidence_ids=evidence_ids, report_error=report_error):
                result = SimpleNamespace(status=status, evidence_ids=evidence_ids)
                self.assertEqual(
                    agent._frontend_qa_terminal_status(result, report_error),
                    expected,
                )

    def test_report_generation_failure_is_shown_without_losing_scan_result(self):
        homepage = SimpleNamespace(
            http_status=200, page_title="Homepage", final_url="http://127.0.0.1/",
            status=ResultStatus.PASSED, message="Homepage OK", screenshot_path=None,
        )
        result = SimpleNamespace(
            project_id="001", homepage=homepage, status=ResultStatus.PASSED,
            image_status=None, image_results=(), image_message="Skipped",
            link_status=None, link_results=(), link_message="Skipped",
            stopped_reason="", evidence_ids=(),
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_frontend_qa_workflow", return_value=result),
            patch.object(agent, "save_inspection_report", side_effect=OSError("disk full")),
            patch.object(agent, "log_warning") as warning,
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_frontend_homepage_scanner("001")

        self.assertIn("[FAILED] Report Generation", output.getvalue())
        self.assertIn("hasil inspeksi tetap tersedia", output.getvalue().lower())
        warning.assert_called_once()

    def test_frontend_scanner_runs_in_worker_and_shows_live_stages(self):
        import threading

        main_thread = threading.get_ident()
        observed = {}
        homepage = SimpleNamespace(
            http_status=200, page_title="Homepage", final_url="http://127.0.0.1/",
            status=ResultStatus.PASSED, message="Homepage OK", screenshot_path=None,
        )
        result = SimpleNamespace(
            project_id="001", homepage=homepage, status=ResultStatus.PASSED,
            image_status=ResultStatus.PASSED, image_results=(),
            image_message="Images checked", link_status=ResultStatus.PASSED,
            link_results=(), link_message="Links checked", stopped_reason="",
        )

        def run_with_events(config, progress):
            observed["thread_id"] = threading.get_ident()
            progress.emit("Homepage", "running", "Homepage loaded", 1, 1)
            progress.emit("Image Inspection", "completed", "1 image checked", 1, 1)
            progress.emit("Link Inspection", "stopped", "No links configured", 0, 0)
            progress.emit("Evidence Collection", "failed", "No screenshot evidence", 0, 1)
            return result

        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_frontend_qa_workflow", side_effect=run_with_events),
            patch.object(agent, "save_inspection_report", return_value="report.json"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_frontend_homepage_scanner("001")

        self.assertNotEqual(observed["thread_id"], main_thread)
        rendered = output.getvalue()
        self.assertIn("Homepage", rendered)
        self.assertIn("Image Inspection", rendered)
        self.assertIn("Link Inspection", rendered)
        self.assertIn("Evidence Collection", rendered)
        self.assertIn("Report Generation", rendered)
        self.assertIn("[FAILED]", rendered)
        self.assertIn("[STOPPED]", rendered)
        self.assertIn("1/1", rendered)


class UnifiedQAWorkflowMenuIntegrationTests(unittest.TestCase):
    def test_unified_workflow_saves_one_project_scoped_report(self):
        result = SimpleNamespace(
            project_id="001", status=ResultStatus.NEEDS_REVIEW,
            stages=(SimpleNamespace(
                name="website_discovery", status=ResultStatus.PASSED,
                message="Discovery selesai",
            ),),
            evidence_ids=("EV-LOCAL",),
        )
        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_unified_qa_workflow", return_value=result) as run,
            patch.object(agent, "save_inspection_report", return_value="unified.json") as save,
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(agent.run_unified_qa_inspection("001"), "001")

        run.assert_called_once()
        save.assert_called_once_with("001", "unified_qa", result)
        self.assertIn("website_discovery", output.getvalue())
        self.assertIn("EV-LOCAL", output.getvalue())

    def test_report_save_failure_marks_unified_workflow_failed(self):
        result = SimpleNamespace(
            project_id="001", status=ResultStatus.NEEDS_REVIEW,
            stages=(), evidence_ids=(),
        )

        def fake_workflow(_config, progress):
            progress.emit(
                "Unified Evidence Collection", "completed",
                "No screenshots were produced.", 0, 0,
            )
            return result

        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_unified_qa_workflow", side_effect=fake_workflow),
            patch.object(agent, "save_inspection_report", side_effect=OSError("disk full")),
            patch.object(agent, "log_warning"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_unified_qa_inspection("001")

        rendered = output.getvalue()
        self.assertIn("[FAILED] Report Generation", rendered)
        self.assertIn("[FAILED] Unified QA Workflow", rendered)
        self.assertNotIn("[COMPLETED] Unified QA Workflow", rendered)

    def test_access_restriction_with_report_failure_does_not_finish_as_success(self):
        result = SimpleNamespace(
            project_id="001", status=ResultStatus.ACCESS_RESTRICTED,
            stages=(), evidence_ids=(),
        )

        def restricted_workflow(_config, progress):
            progress.emit(
                "Unified Evidence Collection", "completed",
                "No screenshots were produced.", 0, 0,
            )
            return result

        with (
            patch.object(agent, "load_scanner_config", return_value=SimpleNamespace(
                project_name="Client", project_id="001"
            )),
            patch.object(agent, "run_unified_qa_workflow", side_effect=restricted_workflow),
            patch.object(agent, "save_inspection_report", side_effect=OSError("disk full")),
            patch.object(agent, "log_warning"),
            patch.object(agent, "log_info"),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            agent.run_unified_qa_inspection("001")

        rendered = output.getvalue()
        self.assertIn("[FAILED] Report Generation", rendered)
        self.assertIn("[FAILED] Unified QA Workflow", rendered)
        self.assertNotIn("[STOPPED] Unified QA Workflow", rendered)




class ProjectAuthorizationMenuDispatchTests(unittest.TestCase):
    def test_main_dispatches_menu_11_to_project_authorization_manager(self):
        with (
            patch.object(agent, "show_menu"),
            patch.object(agent, "manage_project_authorization", return_value="001") as manage,
            patch.object(agent, "log_info"),
            patch.object(agent, "log_warning"),
            patch("builtins.input", side_effect=["11", "9"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            agent.main()

        manage.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
