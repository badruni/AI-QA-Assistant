[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "=== AI QA Assistant: Authentication Discovery Batch ===" -ForegroundColor Cyan

$ProjectRoot = (Get-Location).Path
$RequiredFiles = @(
    "agent.py",
    "modules\website_discovery.py",
    "modules\generic_uat_inspection.py",
    "core\playwright_request_guard.py",
    "core\request_safety.py",
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md",
    "requirements.txt"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path (Join-Path $ProjectRoot $File))) {
        throw "File wajib tidak ditemukan: $File. Jalankan script dari root proyek."
    }
}

$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "backups\before_authentication_discovery_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$BackupFiles = @(
    "agent.py",
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $BackupFiles) {
    $Destination = Join-Path $BackupDir $File
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item (Join-Path $ProjectRoot $File) $Destination
}

foreach ($Directory in @("modules", "tests")) {
    $Target = Join-Path $BackupDir $Directory
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}
if (Test-Path (Join-Path $ProjectRoot "modules\authentication_discovery.py")) {
    Copy-Item (Join-Path $ProjectRoot "modules\authentication_discovery.py") (Join-Path $BackupDir "modules\authentication_discovery.py")
}
if (Test-Path (Join-Path $ProjectRoot "tests\test_authentication_discovery.py")) {
    Copy-Item (Join-Path $ProjectRoot "tests\test_authentication_discovery.py") (Join-Path $BackupDir "tests\test_authentication_discovery.py")
}

Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$Module = @'
from dataclasses import dataclass
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
class AuthenticationPageResult:
    page_url: str
    http_status: int | None
    status: ResultStatus
    signals: dict
    message: str


@dataclass(frozen=True)
class AuthenticationDiscoveryResult:
    project_id: str
    status: ResultStatus
    classification: str
    confidence: str
    pages: tuple
    completed: bool
    stopped_reason: str
    message: str


