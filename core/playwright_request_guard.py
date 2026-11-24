import asyncio
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError

from core.request_safety import (
    RequestSafetyController,
    RequestSafetyStop,
)
from core.security import has_sensitive_url_query


class PlaywrightRequestGuard:
    """Mengamankan request browser dan membatasi akses ke origin proyek."""

    def __init__(self, controller, base_url):
        if not isinstance(controller, RequestSafetyController):
            raise TypeError("Controller keamanan tidak valid.")

        self.controller = controller
        self.base_url = base_url
        self.allowed_origin = self._get_origin(base_url)

        if self.allowed_origin is None:
            raise ValueError("Base URL tidak valid untuk pembatasan origin.")
        if has_sensitive_url_query(base_url):
            raise ValueError(
                "Base URL memuat parameter sensitif dan tidak dapat dipindai."
            )

        self.installed = False
        self.shutting_down = False
        self.response_status_text = {}

    @staticmethod
    def _get_origin(url):
        try:
            parsed = urlsplit(url)

            scheme = parsed.scheme.lower()
            hostname = parsed.hostname

            if scheme not in ("http", "https") or not hostname:
                return None

            if parsed.username is not None or parsed.password is not None:
                return None

            port = parsed.port

            if port is None:
                port = 443 if scheme == "https" else 80

            return scheme, hostname.lower(), port

        except (TypeError, ValueError):
            return None

    def is_allowed_url(self, url):
        return (
            self._get_origin(url) == self.allowed_origin
            and not has_sensitive_url_query(url)
        )

    def install(self, context):
        if self.installed:
            raise RuntimeError("Request guard sudah dipasang.")

        context.route("**/*", self._handle_route)
        self.installed = True

    def begin_shutdown(self):
        """Prevent new route work before its browser context is closed."""
        self.shutting_down = True

    def _finish_route(self, route, action, *args, **kwargs):
        """Make one terminal route attempt, tolerating teardown races only."""
        try:
            getattr(route, action)(*args, **kwargs)
        except (PlaywrightError, asyncio.CancelledError):
            if not self.shutting_down:
                raise

    def _handle_route(self, route):
        if self.shutting_down:
            self._finish_route(route, "abort", "blockedbyclient")
            return

        request_url = route.request.url

        if not self.is_allowed_url(request_url):
            self._finish_route(route, "abort", "blockedbyclient")
            return

        try:
            self.controller.acquire()

        except RequestSafetyStop:
            self._finish_route(route, "abort", "blockedbyclient")
            return

        try:
            response = route.fetch(max_redirects=0)
            self.response_status_text[request_url] = response.status_text

        except asyncio.CancelledError:
            if not self.shutting_down:
                raise
            self._finish_route(route, "abort")
            return

        except PlaywrightError:
            self._finish_route(route, "abort")
            return

        try:
            self.controller.record_response(response.status)

        except RequestSafetyStop:
            self._finish_route(route, "fulfill", response=response)
            return

        # Redirect diblokir agar browser tidak mengikuti Location
        # di luar pengawasan route handler.
        if 300 <= response.status < 400:
            self._finish_route(route, "abort", "blockedbyclient")
            return

        self._finish_route(route, "fulfill", response=response)
