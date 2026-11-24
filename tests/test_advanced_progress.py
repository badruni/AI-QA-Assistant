import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.progress_tracking import ProgressReporter, terminal_status_for_results
from core.result_status import ResultStatus
from modules import authentication_discovery, generic_uat_inspection, website_discovery


class AdvancedProgressStatusTests(unittest.TestCase):
    def test_terminal_mapping_distinguishes_processing_outcomes(self):
        cases = (
            (ResultStatus.PASSED, "completed"),
            (ResultStatus.NEEDS_REVIEW, "completed"),
            (ResultStatus.FAILED, "failed"),
            (ResultStatus.BLOCKED, "failed"),
            (ResultStatus.TIMEOUT, "failed"),
            (ResultStatus.ACCESS_RESTRICTED, "stopped"),
        )
        for result, expected in cases:
            with self.subTest(result=result):
                self.assertEqual(terminal_status_for_results((result,)), expected)

    def test_each_advanced_module_maps_page_timeout_to_failed_terminal(self):
        config = SimpleNamespace(project_id="PROGRESS_TEST")
        passed_discovery = SimpleNamespace(
            project_id="PROGRESS_TEST", status=ResultStatus.PASSED,
            pages=(SimpleNamespace(status=ResultStatus.PASSED),),
        )
        stage_results = (
            (
                "Website Discovery", website_discovery,
                "_discover_website_impl", (config,),
                SimpleNamespace(status=ResultStatus.NEEDS_REVIEW,
                                 pages=(SimpleNamespace(status=ResultStatus.TIMEOUT),)),
            ),
            (
                "Generic UAT", generic_uat_inspection,
                "_inspect_generic_uat_impl", (config, passed_discovery),
                SimpleNamespace(status=ResultStatus.NEEDS_REVIEW,
                                 pages=(SimpleNamespace(status=ResultStatus.TIMEOUT),)),
            ),
            (
                "Authentication Discovery", authentication_discovery,
                "_inspect_authentication_impl", (config, passed_discovery),
                SimpleNamespace(status=ResultStatus.NEEDS_REVIEW,
                                 classification="NEEDS_REVIEW",
                                 pages=(SimpleNamespace(status=ResultStatus.TIMEOUT),)),
            ),
        )

        for stage, module, implementation, args, result in stage_results:
            with self.subTest(stage=stage):
                events = []
                with patch.object(module, implementation, return_value=result):
                    if stage == "Website Discovery":
                        module.discover_website(
                            *args, progress=ProgressReporter(events.append)
                        )
                    elif stage == "Generic UAT":
                        module.inspect_generic_uat(
                            *args, progress=ProgressReporter(events.append)
                        )
                    else:
                        module.inspect_authentication(
                            *args, progress=ProgressReporter(events.append)
                        )
                terminal = [event for event in events if event.stage == stage][-1]
                self.assertEqual(terminal.status, "failed")
                self.assertIn("Timeout", terminal.activity)

    def test_module_exception_emits_failed_terminal(self):
        events = []
        with patch.object(
            website_discovery, "_discover_website_impl",
            side_effect=RuntimeError("synthetic failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                website_discovery.discover_website(
                    SimpleNamespace(), progress=ProgressReporter(events.append)
                )
        terminal = [event for event in events if event.stage == "Website Discovery"][-1]
        self.assertEqual(terminal.status, "failed")


if __name__ == "__main__":
    unittest.main()
