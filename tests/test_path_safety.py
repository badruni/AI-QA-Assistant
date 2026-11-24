import tempfile
import unittest
from pathlib import Path

from core.path_safety import resolve_project_directory, resolve_project_path


class PathSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "projects"
        self.project = self.root / "PROJECT_A"
        self.project.mkdir(parents=True)

    def test_rejects_project_id_traversal(self):
        with self.assertRaises(ValueError):
            resolve_project_directory(self.root, "../outside")

    def test_resolves_contained_project_path(self):
        result = resolve_project_path(self.project, "evidence", "shot.png")
        self.assertEqual(result, self.project.resolve() / "evidence" / "shot.png")

    def test_rejects_relative_path_traversal(self):
        with self.assertRaises(ValueError):
            resolve_project_path(self.project, "reports", "..", "outside.json")

    def test_rejects_absolute_child_path(self):
        with self.assertRaises(ValueError):
            resolve_project_path(self.project, Path(self.temp.name) / "outside")

    def test_rejects_project_directory_symlink_when_supported(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        link = self.root / "PROJECT_LINK"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        with self.assertRaises(ValueError):
            resolve_project_directory(self.root, "PROJECT_LINK")


if __name__ == "__main__":
    unittest.main()
