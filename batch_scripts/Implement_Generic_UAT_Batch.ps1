$ErrorActionPreference = "Stop"

# Jalankan dari root proyek AI-QA-Assistant.
$Root = (Get-Location).Path
$RequiredFiles = @(
    ".\agent.py",
    ".\modules\frontend_scanner.py",
    ".\modules\website_discovery.py",
    ".\tests\test_website_discovery.py",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File. Jalankan skrip dari root proyek."
    }
}

$Python = ".\.venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = ".\backups\before_generic_uat_batch_$Stamp"
New-Item -ItemType Directory -Path $Backup -Force | Out-Null

$FilesToBackup = @(
    ".\agent.py",
    ".\modules\generic_uat_inspection.py",
    ".\tests\test_generic_uat_inspection.py",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $FilesToBackup) {
    if (Test-Path $File -PathType Leaf) {
        $Destination = Join-Path $Backup ([IO.Path]::GetFileName($File))
        Copy-Item $File $Destination -Force
    }
}
Write-Host "Backup dibuat: $((Resolve-Path $Backup).Path)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 1. Modul Generic UAT Inspection
# ---------------------------------------------------------------------------
$Module = @'
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from core.playwright_request_guard import PlaywrightRequestGuard
from core.request_safety import RequestSafetyController
from core.result_status import ResultStatus


@dataclass(frozen=True)
class UATFinding:
    page_url: str
    category: str
    element: str
    issue: str
    status: ResultStatus = ResultStatus.NEEDS_REVIEW


@dataclass(frozen=True)
class UATPageResult:
    page_url: str
    http_status: int | None
    status: ResultStatus
    component_summary: dict
    screenshot_path: Path | None
    message: str


@dataclass(frozen=True)
class GenericUATResult:
    project_id: str
    status: ResultStatus
    pages: tuple
    findings: tuple
    completed: bool
    stopped_reason: str
    message: str


def _build_findings(page_url, snapshot):
    """Membuat indikasi DOM untuk ditinjau; bukan vonis bug fungsional."""
    findings = []
    checks = (
        ("links_without_href", "link", "Tautan tidak memiliki tujuan href."),
        ("links_without_name", "link", "Tautan tidak memiliki accessible name."),
        ("buttons_without_name", "button", "Tombol tidak memiliki accessible name."),
        ("inputs_without_label", "input", "Input tidak memiliki label yang terdeteksi."),
        ("images_without_alt", "image", "Gambar tidak memiliki atribut alt."),
    )

    for key, element, issue in checks:
        count = snapshot.get(key, 0)
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            continue
        for index in range(min(count, 500)):
            findings.append(UATFinding(
                page_url=page_url,
                category="accessibility_or_structure",
                element=f"{element}[{index + 1}]",
                issue=issue,
            ))
    return findings


def _inspect_dom(page):
    """Mengambil ringkasan DOM tanpa klik, submit, atau membaca nilai input."""
    return page.evaluate("""() => {
        const all = selector => [...document.querySelectorAll(selector)];
        const visible = el =>
            !!el.getClientRects().length &&
            getComputedStyle(el).visibility !== 'hidden' &&
            getComputedStyle(el).display !== 'none';

        const hasName = el => {
            const aria = (el.getAttribute('aria-label') || '').trim();
            const title = (el.getAttribute('title') || '').trim();
            const labelledBy = (el.getAttribute('aria-labelledby') || '')
                .split(/\\s+/).filter(Boolean)
                .some(id => {
                    const node = document.getElementById(id);
                    return !!node && !!node.textContent.trim();
                });
            const text = (el.innerText || '').trim();
            return !!(aria || title || labelledBy || text);
        };

        const links = all('a').filter(visible);
        const buttons = all(
            'button, input[type="button"], input[type="submit"], [role="button"]'
        ).filter(visible);
        const inputs = all(
            'input:not([type="hidden"]), textarea, select, [contenteditable="true"]'
        ).filter(visible);
        const images = all('img').filter(visible);

        const linksWithoutHref = links.filter(el =>
            !((el.getAttribute('href') || '').trim())
        );
        const linksWithoutName = links.filter(el =>
            !!((el.getAttribute('href') || '').trim()) && !hasName(el)
        );
        const buttonsWithoutName = buttons.filter(el => {
            if (el instanceof HTMLInputElement) {
                return !((el.value || el.getAttribute('aria-label') ||
                    el.getAttribute('title') || '').trim());
            }
            return !hasName(el);
        });
        const inputsWithoutLabel = inputs.filter(el => {
            const id = el.id;
            const explicit = id && all('label[for]').some(label =>
                label.htmlFor === id && !!label.textContent.trim()
            );
            const wrapping = el.closest('label');
            const aria = (el.getAttribute('aria-label') || '').trim();
            const labelledBy = (el.getAttribute('aria-labelledby') || '')
                .split(/\\s+/).filter(Boolean)
                .some(labelId => {
                    const node = document.getElementById(labelId);
                    return !!node && !!node.textContent.trim();
                });
            return !explicit && !wrapping && !aria && !labelledBy;
        });

        return {
            navigation_count: all('nav, [role="navigation"]').length,
            form_count: all('form').length,
            card_count: all(
                'article, [class*="card" i], [class*="tile" i]'
            ).length,
            link_count: links.length,
            button_count: buttons.length,
            input_count: inputs.length,
            image_count: images.length,
            links_without_href: linksWithoutHref.length,
            links_without_name: linksWithoutName.length,
            buttons_without_name: buttonsWithoutName.length,
            inputs_without_label: inputsWithoutLabel.length,
            images_without_alt: images.filter(el =>
                !el.hasAttribute('alt')
            ).length
        };
    }""") 


