import unittest
from pathlib import Path
from unittest.mock import patch

import agent


class EvidenceViewerOpenTests(unittest.TestCase):
    def test_uses_windows_default_association_first(self):
        screenshot = Path("C:/evidence/home.png")
        with (
            patch.object(agent.os, "startfile", create=True) as start_file,
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            agent.open_screenshot_file(screenshot)
        start_file.assert_called_once_with(str(screenshot))
        popen.assert_not_called()

    def test_uses_explorer_when_startfile_raises_winerror_1155(self):
        screenshot = Path("C:/evidence/home.png")
        error = OSError("No application is associated with the specified file")
        error.winerror = 1155
        with (
            patch.object(agent.os, "startfile", create=True, side_effect=error),
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            agent.open_screenshot_file(screenshot)
        popen.assert_called_once_with(["explorer.exe", str(screenshot)])

    def test_does_not_fallback_for_other_os_errors(self):
        screenshot = Path("C:/evidence/home.png")
        error = OSError("Access is denied")
        error.winerror = 5
        with (
            patch.object(agent.os, "startfile", create=True, side_effect=error),
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            with self.assertRaises(OSError) as raised:
                agent.open_screenshot_file(screenshot)
        self.assertIs(raised.exception, error)
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
