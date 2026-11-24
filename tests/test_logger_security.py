
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from core import logger


ROOT = Path(__file__).resolve().parent.parent


class TestLoggerSecurityIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.system_patch = patch.object(logger, "SYSTEM_LOG_DIR", self.root / "logs")
        self.system_patch.start()
        self.addCleanup(self.system_patch.stop)
        self.projects_patch = patch.object(logger, "PROJECTS_DIR", self.root / "projects")
        self.projects_patch.start()
        self.addCleanup(self.projects_patch.stop)

    def test_system_log_redacts_password(self):
        secret = "SYSTEM_FAKE_PASSWORD_98765"

        logger.log_info(
            "Security Integration Test",
            f"password={secret}"
        )

        log_files = list((self.root / "logs").glob("system_log_*.txt"))

        self.assertTrue(log_files, "System Log tidak ditemukan.")

        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)
        content = latest_log.read_text(encoding="utf-8")

        self.assertNotIn(secret, content)
        self.assertIn("[REDACTED]", content)

    def test_project_log_redacts_token(self):
        project_id = "SECURITY_TEST"
        secret = "PROJECT_FAKE_TOKEN_98765"

        logger.project_log_info(
            project_id,
            "Security Integration Test",
            f"access_token={secret}"
        )

        project_log_dir = self.root / "projects" / project_id / "logs"
        log_files = list(project_log_dir.glob("project_log_*.txt"))

        self.assertTrue(log_files, "Project Log tidak ditemukan.")

        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)
        content = latest_log.read_text(encoding="utf-8")

        self.assertNotIn(secret, content)
        self.assertIn("[REDACTED]", content)

    def test_system_log_redacts_signed_url_and_keeps_safe_query(self):
        secret = "SYNTHETIC_SECRET_2026"
        logger.log_info(
            "Signed URL Security Test",
            "Observed https://example.test/path?lang=id&page=2&"
            f"X-Amz-Signature={secret}",
        )
        log_files = list((self.root / "logs").glob("system_log_*.txt"))
        content = "\n".join(path.read_text(encoding="utf-8") for path in log_files)
        self.assertNotIn(secret, content)
        self.assertIn("lang=id", content)
        self.assertIn("page=2", content)
        self.assertIn("[REDACTED]", content)


if __name__ == "__main__":
    unittest.main()
