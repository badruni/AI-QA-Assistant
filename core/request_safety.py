import time
from collections import deque

from core.result_status import ResultStatus


class RequestSafetyStop(Exception):
    """Exception ketika scanner harus berhenti demi keamanan."""

    def __init__(self, message):
        super().__init__(message)
        self.status = ResultStatus.ACCESS_RESTRICTED


class RequestSafetyController:
    """Mengatur batas request dan penghentian akibat HTTP 403."""

    WINDOW_SECONDS = 60.0

    def __init__(
        self,
        max_requests_per_minute,
        stop_after_consecutive_403,
        clock=None,
        sleeper=None,
    ):
        if (
            isinstance(max_requests_per_minute, bool)
            or not isinstance(max_requests_per_minute, int)
            or not 1 <= max_requests_per_minute <= 10
        ):
            raise ValueError(
                "Batas request harus berupa angka antara 1 dan 10 per menit."
            )

        if (
            isinstance(stop_after_consecutive_403, bool)
            or not isinstance(stop_after_consecutive_403, int)
            or stop_after_consecutive_403 < 1
        ):
            raise ValueError(
                "Batas penghentian 403 harus berupa bilangan bulat positif."
            )

        self.max_requests_per_minute = max_requests_per_minute
        self.stop_after_consecutive_403 = stop_after_consecutive_403

        self._clock = clock or time.monotonic
        self._sleep = sleeper or time.sleep

        self._request_times = deque()
        self._consecutive_403 = 0
        self._stopped = False
        self._stop_reason = None

    @property
    def consecutive_403(self):
        return self._consecutive_403

    @property
    def is_stopped(self):
        return self._stopped

    @property
    def stop_reason(self):
        return self._stop_reason

    def ensure_can_request(self):
        """Memastikan scanner belum dihentikan."""
        if self._stopped:
            raise RequestSafetyStop(
                self._stop_reason or "Scanner dihentikan demi keamanan."
            )

    def acquire(self):
        """
        Memastikan slot request tersedia.

        Metode ini harus dipanggil tepat sebelum setiap request HTTP.
        """
        while True:
            self.ensure_can_request()

            now = self._clock()

            while (
                self._request_times
                and now - self._request_times[0] >= self.WINDOW_SECONDS
            ):
                self._request_times.popleft()

            if len(self._request_times) < self.max_requests_per_minute:
                self._request_times.append(now)
                return

            wait_seconds = (
                self.WINDOW_SECONDS
                - (now - self._request_times[0])
            )

            self._sleep(max(wait_seconds, 0))

    def record_response(self, status_code):
        """Mencatat status HTTP dan menghentikan scanner jika perlu."""
        self.ensure_can_request()

        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise ValueError("Status HTTP tidak valid.")

        if status_code == 403:
            self._consecutive_403 += 1

            if (
                self._consecutive_403
                >= self.stop_after_consecutive_403
            ):
                self._stopped = True
                self._stop_reason = (
                    "Scanner dihentikan karena mencapai batas "
                    f"{self.stop_after_consecutive_403} "
                    "respons HTTP 403 berturut-turut."
                )

                raise RequestSafetyStop(self._stop_reason)

        else:
            self._consecutive_403 = 0

        return self._consecutive_403
