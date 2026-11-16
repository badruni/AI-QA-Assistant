import unittest

from unittest.mock import Mock

from core.request_safety import (
    RequestSafetyController,
    RequestSafetyStop,
)
from core.result_status import ResultStatus


class FakeClock:
    def __init__(self):
        self.current_time = 0.0

    def now(self):
        return self.current_time

    def sleep(self, seconds):
        self.current_time += seconds


class TestRequestSafetyController(unittest.TestCase):

    def setUp(self):
        self.clock = FakeClock()

    def create_controller(self, limit=10, stop_after_403=3):
        return RequestSafetyController(
            max_requests_per_minute=limit,
            stop_after_consecutive_403=stop_after_403,
            clock=self.clock.now,
            sleeper=self.clock.sleep,
        )

    def test_request_within_limit(self):
        controller = self.create_controller(limit=3)

        controller.acquire()
        controller.acquire()
        controller.acquire()

        self.assertEqual(len(controller._request_times), 3)

    def test_rate_limit_waits_until_window_expires(self):
        controller = self.create_controller(limit=2)

        controller.acquire()
        controller.acquire()

        controller.acquire()

        self.assertEqual(self.clock.current_time, 60.0)
        self.assertEqual(len(controller._request_times), 1)

    def test_403_counter_increases(self):
        controller = self.create_controller(stop_after_403=3)

        self.assertEqual(controller.record_response(403), 1)
        self.assertEqual(controller.record_response(403), 2)

    def test_non_403_resets_counter(self):
        controller = self.create_controller(stop_after_403=3)

        controller.record_response(403)
        controller.record_response(403)

        self.assertEqual(controller.record_response(200), 0)

        self.assertEqual(controller.record_response(403), 1)

    def test_stop_after_403_limit(self):
        controller = self.create_controller(stop_after_403=3)

        controller.record_response(403)
        controller.record_response(403)

        with self.assertRaises(RequestSafetyStop) as context:
            controller.record_response(403)

        self.assertTrue(controller.is_stopped)

        self.assertEqual(
            context.exception.status,
            ResultStatus.ACCESS_RESTRICTED,
        )

    def test_request_rejected_after_stop(self):
        controller = self.create_controller(stop_after_403=1)

        with self.assertRaises(RequestSafetyStop):
            controller.record_response(403)

        with self.assertRaises(RequestSafetyStop):
            controller.acquire()

    def test_invalid_rate_limit(self):
        invalid_limits = [0, 11, -1, True, 1.5]

        for limit in invalid_limits:
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    self.create_controller(limit=limit)

    def test_invalid_403_limit(self):
        invalid_limits = [0, -1, True, 1.5]

        for limit in invalid_limits:
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    self.create_controller(stop_after_403=limit)

    def test_invalid_http_status(self):
        controller = self.create_controller()

        invalid_statuses = [0, 600, -1, True, "403", 403.0]

        for status in invalid_statuses:
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    controller.record_response(status)


if __name__ == "__main__":
    unittest.main()
