import unittest
from unittest.mock import Mock, patch

from playwright.sync_api import Error as PlaywrightError

from core.playwright_request_guard import PlaywrightRequestGuard
from core.request_safety import (
    RequestSafetyController,
    RequestSafetyStop,
)


class TestPlaywrightRequestGuard(unittest.TestCase):

    def setUp(self):
        self.controller = RequestSafetyController(
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

        self.guard = PlaywrightRequestGuard(
            self.controller,
            "https://client.example.com",
        )

    def make_route(self, url, status=200):
        route = Mock()
        route.request.url = url

        response = Mock()
        response.status = status

        route.fetch.return_value = response

        return route, response

    def test_same_origin_allowed(self):
        urls = [
            "https://client.example.com/",
            "https://client.example.com/about",
            "https://client.example.com/images/logo.png",
            "https://client.example.com:443/contact",
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(self.guard.is_allowed_url(url))

    def test_external_origin_blocked(self):
        urls = [
            "https://external.example.com/",
            "http://client.example.com/",
            "https://client.example.com:8443/",
            "https://client.example.com.evil.test/",
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertFalse(self.guard.is_allowed_url(url))

    def test_invalid_urls_blocked(self):
        urls = [
            "not-a-url",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "https://user:password@client.example.com/",
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertFalse(self.guard.is_allowed_url(url))

    def test_external_request_aborted_before_acquire(self):
        route, _ = self.make_route(
            "https://external.example.com/image.png"
        )

        with patch.object(
            self.controller,
            "acquire",
        ) as acquire:
            self.guard._handle_route(route)

        route.abort.assert_called_once_with("blockedbyclient")
        route.fetch.assert_not_called()
        route.fulfill.assert_not_called()
        acquire.assert_not_called()

    def test_internal_request_passes_controller(self):
        route, response = self.make_route(
            "https://client.example.com/about"
        )

        with patch.object(
            self.controller,
            "acquire",
        ) as acquire:
            self.guard._handle_route(route)

        acquire.assert_called_once()
        route.fetch.assert_called_once_with(max_redirects=0)
        route.fulfill.assert_called_once_with(response=response)
        route.abort.assert_not_called()

    def test_request_aborted_when_controller_stopped(self):
        route, _ = self.make_route(
            "https://client.example.com/about"
        )

        with patch.object(
            self.controller,
            "acquire",
            side_effect=RequestSafetyStop("Scanner stopped."),
        ):
            self.guard._handle_route(route)

        route.abort.assert_called_once_with("blockedbyclient")
        route.fetch.assert_not_called()

    def test_403_response_is_fulfilled_and_controller_stops(self):
        route, response = self.make_route(
            "https://client.example.com/",
            status=403,
        )

        controller = RequestSafetyController(
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )

        guard = PlaywrightRequestGuard(
            controller,
            "https://client.example.com",
        )

        guard._handle_route(route)

        self.assertTrue(controller.is_stopped)
        route.fulfill.assert_called_once_with(response=response)

    def test_request_after_403_limit_is_aborted(self):
        controller = RequestSafetyController(
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )

        guard = PlaywrightRequestGuard(
            controller,
            "https://client.example.com",
        )

        first_route, _ = self.make_route(
            "https://client.example.com/"
            , status=403
        )

        guard._handle_route(first_route)

        second_route, _ = self.make_route(
            "https://client.example.com/about"
        )

        guard._handle_route(second_route)

        second_route.abort.assert_called_once_with("blockedbyclient")
        second_route.fetch.assert_not_called()

    def test_redirect_is_blocked(self):
        route, response = self.make_route(
            "https://client.example.com/",
            status=302,
        )

        self.guard._handle_route(route)

        route.fetch.assert_called_once_with(max_redirects=0)
        route.abort.assert_called_once_with("blockedbyclient")
        route.fulfill.assert_not_called()

    def test_install_registers_context_route(self):
        context = Mock()

        self.guard.install(context)

        context.route.assert_called_once_with(
            "**/*",
            self.guard._handle_route,
        )

        self.assertTrue(self.guard.installed)

    def test_install_twice_is_rejected(self):
        context = Mock()

        self.guard.install(context)

        with self.assertRaises(RuntimeError):
            self.guard.install(context)

        self.assertEqual(context.route.call_count, 1)

    def test_playwright_fetch_error_aborts_request(self):
        route, _ = self.make_route(
            "https://client.example.com/"
        )

        route.fetch.side_effect = PlaywrightError(
            "Simulated network failure."
        )

        self.guard._handle_route(route)

        route.abort.assert_called_once_with()
        route.fulfill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
