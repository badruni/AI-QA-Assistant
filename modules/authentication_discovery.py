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
from core.access_classification import (
    AccessClassification,
    classify_access_restriction,
)
from core.progress_tracking import (
    emit_progress, result_outcome_labels, terminal_status_for_results,
)


@dataclass(frozen=True)
class AuthenticationPageResult:
    page_url: str
    http_status: int | None
    status: ResultStatus
    signals: dict
    message: str
    access_classification: AccessClassification | None = None


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


def inspect_authentication(
    config, discovery_result, timeout_ms=30000, controller=None, progress=None,
):
    emit_progress(
        progress, "Authentication Discovery", "waiting",
        "Menunggu Authentication Discovery.",
    )
    emit_progress(
        progress, "Authentication Discovery", "running",
        "Menyiapkan halaman PASSED; deteksi bersifat read-only.",
    )
    try:
        result = _inspect_authentication_impl(
            config, discovery_result, timeout_ms=timeout_ms,
            controller=controller, progress=progress,
        )
    except Exception:
        emit_progress(
            progress, "Authentication Discovery", "failed",
            "Authentication Discovery gagal sebelum selesai.",
        )
        raise

    terminal = terminal_status_for_results(
        [result.status, *(item.status for item in result.pages)]
    )
    outcomes = result_outcome_labels(
        [result.status, *(item.status for item in result.pages)]
    )
    total_pages = (
        0 if discovery_result.status == ResultStatus.ACCESS_RESTRICTED else
        sum(item.status == ResultStatus.PASSED for item in discovery_result.pages)
    )
    emit_progress(
        progress, "Authentication Discovery", terminal,
        "Authentication Discovery (pemeriksaan read-only) selesai diproses; hasil QA: "
        f"{result.status.value}"
        f"{'; hasil halaman: ' + outcomes if outcomes else ''}; "
        f"klasifikasi: {result.classification}; "
        f"halaman diperiksa: {len(result.pages)}.",
        len(result.pages), total_pages,
    )
    return result


def _inspect_authentication_impl(
    config, discovery_result, timeout_ms=30000, controller=None, progress=None,
):
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

    controller = controller or RequestSafetyController(
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
                emit_progress(
                    progress, "Authentication Discovery", "running",
                    "Memeriksa sinyal autentikasi tanpa interaksi login.",
                    len(results) + 1, len(candidates),
                )
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
                access_classification = AccessClassification(False, "NONE")
                try:
                    response = page.goto(
                        discovered.url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                    if response is not None:
                        http_status = response.status

                    try:
                        title = page.title()
                        body_text = page.locator("body").inner_text(timeout=3000)
                    except PlaywrightError:
                        title, body_text = "", ""
                    access_classification = classify_access_restriction(
                        http_status, title, body_text
                    )

                    if controller.is_stopped or access_classification.restricted:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            "Akses dibatasi; klasifikasi: "
                            f"{access_classification.classification}."
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
                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            "Inspeksi dihentikan demi keamanan."
                        )
                    else:
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
                    discovered.url, http_status, status, signals, message,
                    access_classification,
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
            guard.begin_shutdown()
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
