import logging
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
from core.evidence_manager import register_evidence
from core.access_classification import (
    AccessClassification,
    classify_access_restriction,
)
from core.path_safety import resolve_project_path
from core.progress_tracking import (
    emit_progress, result_outcome_labels, terminal_status_for_results,
)


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
    access_classification: AccessClassification | None = None


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
            const imageAlt = [...el.querySelectorAll('img')]
                .some(img => (img.getAttribute('alt') || '').trim());
            return !!(aria || title || labelledBy || text || imageAlt);
        };

        const links = all('a').filter(visible);
        const buttons = all(
            'button, input[type="button"], input[type="submit"], [role="button"]'
        ).filter(visible);
        const inputs = all(
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="image"]), textarea, select, [contenteditable="true"]'
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
                return !((el.getAttribute('value') ||
                    el.getAttribute('aria-label') ||
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


def _register_screenshot_evidence(
    project_id, screenshot_path, page_url, title, metadata=None,
):
    try:
        register_evidence(
            project_id=project_id,
            file_path=screenshot_path,
            evidence_type="screenshot",
            source="generic_uat_inspection",
            page_url=page_url,
            title=title or "",
            metadata=metadata or {},
        )
        return True
    except Exception:
        logging.getLogger(__name__).warning(
            "Screenshot evidence registration failed; inspection continues."
        )
        return False


def inspect_generic_uat(
    config, discovery_result, timeout_ms=30000, controller=None, progress=None,
):
    emit_progress(progress, "Generic UAT", "waiting", "Menunggu Generic UAT.")
    emit_progress(progress, "Generic UAT", "running", "Menyiapkan halaman hasil Discovery.")
    try:
        result = _inspect_generic_uat_impl(
            config, discovery_result, timeout_ms=timeout_ms,
            controller=controller, progress=progress,
        )
    except Exception:
        emit_progress(progress, "Generic UAT", "failed", "Generic UAT gagal sebelum selesai.")
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
        progress, "Generic UAT", terminal,
        "Generic UAT selesai diproses; hasil QA: "
        f"{result.status.value}"
        f"{'; hasil halaman: ' + outcomes if outcomes else ''}; "
        f"halaman diperiksa: {len(result.pages)}.",
        len(result.pages), total_pages,
    )
    return result


def _inspect_generic_uat_impl(
    config, discovery_result, timeout_ms=30000, controller=None, progress=None,
):
    """Inspeksi DOM read-only pada halaman PASSED dari Website Discovery."""
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise ValueError("timeout_ms harus berupa bilangan bulat.")
    if timeout_ms < 1000:
        raise ValueError("timeout_ms minimal 1000 milidetik.")
    if discovery_result.project_id != config.project_id:
        raise ValueError("Project ID hasil Discovery tidak sesuai konfigurasi.")

    if discovery_result.status == ResultStatus.ACCESS_RESTRICTED:
        reason = (
            discovery_result.stopped_reason
            or "Website Discovery berstatus Access Restricted."
        )
        return GenericUATResult(
            project_id=config.project_id,
            status=ResultStatus.ACCESS_RESTRICTED,
            pages=(),
            findings=(),
            completed=False,
            stopped_reason=reason,
            message=(
                "Generic UAT tidak dijalankan karena Website Discovery "
                "mengalami pembatasan akses."
            ),
        )

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

    controller = controller or RequestSafetyController(
        config.max_requests_per_minute,
        config.stop_after_consecutive_403,
    )
    guard = PlaywrightRequestGuard(controller, config.base_url)
    screenshots_dir = resolve_project_path(config.project_dir, "evidence", "screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir = resolve_project_path(config.project_dir, "evidence", "screenshots")
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
                emit_progress(
                    progress, "Generic UAT", "running",
                    "Memeriksa halaman hasil Discovery.",
                    index, len(discovered_pages),
                )
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

                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or (
                            "Inspeksi dihentikan oleh kontrol keamanan."
                        )
                    elif access_classification.restricted:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = (
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
                        if screenshot_path is not None:
                            _register_screenshot_evidence(
                                config.project_id,
                                screenshot_path,
                                discovered.url,
                                discovered.title,
                                {"inspection": "generic_uat"},
                            )

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
                    access_classification=access_classification,
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
