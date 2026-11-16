
import json
import unittest
import shutil

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
        self.project_dir = PROJECTS_DIR / TEST_PROJECT_ID

        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

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
            self.project_dir / "documentation"
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
