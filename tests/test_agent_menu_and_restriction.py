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
        self.assertIn("6. Jalankan Authentication Discovery", menu)
        self.assertIn("7. Keluar", menu)
        self.assertNotIn("6. Keluar", menu)


class GenericUATRestrictedIntegrationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()