def inspect_generic_uat(config, discovery_result, timeout_ms=30000):
    """Inspeksi DOM read-only pada halaman PASSED dari Website Discovery."""
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise ValueError("timeout_ms harus berupa bilangan bulat.")
    if timeout_ms < 1000:
        raise ValueError("timeout_ms minimal 1000 milidetik.")
    if discovery_result.project_id != config.project_id:
        raise ValueError("Project ID hasil Discovery tidak sesuai konfigurasi.")

    discovered_pages = [
        item for item in discovery_result.pages
        if item.status == ResultStatus.PASSED
    ]
    if not discovered_pages:
        return GenericUATResult(
            project_id=config.project_id,
            status=ResultStatus.NEEDS_REVIEW,
            pages=(),
            findings=(),
            completed=False,
            stopped_reason="Tidak ada halaman berstatus PASSED untuk diperiksa.",
            message="Generic UAT tidak dijalankan karena tidak ada halaman yang memenuhi syarat.",
        )

    controller = RequestSafetyController(
        config.max_requests_per_minute,
        config.stop_after_consecutive_403,
    )
    guard = PlaywrightRequestGuard(controller, config.base_url)
    screenshots_dir = Path(config.project_dir) / "evidence" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    page_results = []
    findings = []
    stopped_reason = ""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            service_workers="block",
            viewport={"width": 1365, "height": 768},
        )
        guard.install(context)
        page = context.new_page()
        try:
            for index, discovered in enumerate(discovered_pages, start=1):
                if controller.is_stopped:
                    stopped_reason = controller.stop_reason or (
                        "Inspeksi dihentikan oleh kontrol keamanan."
                    )
                    break

                if not guard.is_allowed_url(discovered.url):
                    page_results.append(UATPageResult(
                        page_url=discovered.url,
                        http_status=None,
                        status=ResultStatus.BLOCKED,
                        component_summary={},
                        screenshot_path=None,
                        message="URL tidak termasuk origin proyek.",
                    ))
                    continue

                http_status = None
                summary = {}
                screenshot_path = None
                status = ResultStatus.INCONCLUSIVE
                message = ""

                try:
                    response = page.goto(
                        discovered.url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                    if response is not None:
                        http_status = response.status

                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            "Inspeksi dihentikan oleh kontrol keamanan."
                        )
                    elif http_status in (401, 403):
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = f"Akses dibatasi (HTTP {http_status})."
                    elif http_status is not None and http_status >= 400:
                        status = ResultStatus.FAILED
                        message = f"Halaman merespons HTTP {http_status}."
                    elif response is None:
                        status = ResultStatus.INCONCLUSIVE
                        message = "Respons navigasi tidak dapat diverifikasi."
                    else:
                        summary = _inspect_dom(page)
                        findings.extend(_build_findings(discovered.url, summary))
                        status = ResultStatus.PASSED
                        message = "DOM berhasil diperiksa secara read-only."

                        screenshot_path = screenshots_dir / (
                            f"generic_uat_{timestamp}_{index:02d}.png"
                        )
                        try:
                            page.screenshot(
                                path=str(screenshot_path),
                                full_page=True,
                                timeout=10000,
                            )
                        except PlaywrightError:
                            screenshot_path = None

                except PlaywrightTimeoutError:
                    status = ResultStatus.TIMEOUT
                    message = "Waktu tunggu halaman habis."
                except PlaywrightError as error:
                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            "Inspeksi dihentikan demi keamanan."
                        )
                    else:
                        status = ResultStatus.BLOCKED
                        message = (
                            "Navigasi browser gagal "
                            f"({type(error).__name__})."
                        )

                page_results.append(UATPageResult(
                    page_url=discovered.url,
                    http_status=http_status,
                    status=status,
                    component_summary=summary,
                    screenshot_path=screenshot_path,
                    message=message,
                ))

                if status == ResultStatus.ACCESS_RESTRICTED:
                    stopped_reason = message
                    break
                if controller.is_stopped:
                    stopped_reason = controller.stop_reason or (
                        "Inspeksi dihentikan demi keamanan."
                    )
                    break
        finally:
            context.close()
            browser.close()

    if stopped_reason:
        overall = ResultStatus.ACCESS_RESTRICTED
        completed = False
        message = "Generic UAT dihentikan karena pembatasan akses atau keamanan."
    elif len(page_results) < len(discovered_pages):
        overall = ResultStatus.NEEDS_REVIEW
        completed = False
        message = "Sebagian halaman belum diperiksa."
    elif any(item.status != ResultStatus.PASSED for item in page_results):
        overall = ResultStatus.NEEDS_REVIEW
        completed = False
        message = "Inspeksi selesai, tetapi sebagian halaman perlu ditinjau."
    elif findings:
        overall = ResultStatus.NEEDS_REVIEW
        completed = True
        message = "Inspeksi selesai dan menemukan indikasi yang perlu ditinjau."
    else:
        overall = ResultStatus.PASSED
        completed = True
        message = "Inspeksi DOM selesai tanpa indikasi masalah pada pemeriksaan ini."

    return GenericUATResult(
        project_id=config.project_id,
        status=overall,
        pages=tuple(page_results),
        findings=tuple(findings),
        completed=completed,
        stopped_reason=stopped_reason,
        message=message,
    )