def _classify_auth_signals(snapshot):
    """Klasifikasi indikasi autentikasi; bukan bukti seluruh sistem auth."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot harus berupa dictionary.")

    password_fields = max(0, int(snapshot.get("password_fields", 0) or 0))
    otp_fields = max(0, int(snapshot.get("otp_fields", 0) or 0))
    login_forms = max(0, int(snapshot.get("login_forms", 0) or 0))
    login_text = bool(snapshot.get("login_text"))
    auth_url = bool(snapshot.get("auth_url"))
    social_login = tuple(snapshot.get("social_login", ()) or ())
    sso_hints = tuple(snapshot.get("sso_hints", ()) or ())

    if password_fields or otp_fields or login_forms or social_login or sso_hints:
        return "LOGIN_DETECTED", "HIGH"
    if login_text or auth_url:
        return "LOGIN_DETECTED", "MEDIUM"
    return "NO_LOGIN_DETECTED", "LOW"


def _inspect_auth_dom(page):
    """Ambil sinyal DOM tanpa membaca nilai field, klik, atau submit."""
    return page.evaluate("""() => {
        const visible = el =>
            !!el.getClientRects().length &&
            getComputedStyle(el).visibility !== 'hidden' &&
            getComputedStyle(el).display !== 'none';
        const fields = [...document.querySelectorAll(
            'input, textarea, select, [contenteditable="true"]'
        )].filter(visible);

        const hint = el => [
            el.getAttribute('type'), el.getAttribute('name'),
            el.getAttribute('id'), el.getAttribute('autocomplete'),
            el.getAttribute('placeholder'), el.getAttribute('aria-label')
        ].filter(Boolean).join(' ').toLowerCase();

        const passwordFields = fields.filter(el =>
            (el.getAttribute('type') || '').toLowerCase() === 'password'
        ).length;
        const otpFields = fields.filter(el => {
            const value = hint(el);
            return /one-time-code|otp|verification.?code|security.?code/.test(value);
        }).length;
        const loginForms = [...document.querySelectorAll('form')].filter(form => {
            const formFields = [...form.querySelectorAll('input')];
            return formFields.some(el =>
                (el.getAttribute('type') || '').toLowerCase() === 'password'
            ) || /login|log-in|sign.?in|masuk|autentikasi/.test(
                [
                    form.getAttribute('action'), form.getAttribute('id'),
                    form.getAttribute('class'), form.getAttribute('aria-label')
                ].filter(Boolean).join(' ').toLowerCase()
            );
        }).length;

        const bodyText = (document.body?.innerText || '').toLowerCase();
        const loginText = /\b(log ?in|sign ?in|masuk|masuk akun|akun saya)\b/.test(bodyText);
        const authUrl = /login|log-in|signin|sign-in|auth|account|masuk/i.test(
            location.pathname
        );

        const controls = [...document.querySelectorAll(
            'a, button, [role="button"]'
        )].filter(visible);
        const controlHints = controls.map(el => [
            el.innerText, el.getAttribute('aria-label'),
            el.getAttribute('title'), el.getAttribute('href')
        ].filter(Boolean).join(' ').toLowerCase());

        const socialLogin = [...new Set(
            ['google', 'facebook', 'apple', 'microsoft', 'linkedin']
                .filter(provider => controlHints.some(value =>
                    value.includes(provider) && /sign|log|continue|masuk|auth/.test(value)
                ))
        )];
        const ssoHints = [...new Set(
            ['sso', 'single sign-on', 'saml', 'openid', 'corporate login']
                .filter(term => bodyText.includes(term) ||
                    controlHints.some(value => value.includes(term)))
        )];

        return {
            password_fields: passwordFields,
            otp_fields: otpFields,
            login_forms: loginForms,
            login_text: loginText,
            auth_url: authUrl,
            social_login: socialLogin,
            sso_hints: ssoHints
        };
    }""")


def inspect_authentication(config, discovery_result, timeout_ms=30000):
    """Deteksi indikasi login secara read-only pada halaman Discovery PASSED."""
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise ValueError("timeout_ms harus berupa bilangan bulat.")
    if timeout_ms < 1000:
        raise ValueError("timeout_ms minimal 1000 milidetik.")
    if discovery_result.project_id != config.project_id:
        raise ValueError("Project ID hasil Discovery tidak sesuai konfigurasi.")

    if discovery_result.status == ResultStatus.ACCESS_RESTRICTED:
        reason = discovery_result.stopped_reason or (
            "Website Discovery berstatus Access Restricted."
        )
        return AuthenticationDiscoveryResult(
            project_id=config.project_id,
            status=ResultStatus.ACCESS_RESTRICTED,
            classification="NEEDS_REVIEW",
            confidence="NONE",
            pages=(),
            completed=False,
            stopped_reason=reason,
            message="Authentication Discovery dilewati karena akses dibatasi.",
        )

    candidates = [
        item for item in discovery_result.pages
        if item.status == ResultStatus.PASSED
    ]
    if not candidates:
        return AuthenticationDiscoveryResult(
            project_id=config.project_id,
            status=ResultStatus.NEEDS_REVIEW,
            classification="NEEDS_REVIEW",
            confidence="NONE",
            pages=(),
            completed=False,
            stopped_reason="Tidak ada halaman PASSED dari Website Discovery.",
            message="Tidak ada halaman yang memenuhi syarat untuk diperiksa.",
        )

    controller = RequestSafetyController(
        config.max_requests_per_minute,
        config.stop_after_consecutive_403,
    )
    guard = PlaywrightRequestGuard(controller, config.base_url)
    results = []
    detected = []
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
            for discovered in candidates:
                if controller.is_stopped:
                    stopped_reason = controller.stop_reason or (
                        "Inspeksi dihentikan oleh kontrol keamanan."
                    )
                    break
                if not guard.is_allowed_url(discovered.url):
                    results.append(AuthenticationPageResult(
                        discovered.url, None, ResultStatus.BLOCKED, {},
                        "URL tidak termasuk origin proyek."
                    ))
                    continue

                http_status = None
                status = ResultStatus.INCONCLUSIVE
                signals = {}
                message = ""
                try:
                    response = page.goto(
                        discovered.url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                    if response is not None:
                        http_status = response.status

                    if controller.is_stopped or http_status in (401, 403):
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            f"Akses dibatasi (HTTP {http_status})."
                        )
                    elif http_status is not None and http_status >= 400:
                        status = ResultStatus.FAILED
                        message = f"Halaman merespons HTTP {http_status}."
                    elif response is None:
                        status = ResultStatus.INCONCLUSIVE
                        message = "Respons navigasi tidak dapat diverifikasi."
                    else:
                        signals = _inspect_auth_dom(page)
                        classification, confidence = _classify_auth_signals(signals)
                        if classification == "LOGIN_DETECTED":
                            detected.append((classification, confidence))
                        status = ResultStatus.PASSED
                        message = "Sinyal autentikasi diperiksa secara read-only."
                except PlaywrightTimeoutError:
                    status = ResultStatus.TIMEOUT
                    message = "Waktu tunggu halaman habis."
                except PlaywrightError as error:
                    status = (
                        ResultStatus.ACCESS_RESTRICTED
                        if controller.is_stopped else ResultStatus.BLOCKED
                    )
                    message = controller.stop_reason or (
                        f"Navigasi browser gagal ({type(error).__name__})."
                    )

                results.append(AuthenticationPageResult(
                    discovered.url, http_status, status, signals, message
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
        classification, confidence = "NEEDS_REVIEW", "NONE"
        completed = False
        message = "Authentication Discovery dihentikan karena pembatasan akses."
    elif len(results) < len(candidates) or any(
        item.status != ResultStatus.PASSED for item in results
    ):
        overall = ResultStatus.NEEDS_REVIEW
        classification, confidence = "NEEDS_REVIEW", "NONE"
        completed = False
        message = "Sebagian halaman belum dapat diperiksa secara tuntas."
    elif detected:
        overall = ResultStatus.PASSED
        classification = "LOGIN_DETECTED"
        confidence = "HIGH" if any(item[1] == "HIGH" for item in detected) else "MEDIUM"
        completed = True
        message = "Ditemukan indikasi autentikasi pada halaman yang diperiksa."
    else:
        overall = ResultStatus.NEEDS_REVIEW
        classification = "NO_LOGIN_DETECTED"
        confidence = "LOW"
        completed = True
        message = (
            "Tidak ditemukan indikasi login pada halaman yang diperiksa; "
            "ini bukan bukti bahwa website tidak memiliki autentikasi."
        )

    return AuthenticationDiscoveryResult(
        project_id=config.project_id,
        status=overall,
        classification=classification,
        confidence=confidence,
        pages=tuple(results),
        completed=completed,
        stopped_reason=stopped_reason,
        message=message,
    )
'@

$Tests = @'
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.result_status import ResultStatus
from modules.authentication_discovery import (
    _classify_auth_signals,
    inspect_authentication,
)


class AuthenticationClassificationTests(unittest.TestCase):
    def test_password_field_detects_login_with_high_confidence(self):
        result = _classify_auth_signals({"password_fields": 1})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_otp_field_detects_login(self):
        result = _classify_auth_signals({"otp_fields": 1})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_social_login_is_reported(self):
        result = _classify_auth_signals({"social_login": ["google"]})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_sso_hint_is_reported(self):
        result = _classify_auth_signals({"sso_hints": ["saml"]})
        self.assertEqual(result, ("LOGIN_DETECTED", "HIGH"))

    def test_login_text_is_medium_confidence(self):
        result = _classify_auth_signals({"login_text": True})
        self.assertEqual(result, ("LOGIN_DETECTED", "MEDIUM"))

    def test_no_signal_is_low_confidence(self):
        result = _classify_auth_signals({})
        self.assertEqual(result, ("NO_LOGIN_DETECTED", "LOW"))

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            _classify_auth_signals(None)


class AuthenticationSafetyTests(unittest.TestCase):
    def test_restricted_discovery_does_not_launch_browser(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            project_id="001",
            status=ResultStatus.ACCESS_RESTRICTED,
            stopped_reason="HTTP 403",
            pages=(),
        )
        with patch("modules.authentication_discovery.sync_playwright") as browser:
            result = inspect_authentication(config, discovery)
        browser.assert_not_called()
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertEqual(result.classification, "NEEDS_REVIEW")
        self.assertFalse(result.completed)

    def test_project_id_mismatch_is_rejected(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            project_id="002",
            status=ResultStatus.PASSED,
            stopped_reason="",
            pages=(),
        )
        with self.assertRaises(ValueError):
            inspect_authentication(config, discovery)


if __name__ == "__main__":
    unittest.main()
'@

$AgentPath = Join-Path $ProjectRoot "agent.py"
$Agent = [System.IO.File]::ReadAllText($AgentPath, [System.Text.Encoding]::UTF8)

if ($Agent -notmatch "from modules\.authentication_discovery import inspect_authentication") {
    $Agent = [regex]::Replace(
        $Agent,
        '(?m)^from modules\.generic_uat_inspection import inspect_generic_uat\r?$',
        'from modules.generic_uat_inspection import inspect_generic_uat' + "`r`n" +
        'from modules.authentication_discovery import inspect_authentication',
        1
    )
}
if ($Agent -notmatch "from core\.result_status import ResultStatus") {
    $Agent = [regex]::Replace(
        $Agent,
        '(?m)^from core\.logger import \($',
        'from core.result_status import ResultStatus' + "`r`n`r`n" +
        'from core.logger import (',
        1
    )
}
if ($Agent -notmatch "def run_authentication_discovery") {
    $Function = @'

def run_authentication_discovery(active_project_id):
    print("\n================================")
    print("       AUTHENTICATION DISCOVERY")
    print("================================")

    if not active_project_id:
        print("\nBelum ada proyek aktif.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\nAuthentication Discovery tidak dijalankan.")
            return None

    try:
        config = load_scanner_config(active_project_id)
        print("\nTahap 1/2: Website Discovery...")
        discovery = discover_website(config)
        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if discovery.status == ResultStatus.ACCESS_RESTRICTED:
            print("\nAuthentication Discovery dihentikan karena akses dibatasi.")
            log_warning(
                "Authentication Discovery",
                "Tahap dilewati karena Website Discovery berstatus Access Restricted."
            )
            return active_project_id

        print("\nTahap 2/2: Deteksi indikasi autentikasi (read-only)...")
        result = inspect_authentication(config, discovery)
        print("\n================================")
        print("       HASIL AUTHENTICATION DISCOVERY")
        print("================================")
        print("Project ID    :", result.project_id)
        print("Status        :", result.status.value)
        print("Klasifikasi   :", result.classification)
        print("Confidence    :", result.confidence)
        print("Halaman       :", len(result.pages))
        print("Selesai       :", result.completed)
        print("Pesan         :", result.message)

        for item in result.pages:
            print("\n- URL:", item.page_url)
            print("  HTTP:", item.http_status or "(tidak tersedia)")
            print("  Status:", item.status.value)
            if item.signals:
                print("  Indikasi:", item.signals)
            print("  Catatan:", item.message)

        log_info(
            "Authentication Discovery",
            (
                f"Project ID: {active_project_id}, "
                f"Classification: {result.classification}, "
                f"Status: {result.status.value}, Pages: {len(result.pages)}"
            )
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print("\n[ERROR] Authentication Discovery tidak dapat dijalankan.")
        print("Detail:", error)
        log_warning(
            "Authentication Discovery",
            "Konfigurasi proyek tidak memenuhi persyaratan."
        )
    except Exception as error:
        print("\n[ERROR] Terjadi kendala saat Authentication Discovery.")
        print("Detail error dapat diperiksa di folder logs.")
        log_exception(
            "Authentication Discovery",
            error,
            "Pemeriksaan indikasi autentikasi mengalami kendala."
        )

    return active_project_id

'@
    $Anchor = "def run_generic_uat_inspection(active_project_id):"
    if (-not $Agent.Contains($Anchor)) { throw "Anchor fungsi Generic UAT tidak ditemukan; perubahan dibatalkan." }
    $Agent = $Agent.Replace($Anchor, $Function + $Anchor)
}

if ($Agent -notmatch '6\\. Jalankan Authentication Discovery') {
    $Agent = [regex]::Replace(
        $Agent,
        '(?m)^    print\("6\. Keluar"\)$',
        '    print("6. Jalankan Authentication Discovery")' + "`r`n" +
        '    print("7. Keluar")',
        1
    )
}
if ($Agent -notmatch 'choice == "7"') {
    $Agent = [regex]::Replace(
        $Agent,
        '(?m)^            elif choice == "6":\r?\n(?=                log_info\()',
        '            elif choice == "6":' + "`r`n" +
        '                active_project_id = run_authentication_discovery(active_project_id)' +
        "`r`n`r`n" + '            elif choice == "7":' + "`r`n",
        1
    )
}

if ($Agent -notmatch 'choice == "7"') {
    throw "Integrasi menu tidak berhasil diverifikasi. Backup tersedia di $BackupDir"
}

$DocsUpdates = @{
    "docs\PROJECT_SETUP_GUIDE.md" = @'

## Authentication Discovery

2026-11-17:
- Menambahkan deteksi indikasi autentikasi secara read-only.
- Pemeriksaan hanya dilakukan pada halaman Website Discovery berstatus PASSED.
- Sinyal yang diamati meliputi password field, OTP hints, pola form login,
  petunjuk social login, SSO, teks login, dan URL autentikasi.
- Tidak mengisi field, mencoba kredensial, klik tombol login, atau submit form.
- Tidak membaca nilai input, password, token, cookie, maupun session.
- `LOGIN_DETECTED` berarti ada indikasi pada DOM yang diamati, bukan verifikasi
  bahwa seluruh mekanisme autentikasi telah ditemukan.
- `NO_LOGIN_DETECTED` ber-confidence LOW dan bukan bukti bahwa website tidak
  memiliki halaman/member authentication.
- Jika tidak ada halaman yang dapat diperiksa atau akses dibatasi, hasilnya
  `NEEDS_REVIEW` atau `ACCESS_RESTRICTED`.
'@
    "docs\PORTABLE_SETUP_GUIDE.md" = @'

## Authentication Discovery

2026-11-17:
- Modul `modules/authentication_discovery.py` menambahkan deteksi indikasi login
  secara read-only.
- Pemeriksaan tidak melakukan login, mengisi kredensial, klik, atau submit.
- Nilai password, OTP, token, cookie, dan session tidak dibaca atau disimpan.
- `NO_LOGIN_DETECTED` memiliki confidence LOW dan tidak membuktikan ketiadaan
  fitur autentikasi.
- Jalankan regression test dengan:
  `.\.venv-scanner\Scripts\python.exe -m unittest tests.test_authentication_discovery -v`
'@
}

[System.IO.File]::WriteAllText(
    (Join-Path $ProjectRoot "modules\authentication_discovery.py"),
    $Module,
    [System.Text.UTF8Encoding]::new($false)
)
New-Item -ItemType Directory -Path (Join-Path $ProjectRoot "tests") -Force | Out-Null
[System.IO.File]::WriteAllText(
    (Join-Path $ProjectRoot "tests\test_authentication_discovery.py"),
    $Tests,
    [System.Text.UTF8Encoding]::new($false)
)
[System.IO.File]::WriteAllText(
    $AgentPath, $Agent, [System.Text.UTF8Encoding]::new($false)
)

foreach ($Entry in $DocsUpdates.GetEnumerator()) {
    $Path = Join-Path $ProjectRoot $Entry.Key
    $Current = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    if ($Current -notmatch "## Authentication Discovery") {
        [System.IO.File]::AppendAllText(
            $Path,
            "`r`n" + $Entry.Value + "`r`n",
            [System.Text.UTF8Encoding]::new($false)
        )
    }
}

Write-Host "`nPerubahan batch diterapkan." -ForegroundColor Green
Write-Host "Menjalankan compile check..." -ForegroundColor Cyan
& $Python -m py_compile agent.py modules\authentication_discovery.py tests\test_authentication_discovery.py
if ($LASTEXITCODE -ne 0) { throw "Compile check gagal. Jangan lanjut sebelum diagnosis." }

Write-Host "`nMenjalankan focused tests..." -ForegroundColor Cyan
& $Python -m unittest tests.test_authentication_discovery -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Backup tersedia di $BackupDir" }

Write-Host "`nMemeriksa whitespace diff..." -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup tersedia di $BackupDir" }

Write-Host "`n=== BATCH SELESAI: MENUNGGU VERIFIKASI PENGGUNA ===" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "File baru: modules\authentication_discovery.py, tests\test_authentication_discovery.py"
Write-Host "Belum ada commit atau push."
