import unittest
from core.progress_tracking import ProgressEvent, ProgressReporter


class ProgressReporterTests(unittest.TestCase):
    def test_events_are_shared_and_can_be_indeterminate(self):
        events = []
        reporter = ProgressReporter(events.append)

        discovery = reporter.emit(
            "Website Discovery", "running", "Inspecting next page"
        )
        cms = reporter.emit("CMS Inspection", "waiting", "Waiting for stage")

        self.assertEqual(discovery, ProgressEvent(
            "Website Discovery", "running", "Inspecting next page", None, None
        ))
        self.assertIsNone(discovery.total)
        self.assertEqual(cms.stage, "CMS Inspection")
        self.assertEqual(events, [discovery, cms])

    def test_all_lifecycle_states_are_supported(self):
        reporter = ProgressReporter()
        for status in ("running", "waiting", "completed", "failed", "stopped"):
            with self.subTest(status=status):
                event = reporter.emit("Generic UAT", status, "Current activity")
                self.assertEqual(event.status, status)

    def test_invalid_or_simulated_counts_are_rejected(self):
        reporter = ProgressReporter()
        with self.assertRaises(ValueError):
            reporter.emit("Homepage", "running", "Work", 2, 1)
        with self.assertRaises(ValueError):
            reporter.emit("Homepage", "running", "Work", True, 1)
        with self.assertRaises(ValueError):
            reporter.emit("Homepage", "unknown", "Work")


if __name__ == "__main__":
    unittest.main()