'@

Set-Content -Path .\modules\generic_uat_inspection.py -Value $Module -Encoding utf8

# ---------------------------------------------------------------------------
# 2. Unit dan integration test menggunakan HTTP server lokal
# ---------------------------------------------------------------------------
$Tests = @'
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from core.result_status import ResultStatus
from modules.frontend_scanner import ScannerConfig
from modules.generic_uat_inspection import (
    _build_findings,
    inspect_generic_uat,
)
from modules.website_discovery import (
    DiscoveredPage,
    WebsiteDiscoveryResult,
)


class TestGenericUATFindings(unittest.TestCase):
    def test_creates_review_findings_from_dom_snapshot(self):
        snapshot = {
            "links_without_href": 1,
            "links_without_name": 2,
            "buttons_without_name": 1,
            "inputs_without_label": 1,
            "images_without_alt": 1,
        }
        findings = _build_findings("https://example.test/", snapshot)
        self.assertEqual(len(findings), 6)
        self.assertTrue(all(
            item.status == ResultStatus.NEEDS_REVIEW for item in findings
        ))

    def test_empty_snapshot_has_no_findings(self):
        self.assertEqual(_build_findings("https://example.test/", {}), [])

    def test_invalid_counts_are_ignored(self):
        findings = _build_findings(
            "https://example.test/",
            {"links_without_href": -1, "buttons_without_name": True},
        )
        self.assertEqual(findings, [])


class TestGenericUATIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hits = {}
        cls.lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path).path
                with TestGenericUATIntegration.lock:
                    TestGenericUATIntegration.hits[path] = (
                        TestGenericUATIntegration.hits.get(path, 0) + 1
                    )

                if path == "/forbidden":
                    status = 403
                    body = "<title>Forbidden</title><h1>Forbidden</h1>"
                elif path == "/clean":
                    status = 200
                    body = (
                        "<title>Clean</title><nav><a href='/clean'>Home</a></nav>"
                        "<h1>Clean page</h1>"
                        "<img src='/pixel' alt='Small logo'>"
                        "<form><label for='email'>Email</label>"
                        "<input id='email' type='email'></form>"
                    )
                elif path == "/pixel":
                    status = 200
                    body = ""
                else:
                    status = 200
                    body = (
                        "<title>Review</title><h1>Review page</h1>"
                        "<a>Missing href</a>"
                        "<a href='/clean'></a>"
                        "<button></button>"
                        "<input type='text'>"
                        "<img src='/pixel'>"
                        "<img src='http://127.0.0.1:1/external' alt='external'>"
                    )

                self.send_response(status)
                if path == "/pixel":
                    self.send_header("Content-Type", "image/gif")
                    self.end_headers()
                    self.wfile.write(b"GIF89a")
                    return
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

            def log_message(self, fmt, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True
        )
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        with self.lock:
            self.hits.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp.name)
        self.config = ScannerConfig(
            project_id="GENERIC_UAT_TEST",
            project_name="Generic UAT Test",
            base_url=self.origin + "/",
            project_dir=self.project_dir,
            check_images=False,
            check_links=False,
            max_requests_per_minute=10,
            stop_after_consecutive_403=3,
        )

    def tearDown(self):
        self.temp.cleanup()

    def _discovery(self, path, status=ResultStatus.PASSED):
        url = self.origin + path
        discovered = DiscoveredPage(
            url=url,
            final_url=url,
            title="Test",
            http_status=200,
            status=status,
            page_type="unknown",
            component_counts={},
            internal_links=(),
            screenshot_path=None,
            message="Test fixture",
        )
        return WebsiteDiscoveryResult(
            project_id=self.config.project_id,
            start_url=self.config.base_url,
            status=ResultStatus.PASSED,
            pages=(discovered,),
            max_pages=20,
            completed=True,
            stopped_reason="",
            message="Test fixture",
        )

    def test_inspects_dom_and_creates_screenshot(self):
        result = inspect_generic_uat(self.config, self._discovery("/review"))
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)
        self.assertTrue(result.completed)
        self.assertGreaterEqual(len(result.findings), 5)
        self.assertEqual(result.pages[0].status, ResultStatus.PASSED)
        self.assertIsNotNone(result.pages[0].screenshot_path)
        self.assertTrue(result.pages[0].screenshot_path.exists())

    def test_clean_page_passes_without_findings(self):
        result = inspect_generic_uat(self.config, self._discovery("/clean"))
        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.findings, ())

    def test_403_stops_inspection(self):
        config = ScannerConfig(
            project_id=self.config.project_id,
            project_name=self.config.project_name,
            base_url=self.config.base_url,
            project_dir=self.project_dir,
            check_images=False,
            check_links=False,
            max_requests_per_minute=10,
            stop_after_consecutive_403=1,
        )
        result = inspect_generic_uat(config, self._discovery("/forbidden"))
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)
        self.assertIn("403", result.stopped_reason)

    def test_skips_pages_not_passed_by_discovery(self):
        result = inspect_generic_uat(
            self.config,
            self._discovery("/review", status=ResultStatus.FAILED),
        )
        self.assertEqual(result.status, ResultStatus.NEEDS_REVIEW)
        self.assertEqual(result.pages, ())
        self.assertEqual(self.hits, {})

    def test_rejects_discovery_from_another_project(self):
        discovery = self._discovery("/review")
        discovery = WebsiteDiscoveryResult(
            project_id="OTHER_PROJECT",
            start_url=discovery.start_url,
            status=discovery.status,
            pages=discovery.pages,
            max_pages=discovery.max_pages,
            completed=discovery.completed,
            stopped_reason=discovery.stopped_reason,
            message=discovery.message,
        )
        with self.assertRaises(ValueError):
            inspect_generic_uat(self.config, discovery)


if __name__ == "__main__":
    unittest.main()
'@

Set-Content -Path .\tests\test_generic_uat_inspection.py -Value $Tests -Encoding utf8

# ---------------------------------------------------------------------------
# 3. Integrasi agent.py dengan penggantian yang harus cocok tepat satu kali
# ---------------------------------------------------------------------------
$AgentPath = ".\agent.py"
$Agent = Get-Content $AgentPath -Raw
$Agent = $Agent -replace "`r`n", "`n"

$ImportPattern = '(?s)from modules\.frontend_scanner import \(\s*load_scanner_config,\s*inspect_homepage\s*\)'
$ImportReplacement = @'
from modules.frontend_scanner import (
    load_scanner_config,
    inspect_homepage
)
from modules.website_discovery import discover_website
from modules.generic_uat_inspection import inspect_generic_uat
'@
if ([regex]::Matches($Agent, $ImportPattern).Count -ne 1) {
    throw "Blok import frontend_scanner tidak ditemukan tepat satu kali; agent.py tidak ditulis."
}
$Agent = ([regex]::new($ImportPattern)).Replace($Agent, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $ImportReplacement }, 1)

