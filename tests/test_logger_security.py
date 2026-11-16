
import unittest
from pathlib import Path

from core.logger import log_info, project_log_info


ROOT = Path(__file__).resolve().parent.parent


class TestLoggerSecurityIntegration(unittest.TestCase):

    def test_system_log_redacts_password(self):
        secret = "SYSTEM_FAKE_PASSWORD_98765"

        log_info(
            "Security Integration Test",
            f"password={secret}"
        )

        log_files = list(ROOT.joinpath("logs").glob("system_log_*.txt"))

        self.assertTrue(log_files, "System Log tidak ditemukan.")

        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)
        content = latest_log.read_text(encoding="utf-8")

        self.assertNotIn(secret, content)
        self.assertIn("[REDACTED]", content)

    def test_project_log_redacts_token(self):
        project_id = "SECURITY_TEST"
        secret = "PROJECT_FAKE_TOKEN_98765"

        project_log_info(
            project_id,
            "Security Integration Test",
            f"access_token={secret}"
        )

        project_log_dir = ROOT / "projects" / project_id / "logs"
        log_files = list(project_log_dir.glob("project_log_*.txt"))

        self.assertTrue(log_files, "Project Log tidak ditemukan.")

        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)
        content = latest_log.read_text(encoding="utf-8")

        self.assertNotIn(secret, content)
        self.assertIn("[REDACTED]", content)


if __name__ == "__main__":
    unittest.main()
