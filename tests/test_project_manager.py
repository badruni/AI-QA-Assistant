
import json
import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

from core.project_manager import (
    create_project,
    list_projects,
    get_project,
    validate_project_id,
    validate_url,
    PROJECTS_DIR
)


TEST_PROJECT_ID = "PM_TEST_CLIENT"


class TestProjectManager(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.projects_patch = patch("core.project_manager.PROJECTS_DIR", Path(self.temp.name))
        self.projects_patch.start()
        self.addCleanup(self.projects_patch.stop)
        self.project_dir = Path(self.temp.name) / TEST_PROJECT_ID

    def test_valid_project_id(self):
        self.assertEqual(
            validate_project_id("client_001"),
            "client_001"
        )

    def test_invalid_project_id(self):
        invalid_ids = [
            "../client",
            "client/test",
            "client name",
            "",
            "client@001"
        ]

        for project_id in invalid_ids:
            with self.subTest(project_id=project_id):
                with self.assertRaises(ValueError):
                    validate_project_id(project_id)

    def test_valid_url(self):
        self.assertEqual(
            validate_url("https://example.com"),
            "https://example.com"
        )

    def test_non_sensitive_query_is_preserved_for_operational_use(self):
        url = "https://example.com/catalog?lang=id&page=2"
        self.assertEqual(validate_url(url), url)

        create_project(
            TEST_PROJECT_ID, "Project Manager Test", url
        )
        self.assertEqual(get_project(TEST_PROJECT_ID)["base_url"], url)

    def test_sensitive_query_is_rejected_before_project_config_is_written(self):
        url = (
            "https://example.com/?lang=id&access_token="
            "SYNTHETIC_SECRET_2026&signature=other-secret"
        )
        with self.assertRaisesRegex(ValueError, "parameter query sensitif"):
            create_project(
                TEST_PROJECT_ID, "Project Manager Test", url
            )
        self.assertFalse(self.project_dir.exists())
        self.assertFalse(any(
            "SYNTHETIC_SECRET_2026" in path.read_text(encoding="utf-8")
            for path in Path(self.temp.name).rglob("*.json")
        ))

    def test_invalid_url(self):
        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "https://",
            "https://user:password@example.com"
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_url(url)

    def test_create_project(self):
        project_dir = create_project(
            TEST_PROJECT_ID,
            "Project Manager Test",
            "https://example.com",
            "https://example.com/admin"
        )

        self.assertTrue(project_dir.is_dir())

        self.assertTrue(
            (project_dir / "project_config.json").is_file()
        )

        expected_directories = [
            "logs",
            "documentation",
            "reports",
            "evidence/screenshots",
            "evidence/attachments"
        ]

        for directory in expected_directories:
            with self.subTest(directory=directory):
                self.assertTrue(
                    (project_dir / directory).is_dir()
                )

    def test_project_config(self):
        create_project(
            TEST_PROJECT_ID,
            "Project Manager Test",
            "https://example.com"
        )

        config = get_project(TEST_PROJECT_ID)

        self.assertEqual(
            config["project_id"],
            TEST_PROJECT_ID
        )

        self.assertEqual(
            config["project_name"],
            "Project Manager Test"
        )

        self.assertEqual(
            config["base_url"],
            "https://example.com"
        )

        self.assertEqual(config["cms_url"], "")

        self.assertNotIn("password", config)

    def test_list_projects(self):
        create_project(
            TEST_PROJECT_ID,
            "Project Manager Test",
            "https://example.com"
        )

        projects = list_projects()

        project_ids = [
            project["project_id"]
            for project in projects
        ]

        self.assertIn(TEST_PROJECT_ID, project_ids)

        self.assertNotIn("LOGGER_TEST", project_ids)
        self.assertNotIn("SECURITY_TEST", project_ids)

    def test_duplicate_project(self):
        create_project(
            TEST_PROJECT_ID,
            "Project Manager Test",
            "https://example.com"
        )

        with self.assertRaises(FileExistsError):
            create_project(
                TEST_PROJECT_ID,
                "Duplicate Project",
                "https://example.com"
            )

    def test_invalid_project_config(self):
        create_project(
            TEST_PROJECT_ID,
            "Project Manager Test",
            "https://example.com"
        )

        config_file = (
            self.project_dir / "project_config.json"
        )

        config_file.write_text(
            "{ invalid json }",
            encoding="utf-8"
        )

        with self.assertRaises(json.JSONDecodeError):
            get_project(TEST_PROJECT_ID)

    def test_partial_project_creation_cleanup(self):
        original_mkdir = Path.mkdir

        failed_directory = (
            self.project_dir.resolve() / "documentation"
        )

        def simulate_mkdir_failure(path, *args, **kwargs):
            if path == failed_directory:
                raise OSError(
                    "Simulasi kegagalan pembuatan folder."
                )

            return original_mkdir(
                path, *args, **kwargs
            )

        with patch(
            "pathlib.Path.mkdir",
            new=simulate_mkdir_failure
        ):
            with self.assertRaises(OSError):
                create_project(
                    TEST_PROJECT_ID,
                    "Project Manager Test",
                    "https://example.com"
                )

        self.assertFalse(
            self.project_dir.exists(),
            "Folder proyek setengah jadi masih tertinggal."
        )


if __name__ == "__main__":
    unittest.main()