$MenuPattern = '(?m)^([ \t]*)print\("4\. Jalankan Frontend Homepage Scanner"\)\n[ \t]*print\("5\. Keluar"\)'
$MenuReplacement = @'
    print("4. Jalankan Frontend Homepage Scanner")
    print("5. Jalankan Generic UAT Inspection")
    print("6. Keluar")
'@
if ([regex]::Matches($Agent, $MenuPattern).Count -ne 1) {
    throw "Blok menu utama tidak ditemukan tepat satu kali; agent.py tidak ditulis."
}
$Agent = ([regex]::new($MenuPattern)).Replace($Agent, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $MenuReplacement.TrimEnd() }, 1)

$MainPattern = '(?s)            elif choice == "5":\n                log_info\(\n                    "Menutup aplikasi",\n                    "Pengguna menutup AI QA Assistant secara normal\."\n                \)\n                print\("AI QA Assistant ditutup\."\)\n                break'
$MainReplacement = @'
            elif choice == "5":
                active_project_id = run_generic_uat_inspection(
                    active_project_id
                )

            elif choice == "6":
                log_info(
                    "Menutup aplikasi",
                    "Pengguna menutup AI QA Assistant secara normal."
                )
                print("AI QA Assistant ditutup.")
                break
'@
if ([regex]::Matches($Agent, $MainPattern).Count -ne 1) {
    throw "Blok pilihan keluar pada main() tidak ditemukan tepat satu kali; agent.py tidak ditulis."
}
$Agent = ([regex]::new($MainPattern)).Replace($Agent, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $MainReplacement.TrimEnd() }, 1)

$FunctionMarker = 'def project_manager_menu\(active_project_id\):'
$FunctionBody = @'
def run_generic_uat_inspection(active_project_id):
    print("\n================================")
    print("       GENERIC UAT INSPECTION")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        print("Silakan pilih proyek yang akan diperiksa.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nGeneric UAT tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)

        print("\nTahap 1/2: Website Discovery...")
        discovery = discover_website(config)
        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if not discovery.pages:
            print("Tidak ada halaman yang dapat diproses.")
            return active_project_id

        print("\nTahap 2/2: Generic UAT DOM Inspection...")
        result = inspect_generic_uat(config, discovery)

        print("\n================================")
        print("       HASIL GENERIC UAT")
        print("================================")
        print("Project ID :", result.project_id)
        print("Status     :", result.status.value)
        print("Halaman    :", len(result.pages))
        print("Temuan     :", len(result.findings))
        print("Selesai    :", result.completed)
        print("Pesan      :", result.message)

        for page_result in result.pages:
            print("\n- URL:", page_result.page_url)
            print("  HTTP:", page_result.http_status or "(tidak tersedia)")
            print("  Status:", page_result.status.value)
            print("  Komponen:", page_result.component_summary)
            if page_result.screenshot_path:
                print("  Evidence:", page_result.screenshot_path)

        if result.findings:
            print("\nINDIKASI UNTUK DITINJAU")
            for number, finding in enumerate(result.findings, start=1):
                print(f"{number}. [{finding.category}] {finding.element}")
                print("   URL   :", finding.page_url)
                print("   Detail:", finding.issue)
                print("   Status:", finding.status.value)

        log_info(
            "Generic UAT Inspection",
            (
                f"Inspeksi selesai. Project ID: {active_project_id}, "
                f"Status: {result.status.value}, "
                f"Halaman: {len(result.pages)}, "
                f"Temuan: {len(result.findings)}"
            )
        )

    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Generic UAT tidak dapat dijalankan.")
        print("Detail:", error)
        log_warning(
            "Generic UAT Inspection",
            "Konfigurasi proyek tidak memenuhi persyaratan inspeksi."
        )
    except Exception as error:
        print("\n[ERROR] Terjadi kesalahan saat Generic UAT.")
        print("Detail error dapat diperiksa di folder logs.")
        log_error(
            activity="Generic UAT Inspection",
            explanation="Inspeksi DOM mengalami kegagalan.",
            causes=[
                "Browser atau scanner mengalami kendala.",
                "Konfigurasi atau lingkungan aplikasi bermasalah."
            ],
            actions=[
                "Periksa folder logs.",
                "Pastikan instalasi Playwright dan Chromium tersedia."
            ]
        )

    return active_project_id


'@
if ([regex]::Matches($Agent, $FunctionMarker).Count -ne 1) {
    throw "Titik penyisipan fungsi Generic UAT tidak ditemukan tepat satu kali."
}
$Agent = ([regex]::new($FunctionMarker)).Replace($Agent, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $FunctionBody + $m.Value }, 1)

