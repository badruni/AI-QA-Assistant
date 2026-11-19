[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path
$StatePath = Join-Path $ProjectRoot "batch_scripts\.request_safety_delivery_state.json"
if (-not (Test-Path -LiteralPath $StatePath)) {
    throw "State Prepare tidak ditemukan. Jalankan Prepare_Request_Safety_Batch.ps1 terlebih dahulu."
}
$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if ($State.project_root -ne $ProjectRoot) {
    throw "Project root berbeda dari lokasi Prepare. Jalankan ulang Prepare pada repository ini."
}

$TestPath = Join-Path $ProjectRoot "tests\test_request_safety_delivery.py"
$DocPath = Join-Path $ProjectRoot "docs\FEATURE_01_REQUEST_SAFETY.md"
if ((Test-Path $TestPath) -or (Test-Path $DocPath)) {
    throw "Target file sudah ada. Tidak akan menimpa file pengguna: periksa $TestPath dan $DocPath."
}

$TestContent = @'
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
'@

$DocContent = @'
# Feature 01 — Request Safety & Rate Limit

## Tujuan
Mengendalikan laju request HTTP dan menghentikan pemindaian setelah ambang respons HTTP 403 berturut-turut tercapai.

## Ruang lingkup
- `core/request_safety.py`: rolling window 60 detik, batas 1–10 request per menit, dan penghentian 403.
- `core/playwright_request_guard.py`: pengendalian request browser dan pembatasan origin.
- `modules/frontend_scanner.py`: penggunaan controller pada homepage, image, dan link inspection.

## Acceptance criteria
- RS-01: Batas request valid antara 1 dan 10 per menit.
- RS-02: Timestamp request dikelola dengan rolling window 60 detik.
- RS-03: Request di bawah batas memperoleh slot.
- RS-04: Request berikutnya menunggu sampai slot tersedia.
- RS-05: Request dapat berlanjut setelah menunggu.
- RS-06: Timestamp kedaluwarsa dihitung satu per satu, bukan berdasarkan menit kalender.
- RS-07: Request browser melewati PlaywrightRequestGuard.
- RS-08: Pemeriksaan link API memanggil controller sebelum request.
- RS-09: Respons non-403 mereset hitungan 403 berturut-turut.
- RS-10: Scanner berhenti ketika ambang 403 tercapai.
- RS-11: Tidak ada request baru setelah controller berhenti.
- RS-12: Pengujian tambahan berjalan tanpa mengakses website publik.

## Bukti dan batasan verifikasi
Test tambahan menggunakan fake clock agar penantian 60 detik dapat diverifikasi tanpa menunggu waktu nyata. Test guard menggunakan mock route; ini membuktikan urutan pemanggilan controller sebelum fetch, bukan pengukuran trafik jaringan nyata.

Pengujian lokal 403 sebelumnya membuktikan `inspect_links()` berhenti setelah tiga respons 403 dan tidak meminta endpoint sentinel. Hasil tersebut merupakan bukti skenario lokal, bukan jaminan semua kemungkinan situs.

## Belum dinyatakan selesai
Paket ini belum mengubah implementasi produksi. Integrasi end-to-end rate limit pada masing-masing `inspect_homepage()`, `inspect_images()`, dan `inspect_links()` masih memerlukan pengujian khusus bila dependency injection controller diperlukan. Fitur baru dapat diterima 100% setelah seluruh test yang relevan dan regression suite lulus serta dokumentasi ditinjau.

## Menjalankan test tambahan
```powershell
& ".\.venv-scanner\Scripts\python.exe" -m unittest tests.test_request_safety_delivery -v
```

## Menjalankan regression suite
```powershell
& ".\.venv-scanner\Scripts\python.exe" -m unittest discover -s tests -v
```
'@

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($TestPath, $TestContent, $Utf8NoBom)
[System.IO.File]::WriteAllText($DocPath, $DocContent, $Utf8NoBom)

Write-Host "File tambahan berhasil dibuat:" -ForegroundColor Green
Write-Host " - tests\test_request_safety_delivery.py"
Write-Host " - docs\FEATURE_01_REQUEST_SAFETY.md"
Write-Host "File implementasi produksi tidak diubah."
