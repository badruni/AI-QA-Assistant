import unittest
from unittest.mock import Mock

from core.request_safety import RequestSafetyController, RequestSafetyStop
from core.playwright_request_guard import PlaywrightRequestGuard


class FakeClock:
    def __init__(self):
        self.current_time = 0.0
        self.sleeps = []

    def now(self):
        return self.current_time

    def advance(self, seconds):
        self.current_time += seconds

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.current_time += seconds


class TestRequestSafetyDelivery(unittest.TestCase):
    def make_controller(self, limit=2, threshold=3):
        self.clock = FakeClock()
        return RequestSafetyController(
            max_requests_per_minute=limit,
            stop_after_consecutive_403=threshold,
            clock=self.clock.now,
            sleeper=self.clock.sleep,
        )

    def test_rolling_window_expires_each_request_individually(self):
        controller = self.make_controller(limit=2)
        controller.acquire()                 # t=0
        self.clock.advance(10)
        controller.acquire()                 # t=10
        self.clock.advance(10)
        controller.acquire()                 # waits until t=60

        self.assertEqual(self.clock.current_time, 60.0)
        self.assertEqual(self.clock.sleeps, [40.0])
        self.assertEqual(list(controller._request_times), [10.0, 60.0])

        self.clock.advance(10)
        controller.acquire()                 # t=70; t=10 expires
        self.assertEqual(self.clock.current_time, 70.0)
        self.assertEqual(list(controller._request_times), [60.0, 70.0])

    def test_limit_one_waits_full_window_then_continues(self):
        controller = self.make_controller(limit=1)
        controller.acquire()
        controller.acquire()
        self.assertEqual(self.clock.current_time, 60.0)
        self.assertEqual(self.clock.sleeps, [60.0])
        self.assertEqual(list(controller._request_times), [60.0])

    def test_exact_window_boundary_is_expired(self):
        controller = self.make_controller(limit=1)
        controller.acquire()
        self.clock.advance(60)
        controller.acquire()
        self.assertEqual(self.clock.sleeps, [])
        self.assertEqual(list(controller._request_times), [60.0])

    def test_non_403_resets_consecutive_403_count(self):
        controller = self.make_controller(threshold=3)
        self.assertEqual(controller.record_response(403), 1)
        self.assertEqual(controller.record_response(403), 2)
        self.assertEqual(controller.record_response(200), 0)
        self.assertEqual(controller.record_response(403), 1)
        self.assertFalse(controller.is_stopped)

    def test_no_request_can_be_acquired_after_403_stop(self):
        controller = self.make_controller(threshold=1)
        with self.assertRaises(RequestSafetyStop):
            controller.record_response(403)
        with self.assertRaises(RequestSafetyStop):
            controller.acquire()
        self.assertTrue(controller.is_stopped)

    def test_playwright_guard_applies_rate_limit_before_fetch(self):
        controller = self.make_controller(limit=1)
        guard = PlaywrightRequestGuard(
            controller=controller,
            base_url="http://127.0.0.1:8000/",
        )

        def make_route():
            route = Mock()
            route.request.url = "http://127.0.0.1:8000/resource"
            response = Mock()
            response.status = 200
            response.status_text = "OK"
            route.fetch.return_value = response
            return route

        first = make_route()
        guard._handle_route(first)
        first.fetch.assert_called_once_with(max_redirects=0)
        first.fulfill.assert_called_once_with(response=first.fetch.return_value)

        second = make_route()
        guard._handle_route(second)
        self.assertEqual(self.clock.sleeps, [60.0])
        second.fetch.assert_called_once_with(max_redirects=0)

    def test_playwright_guard_does_not_fetch_after_controller_stops(self):
        controller = self.make_controller(threshold=1)
        guard = PlaywrightRequestGuard(
            controller=controller,
            base_url="http://127.0.0.1:8000/",
        )
        with self.assertRaises(RequestSafetyStop):
            controller.record_response(403)

        route = Mock()
        route.request.url = "http://127.0.0.1:8000/next"
        guard._handle_route(route)

        route.abort.assert_called_once_with("blockedbyclient")
        route.fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()