Set-Content -Path $AgentPath -Value $Agent -Encoding utf8

# ---------------------------------------------------------------------------
# 4. Dokumentasi: append section tanpa menghapus isi yang sudah ada
# ---------------------------------------------------------------------------
$ProjectDoc = ".\docs\PROJECT_SETUP_GUIDE.md"
$ProjectMarker = "## 18. Generic UAT Inspection"
if (-not (Select-String -Path $ProjectDoc -SimpleMatch $ProjectMarker -Quiet)) {
    Add-Content -Path $ProjectDoc -Encoding utf8 -Value @'

## 18. Generic UAT Inspection

Generic UAT Inspection adalah tahap inspeksi DOM read-only setelah Website Discovery.

Cakupan tahap awal:
- Memeriksa tautan tanpa tujuan atau accessible name.
- Memeriksa tombol tanpa accessible name.
- Memeriksa input tanpa label yang terdeteksi.
- Memeriksa gambar tanpa atribut alt.
- Merangkum navigasi, formulir, kartu, tautan, tombol, input, dan gambar.
- Menyimpan screenshot di `projects/<project_id>/evidence/screenshots`.

Batasan dan keamanan:
- Hanya halaman hasil Website Discovery dengan status `Passed` yang diperiksa.
- Project ID hasil Discovery harus sama dengan konfigurasi proyek.
- Request menggunakan `PlaywrightRequestGuard` dan `RequestSafetyController`.
- Request eksternal dan redirect di luar origin proyek diblokir oleh guard.
- Tidak ada klik tombol, pengiriman formulir, atau pembacaan nilai input.
- Batas request per menit dan penghentian setelah batas HTTP 403 tetap berlaku.
- Indikasi struktur/aksesibilitas menggunakan status `Needs Review`, bukan vonis bug fungsional.
- Tahap ini belum membuktikan alur bisnis atau perilaku interaktif.

Menu aplikasi:
- Pilihan 5: Generic UAT Inspection.
- Pilihan 6: Keluar.
'@
}

$PortableDoc = ".\docs\PORTABLE_SETUP_GUIDE.md"
$PortableMarker = "## Generic UAT Inspection"
if (-not (Select-String -Path $PortableDoc -SimpleMatch $PortableMarker -Quiet)) {
    Add-Content -Path $PortableDoc -Encoding utf8 -Value @'

## Generic UAT Inspection

Generic UAT merupakan tahap inspeksi DOM read-only setelah Website Discovery.
Modul baru berada di `modules/generic_uat_inspection.py` dan test-nya berada
di `tests/test_generic_uat_inspection.py`.

Tidak ada aksi klik atau submit formulir. Screenshot disimpan di folder evidence
masing-masing proyek. Seluruh request tetap menggunakan request guard dan
safety controller yang sudah ada. Temuan awal dicatat sebagai `Needs Review`
dan perlu validasi lanjutan sebelum disebut bug.
'@
}

# ---------------------------------------------------------------------------
# 5. Pemeriksaan sintaks, test fitur, regression suite, dan diff check
# ---------------------------------------------------------------------------
Write-Host "`n=== COMPILE CHECK ===" -ForegroundColor Cyan
& $Python -m py_compile .\agent.py .\modules\generic_uat_inspection.py .\tests\test_generic_uat_inspection.py
if ($LASTEXITCODE -ne 0) { throw "Compile check gagal. Backup tersedia di $Backup" }

Write-Host "`n=== GENERIC UAT TESTS ===" -ForegroundColor Cyan
& $Python -m unittest tests.test_generic_uat_inspection -v
if ($LASTEXITCODE -ne 0) { throw "Generic UAT tests gagal. Jangan commit. Backup tersedia di $Backup" }

Write-Host "`n=== FULL REGRESSION TESTS ===" -ForegroundColor Cyan
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Regression tests gagal. Jangan commit. Backup tersedia di $Backup" }

Write-Host "`n=== GIT DIFF CHECK ===" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup tersedia di $Backup" }

Write-Host "`nBatch implementation dan seluruh pemeriksaan berhasil." -ForegroundColor Green
Write-Host "Backup: $((Resolve-Path $Backup).Path)"
Write-Host "Belum ada commit atau push Git."
