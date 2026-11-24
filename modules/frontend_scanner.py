import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.sync_api import (
    sync_playwright,
)

from core.access_classification import (
    AccessClassification,
    classify_access_restriction,
)
from core.evidence_manager import list_evidence, register_evidence, verify_evidence
from core.path_safety import resolve_project_directory, resolve_project_path
from core.playwright_request_guard import PlaywrightRequestGuard
from core.project_manager import get_project, validate_project_id, validate_url
from core.request_safety import (
    RequestSafetyController,
    RequestSafetyStop,
)
from core.result_status import ResultStatus
from core.security import has_sensitive_url_query, sanitize_text, sanitize_url

from core.data_paths import PROJECTS_DIR


def _emit_progress(progress, stage, status, activity, current=None, total=None):
    if progress is not None:
        progress.emit(stage, status, activity, current=current, total=total)


def _register_screenshot_evidence(
    project_id,
    screenshot_path,
    page_url,
    title,
    metadata=None,
):
    """Register a created screenshot; registry failure must not fail inspection."""
    try:
        register_evidence(
            project_id=project_id,
            file_path=screenshot_path,
            evidence_type="screenshot",
            source="frontend_scanner",
            page_url=page_url,
            title=title or "",
            metadata=metadata or {},
        )
        return True
    except Exception as error:
        logging.getLogger(__name__).warning(
            "Screenshot evidence registration failed; inspection continues. "
            "error_type=%s",
            type(error).__name__,
        )
        return False


def _looks_like_waf_block_page(page_title, page_text):
    """Mendeteksi indikator kuat halaman blokir WAF."""
    return classify_access_restriction(title=page_title, body_text=page_text).restricted


@dataclass(frozen=True)
class ScannerConfig:
    project_id: str
    project_name: str
    base_url: str
    project_dir: Path
    check_images: bool
    check_links: bool
    max_requests_per_minute: int
    stop_after_consecutive_403: int


@dataclass(frozen=True)
class HomepageInspectionResult:
    project_id: str
    requested_url: str
    final_url: str
    status: ResultStatus
    http_status: int | None
    page_title: str
    screenshot_path: Path | None
    message: str
    http_status_text: str = ""
    response_preview: str = ""
    access_classification: AccessClassification | None = None


@dataclass(frozen=True)
class ImageInspectionResult:
    image_url: str
    http_status: int | None
    status: ResultStatus
    message: str


@dataclass(frozen=True)
class LinkInspectionResult:
    link_url: str
    link_text: str
    link_type: str
    http_status: int | None
    status: ResultStatus
    message: str


@dataclass(frozen=True)
class FrontendQAWorkflowResult:
    """Project-scoped result for one coordinated frontend QA cycle."""

    project_id: str
    status: ResultStatus
    homepage: HomepageInspectionResult
    image_results: tuple[ImageInspectionResult, ...]
    link_results: tuple[LinkInspectionResult, ...]
    image_status: ResultStatus | None
    link_status: ResultStatus | None
    image_message: str
    link_message: str
    stopped_reason: str = ""
    evidence_ids: tuple[str, ...] = ()


def _classify_link(href, base_url):
    """Mengklasifikasikan tautan tanpa mengirim HTTP request."""

    href = (href or "").strip()

    if not href:
        return "special", ""

    if href.startswith("#"):
        return "anchor", href

    try:
        raw_target = urlsplit(href)

        if raw_target.scheme and raw_target.scheme.lower() not in (
            "http",
            "https",
        ):
            return "special", href

        if raw_target.scheme.lower() in ("http", "https"):
            if not raw_target.hostname:
                return "special", href

        target = urlsplit(urljoin(base_url, href))
        base = urlsplit(base_url)

        if not target.hostname:
            return "special", href

        if target.scheme.lower() not in ("http", "https"):
            return "special", href

        if not target.hostname or target.username or target.password:
            return "special", href

        base_origin = (
            base.scheme.lower(),
            (base.hostname or "").lower(),
            base.port or (443 if base.scheme.lower() == "https" else 80),
        )

        target_origin = (
            target.scheme.lower(),
            target.hostname.lower(),
            target.port or (443 if target.scheme.lower() == "https" else 80),
        )

        normalized_url = urlunsplit(
            (
                target.scheme.lower(),
                target.netloc,
                target.path or "/",
                target.query,
                "",
            )
        )

        if has_sensitive_url_query(normalized_url):
            return "sensitive", sanitize_url(normalized_url)

        if target_origin == base_origin:
            return "internal", normalized_url

        return "external", normalized_url

    except (TypeError, ValueError):
        return "special", href


def _extract_page_links(page):
    """Mengambil URL dan teks dari seluruh elemen anchor halaman."""

    return page.locator("a[href]").evaluate_all(
        """elements => elements.map(link => ({
            href: link.getAttribute("href"),
            text: (link.innerText || link.getAttribute("aria-label") || "")
                .trim()
        }))"""
    )


def load_scanner_config(project_id):
    """Membaca dan memvalidasi konfigurasi frontend scanner."""

    validate_project_id(project_id)
    project = get_project(project_id)

    if not isinstance(project, dict):
        raise ValueError("Format konfigurasi proyek tidak valid.")

    scan = project.get("scan")

    if not isinstance(scan, dict):
        raise ValueError("Konfigurasi scanner tidak tersedia.")

    if scan.get("frontend_enabled") is not True:
        raise ValueError("Frontend scanner tidak diaktifkan.")

    base_url = validate_url(project.get("base_url"))

    check_images = scan.get("check_images")
    check_links = scan.get("check_links")

    if not isinstance(check_images, bool):
        raise ValueError("Pengaturan check_images harus berupa boolean.")

    if not isinstance(check_links, bool):
        raise ValueError("Pengaturan check_links harus berupa boolean.")

    max_requests = scan.get("max_requests_per_minute")
    stop_after_403 = scan.get("stop_after_consecutive_403")

    if (
        isinstance(max_requests, bool)
        or not isinstance(max_requests, int)
        or not 1 <= max_requests <= 10
    ):
        raise ValueError("Batas request harus berupa angka antara 1 dan 10 per menit.")

    if (
        isinstance(stop_after_403, bool)
        or not isinstance(stop_after_403, int)
        or stop_after_403 < 1
    ):
        raise ValueError("Batas penghentian 403 harus berupa bilangan bulat positif.")

    project_dir = resolve_project_directory(PROJECTS_DIR, project_id)

    return ScannerConfig(
        project_id=project_id,
        project_name=project.get("project_name", ""),
        base_url=base_url,
        project_dir=project_dir,
        check_images=check_images,
        check_links=check_links,
        max_requests_per_minute=max_requests,
        stop_after_consecutive_403=stop_after_403,
    )


def inspect_images(config, timeout_ms=30000, controller=None, progress=None):
    """Memeriksa gambar pada homepage tanpa melewati request guard."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = controller or RequestSafetyController(
        max_requests_per_minute=config.max_requests_per_minute,
        stop_after_consecutive_403=config.stop_after_consecutive_403,
    )

    guard = PlaywrightRequestGuard(
        controller=controller,
        base_url=config.base_url,
    )

    image_responses = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
                service_workers="block",
                viewport={"width": 1365, "height": 768},
            )

            try:
                guard.install(context)
                page = context.new_page()

                def record_image_response(response):
                    if response.request.resource_type == "image":
                        image_responses[response.url] = response.status

                page.on("response", record_image_response)

                try:
                    page.goto(
                        config.base_url,
                        wait_until="load",
                        timeout=timeout_ms,
                    )
                except PlaywrightError:
                    if not controller.is_stopped:
                        raise
                    images = []
                else:
                    images = page.locator("img").evaluate_all(
                        """elements => elements.map(image => ({
                            url: image.currentSrc || image.src,
                            currentSrc: image.currentSrc,
                            complete: image.complete,
                            naturalWidth: image.naturalWidth,
                            naturalHeight: image.naturalHeight,
                            loading: image.loading
                        }))"""
                    )

            finally:
                guard.begin_shutdown()
                context.close()

        finally:
            browser.close()

    results = []
    seen_urls = set()
    total = len(images)

    for index, image in enumerate(images, start=1):
        image_url = image["url"]

        if not image_url:
            _emit_progress(
                progress,
                "Image Inspection",
                "running",
                "Elemen gambar tanpa URL dilewati.",
                index,
                total,
            )
            continue

        if image_url in seen_urls:
            _emit_progress(
                progress,
                "Image Inspection",
                "running",
                "URL gambar duplikat dilewati.",
                index,
                total,
            )
            continue

        seen_urls.add(image_url)

        if not guard.is_allowed_url(image_url):
            result = ImageInspectionResult(
                image_url=image_url,
                http_status=None,
                status=ResultStatus.INCONCLUSIVE,
                message=(
                    "URL gambar tidak memenuhi kebijakan inspeksi dan tidak diperiksa."
                ),
            )
        else:
            http_status = image_responses.get(image_url)

            if http_status in (401, 403, 429):
                result = ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.ACCESS_RESTRICTED,
                    message=f"Akses gambar dibatasi (HTTP {http_status}).",
                )
            elif http_status is not None and http_status >= 400:
                result = ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.FAILED,
                    message=f"Gambar mengembalikan HTTP {http_status}.",
                )
            elif (
                image["complete"]
                and image["naturalWidth"] > 0
                and image["naturalHeight"] > 0
            ):
                result = ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.PASSED,
                    message="Gambar berhasil dimuat dan didekode browser.",
                )
            elif image["complete"] and image["currentSrc"]:
                result = ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.FAILED,
                    message="Gambar selesai dimuat tetapi gagal didekode browser.",
                )
            else:
                result = ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.INCONCLUSIVE,
                    message="Gambar belum selesai dimuat atau lazy loading belum terpicu.",
                )

        results.append(result)
        _emit_progress(
            progress,
            "Image Inspection",
            "running",
            f"Gambar diperiksa: {result.status.value}.",
            index,
            total,
        )

    return results


def inspect_homepage(config, timeout_ms=30000, controller=None, progress=None):
    """Memeriksa homepage proyek menggunakan Playwright."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = controller or RequestSafetyController(
        max_requests_per_minute=config.max_requests_per_minute,
        stop_after_consecutive_403=config.stop_after_consecutive_403,
    )

    guard = PlaywrightRequestGuard(
        controller=controller,
        base_url=config.base_url,
    )

    screenshot_dir = resolve_project_path(config.project_dir, "evidence", "screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir = resolve_project_path(config.project_dir, "evidence", "screenshots")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    screenshot_file = screenshot_dir / f"homepage_{timestamp}.png"

    screenshot_path = None
    http_status = None
    http_status_text = ""
    response_preview = ""
    page_title = ""
    final_url = config.base_url
    access_classification = AccessClassification(False, "NONE")

    status = ResultStatus.INCONCLUSIVE
    message = "Pemeriksaan belum menghasilkan kesimpulan."

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
                service_workers="block",
                viewport={
                    "width": 1365,
                    "height": 768,
                },
            )

            try:
                guard.install(context)
                page = context.new_page()

                try:
                    _emit_progress(
                        progress,
                        "Homepage",
                        "running",
                        "Membuka homepage melalui browser.",
                        0,
                        1,
                    )
                    response = page.goto(
                        config.base_url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )

                    final_url = page.url

                    if response is None:
                        status = ResultStatus.INCONCLUSIVE
                        message = "Browser tidak menerima respons HTTP."
                    else:
                        http_status = response.status
                        http_status_text = guard.response_status_text.get(
                            response.url,
                            response.status_text,
                        )

                        try:
                            response_body = response.text()
                            response_preview = response_body[:500]
                        except PlaywrightError:
                            response_preview = "Isi respons tidak dapat dibaca."

                        try:
                            page_title = page.title()
                        except PlaywrightError:
                            page_title = ""

                        try:
                            page_text = page.locator("body").inner_text(timeout=5000)
                        except PlaywrightError:
                            page_text = ""

                        access_classification = classify_access_restriction(
                            http_status, page_title, page_text
                        )
                        if access_classification.restricted:
                            status = ResultStatus.ACCESS_RESTRICTED
                            message = (
                                "Akses homepage dibatasi; klasifikasi: "
                                f"{access_classification.classification}."
                            )

                        elif http_status >= 400:
                            status = ResultStatus.FAILED
                            message = f"Homepage mengembalikan HTTP {http_status}."

                        elif controller.is_stopped:
                            status = ResultStatus.ACCESS_RESTRICTED
                            message = controller.stop_reason

                        else:
                            status = ResultStatus.PASSED
                            message = (
                                "Homepage berhasil diakses dan respons HTTP diterima."
                            )

                except PlaywrightTimeoutError:
                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason
                    else:
                        status = ResultStatus.TIMEOUT
                        message = "Pemeriksaan homepage melewati batas waktu."

                    final_url = page.url

                except PlaywrightError:
                    if controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason
                    else:
                        status = ResultStatus.BLOCKED
                        message = "Navigasi homepage gagal atau diblokir oleh mekanisme keamanan."

                    final_url = page.url

                # Screenshot dan registrasi merupakan tahap evidence yang nyata.
                _emit_progress(
                    progress,
                    "Evidence Collection",
                    "running",
                    "Mengambil screenshot homepage.",
                    0,
                    1,
                )
                # Screenshot hanya valid jika navigasi menghasilkan respons HTTP
                # dan halaman berhasil dimuat atau menampilkan halaman pembatasan.
                screenshot_allowed = http_status is not None and status in (
                    ResultStatus.PASSED,
                    ResultStatus.ACCESS_RESTRICTED,
                )

                if screenshot_allowed:
                    try:
                        page.screenshot(
                            path=str(screenshot_file),
                            full_page=True,
                            timeout=10000,
                        )

                        if screenshot_file.is_file():
                            screenshot_path = screenshot_file
                            _register_screenshot_evidence(
                                config.project_id,
                                screenshot_path,
                                final_url,
                                page_title,
                                {"inspection": "frontend_homepage"},
                            )

                    except PlaywrightError:
                        screenshot_path = None

            finally:
                guard.begin_shutdown()
                context.close()

        finally:
            browser.close()

    return HomepageInspectionResult(
        project_id=config.project_id,
        requested_url=config.base_url,
        final_url=final_url,
        status=status,
        http_status=http_status,
        page_title=page_title,
        screenshot_path=screenshot_path,
        message=message,
        http_status_text=http_status_text,
        response_preview=response_preview,
        access_classification=access_classification,
    )


def inspect_links(config, timeout_ms=30000, controller=None, progress=None):
    """Memeriksa tautan homepage dengan pembatasan keamanan."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = controller or RequestSafetyController(
        max_requests_per_minute=config.max_requests_per_minute,
        stop_after_consecutive_403=config.stop_after_consecutive_403,
    )

    guard = PlaywrightRequestGuard(
        controller=controller,
        base_url=config.base_url,
    )

    results = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
                service_workers="block",
            )

            try:
                guard.install(context)
                page = context.new_page()

                try:
                    page.goto(
                        config.base_url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                except PlaywrightError:
                    if controller.is_stopped:
                        return results
                    raise

                links = _extract_page_links(page)
                seen_urls = set()
                _emit_progress(
                    progress,
                    "Link Inspection",
                    "running",
                    "Daftar tautan homepage tersedia untuk diperiksa.",
                    0,
                    len(links),
                )

                api_context = playwright.request.new_context(
                    timeout=timeout_ms,
                    max_redirects=0,
                )

                try:
                    for link_index, link in enumerate(links, start=1):
                        link_type, link_url = _classify_link(
                            link["href"],
                            page.url,
                        )

                        if link_type in ("internal", "anchor"):
                            dedup_key = link_url
                        else:
                            dedup_key = (link_type, link_url)

                        if dedup_key in seen_urls:
                            _emit_progress(
                                progress,
                                "Link Inspection",
                                "running",
                                "Tautan duplikat dilewati.",
                                link_index,
                                len(links),
                            )
                            continue

                        seen_urls.add(dedup_key)

                        http_status = None
                        stop_scan = False

                        if link_type == "internal":
                            if not guard.is_allowed_url(link_url):
                                status = ResultStatus.INCONCLUSIVE
                                message = "Tautan tidak memenuhi pembatasan origin."
                            else:
                                try:
                                    controller.acquire()

                                    response = api_context.get(
                                        link_url,
                                        timeout=timeout_ms,
                                        max_redirects=0,
                                        fail_on_status_code=False,
                                    )

                                    http_status = response.status

                                    try:
                                        controller.record_response(http_status)
                                    except RequestSafetyStop as exc:
                                        status = ResultStatus.ACCESS_RESTRICTED
                                        message = str(exc)
                                        stop_scan = True
                                    else:
                                        if 200 <= http_status < 300:
                                            status = ResultStatus.PASSED
                                            message = (
                                                f"Tautan merespons HTTP {http_status}."
                                            )
                                        elif http_status in (401, 403, 429):
                                            status = ResultStatus.ACCESS_RESTRICTED
                                            message = (
                                                "Akses tautan dibatasi "
                                                f"(HTTP {http_status})."
                                            )
                                            stop_scan = http_status in (401, 429)
                                        elif 300 <= http_status < 400:
                                            status = ResultStatus.INCONCLUSIVE
                                            message = (
                                                "Redirect tidak diikuti "
                                                f"(HTTP {http_status})."
                                            )
                                        elif 400 <= http_status <= 599:
                                            status = ResultStatus.FAILED
                                            message = (
                                                f"Tautan merespons HTTP {http_status}."
                                            )
                                        else:
                                            status = ResultStatus.INCONCLUSIVE
                                            message = (
                                                "Respons HTTP tidak dapat "
                                                "diklasifikasikan."
                                            )

                                except RequestSafetyStop as exc:
                                    status = ResultStatus.ACCESS_RESTRICTED
                                    message = str(exc)
                                    stop_scan = True

                                except PlaywrightTimeoutError:
                                    status = ResultStatus.TIMEOUT
                                    message = "Pemeriksaan tautan melewati batas waktu."

                                except PlaywrightError:
                                    status = ResultStatus.INCONCLUSIVE
                                    message = (
                                        "Request tidak dapat diselesaikan "
                                        "oleh Playwright."
                                    )

                        elif link_type == "external":
                            status = ResultStatus.INCONCLUSIVE
                            message = "Tautan eksternal tidak diperiksa."

                        elif link_type == "sensitive":
                            status = ResultStatus.INCONCLUSIVE
                            message = (
                                "Tautan dengan parameter sensitif tidak diperiksa."
                            )

                        elif link_type == "anchor":
                            anchor_id = link_url[1:]

                            anchor_exists = (
                                page.locator(
                                    f'[id="{anchor_id}"], [name="{anchor_id}"]'
                                ).count()
                                > 0
                            )

                            if anchor_exists:
                                status = ResultStatus.PASSED
                                message = "Target anchor ditemukan pada halaman."
                            else:
                                status = ResultStatus.FAILED
                                message = "Target anchor tidak ditemukan pada halaman."

                        else:
                            status = ResultStatus.INCONCLUSIVE
                            message = "Protokol khusus tidak diperiksa."

                        results.append(
                            LinkInspectionResult(
                                link_url=link_url,
                                link_text=link["text"],
                                link_type=link_type,
                                http_status=http_status,
                                status=status,
                                message=message,
                            )
                        )
                        _emit_progress(
                            progress,
                            "Link Inspection",
                            "running",
                            f"Tautan {link_type} diperiksa: {status.value}.",
                            link_index,
                            len(links),
                        )

                        if stop_scan:
                            break

                finally:
                    api_context.dispose()

            finally:
                guard.begin_shutdown()
                context.close()

        finally:
            browser.close()

    return results


def _progress_terminal_status(statuses):
    statuses = tuple(statuses)
    if ResultStatus.ACCESS_RESTRICTED in statuses:
        return "stopped"
    if any(
        status
        in (
            ResultStatus.FAILED,
            ResultStatus.BLOCKED,
            ResultStatus.TIMEOUT,
        )
        for status in statuses
    ):
        return "failed"
    return "completed"


def run_frontend_qa_workflow(
    config,
    timeout_ms=30000,
    controller=None,
    progress=None,
):
    """Run frontend inspection stages and publish optional factual progress."""
    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    controller = controller or RequestSafetyController(
        max_requests_per_minute=config.max_requests_per_minute,
        stop_after_consecutive_403=config.stop_after_consecutive_403,
    )

    _emit_progress(progress, "Homepage", "waiting", "Menunggu inspeksi homepage.")
    _emit_progress(progress, "Homepage", "running", "Memulai inspeksi homepage.", 0, 1)
    try:
        if progress is None:
            homepage = inspect_homepage(config, timeout_ms, controller)
        else:
            homepage = inspect_homepage(
                config, timeout_ms, controller, progress=progress
            )
    except Exception:
        _emit_progress(progress, "Homepage", "failed", "Inspeksi homepage gagal.", 0, 1)
        raise

    homepage_terminal = _progress_terminal_status((homepage.status,))
    _emit_progress(
        progress,
        "Homepage",
        homepage_terminal,
        f"Inspeksi homepage selesai diproses; hasil QA: {homepage.status.value}.",
        1,
        1,
    )

    _emit_progress(
        progress,
        "Evidence Collection",
        "running",
        "Memverifikasi registrasi evidence homepage.",
    )
    evidence_ids = _workflow_evidence_ids(config, homepage)
    evidence_state = "completed" if evidence_ids else "failed"
    _emit_progress(
        progress,
        "Evidence Collection",
        evidence_state,
        "Evidence homepage terverifikasi."
        if evidence_ids
        else "Evidence homepage tidak tersedia atau gagal diverifikasi.",
        len(evidence_ids),
        1,
    )

    image_results = ()
    link_results = ()
    image_status = None
    link_status = None
    image_message = "Pemeriksaan gambar dinonaktifkan pada konfigurasi proyek."
    link_message = "Pemeriksaan tautan dinonaktifkan pada konfigurasi proyek."

    if homepage.status == ResultStatus.ACCESS_RESTRICTED or controller.is_stopped:
        reason = controller.stop_reason or homepage.message
        skipped_status = ResultStatus.ACCESS_RESTRICTED
        skipped_message = "Dilewati karena akses homepage dibatasi."

    elif homepage.status != ResultStatus.PASSED:
        reason = homepage.message
        skipped_status = ResultStatus.INCONCLUSIVE
        skipped_message = "Dilewati karena homepage tidak berhasil diakses."

    else:
        reason = None
        skipped_status = None
        skipped_message = ""

    if skipped_status is not None:
        if config.check_images:
            image_status = skipped_status
            image_message = skipped_message
            _emit_progress(progress, "Image Inspection", "stopped", image_message, 0, 0)

        if config.check_links:
            link_status = skipped_status
            link_message = skipped_message
            _emit_progress(progress, "Link Inspection", "stopped", link_message, 0, 0)

        result = FrontendQAWorkflowResult(
            config.project_id,
            homepage.status
            if skipped_status == ResultStatus.INCONCLUSIVE
            else ResultStatus.ACCESS_RESTRICTED,
            homepage,
            image_results,
            link_results,
            image_status,
            link_status,
            image_message,
            link_message,
            reason or "",
            evidence_ids,
        )

        terminal = (
            "stopped"
            if skipped_status == ResultStatus.ACCESS_RESTRICTED
            else _progress_terminal_status((homepage.status,))
        )

        _emit_progress(
            progress,
            "Frontend Inspection",
            terminal,
            f"Inspeksi frontend dihentikan: {result.status.value}. {reason or ''}",
        )
        return result
    if config.check_images:
        _emit_progress(
            progress,
            "Image Inspection",
            "waiting",
            "Menunggu pemeriksaan gambar.",
        )
        _emit_progress(
            progress,
            "Image Inspection",
            "running",
            "Memulai pemeriksaan gambar homepage.",
        )
        try:
            if progress is None:
                image_results = tuple(inspect_images(config, timeout_ms, controller))
            else:
                image_results = tuple(
                    inspect_images(config, timeout_ms, controller, progress=progress)
                )
        except Exception:
            _emit_progress(
                progress,
                "Image Inspection",
                "failed",
                "Pemeriksaan gambar gagal.",
            )
            raise
        restricted = controller.is_stopped or any(
            item.status == ResultStatus.ACCESS_RESTRICTED for item in image_results
        )
        image_status = (
            ResultStatus.ACCESS_RESTRICTED
            if restricted
            else _aggregate_result_status(item.status for item in image_results)
        )
        image_message = controller.stop_reason or "Pemeriksaan gambar selesai."
        image_terminal = _progress_terminal_status(
            [image_status, *(item.status for item in image_results)]
        )
        _emit_progress(
            progress,
            "Image Inspection",
            image_terminal,
            f"Pemeriksaan gambar selesai diproses; hasil QA: {image_status.value}.",
        )
        if restricted:
            if config.check_links:
                link_status = ResultStatus.ACCESS_RESTRICTED
                link_message = (
                    "Dilewati setelah pembatasan akses pada pemeriksaan gambar."
                )
                _emit_progress(
                    progress, "Link Inspection", "stopped", link_message, 0, 0
                )
            result = FrontendQAWorkflowResult(
                config.project_id,
                ResultStatus.ACCESS_RESTRICTED,
                homepage,
                image_results,
                link_results,
                image_status,
                link_status,
                image_message,
                link_message,
                controller.stop_reason or image_message,
                evidence_ids,
            )
            _emit_progress(
                progress,
                "Frontend Inspection",
                "stopped",
                result.stopped_reason,
            )
            return result

    if config.check_links:
        _emit_progress(
            progress,
            "Link Inspection",
            "waiting",
            "Menunggu pemeriksaan tautan.",
        )
        _emit_progress(
            progress,
            "Link Inspection",
            "running",
            "Memulai pemeriksaan tautan homepage.",
        )
        try:
            if progress is None:
                link_results = tuple(inspect_links(config, timeout_ms, controller))
            else:
                link_results = tuple(
                    inspect_links(config, timeout_ms, controller, progress=progress)
                )
        except Exception:
            _emit_progress(
                progress,
                "Link Inspection",
                "failed",
                "Pemeriksaan tautan gagal.",
            )
            raise
        restricted = controller.is_stopped or any(
            item.status == ResultStatus.ACCESS_RESTRICTED for item in link_results
        )
        link_status = (
            ResultStatus.ACCESS_RESTRICTED
            if restricted
            else _aggregate_result_status(item.status for item in link_results)
        )
        link_message = controller.stop_reason or "Pemeriksaan tautan selesai."
        link_terminal = _progress_terminal_status(
            [link_status, *(item.status for item in link_results)]
        )
        _emit_progress(
            progress,
            "Link Inspection",
            link_terminal,
            f"Pemeriksaan tautan selesai diproses; hasil QA: {link_status.value}.",
        )

    stage_statuses = [homepage.status]
    if image_status is not None:
        stage_statuses.append(image_status)
    if link_status is not None:
        stage_statuses.append(link_status)
    status = _aggregate_result_status(stage_statuses)
    result = FrontendQAWorkflowResult(
        config.project_id,
        status,
        homepage,
        image_results,
        link_results,
        image_status,
        link_status,
        image_message,
        link_message,
        controller.stop_reason or "",
        evidence_ids,
    )
    terminal_status = _progress_terminal_status(
        [
            homepage.status,
            status,
            *(item.status for item in image_results),
            *(item.status for item in link_results),
        ]
    )
    if terminal_status == "completed" and not evidence_ids:
        terminal_status = "failed"
    _emit_progress(
        progress,
        "Frontend Inspection",
        terminal_status,
        "Inspeksi frontend selesai diproses; hasil QA: "
        f"{status.value}; evidence: "
        f"{'verified' if evidence_ids else 'failed'}.",
    )
    return result


def _aggregate_result_status(statuses):
    statuses = tuple(statuses)
    if not statuses:
        return ResultStatus.PASSED
    if ResultStatus.ACCESS_RESTRICTED in statuses:
        return ResultStatus.ACCESS_RESTRICTED
    if ResultStatus.FAILED in statuses:
        return ResultStatus.FAILED
    if ResultStatus.BLOCKED in statuses:
        return ResultStatus.BLOCKED
    if ResultStatus.TIMEOUT in statuses:
        return ResultStatus.TIMEOUT
    if any(status != ResultStatus.PASSED for status in statuses):
        return ResultStatus.INCONCLUSIVE
    return ResultStatus.PASSED


def _workflow_evidence_ids(config, homepage):
    if not homepage.screenshot_path:
        return ()
    try:
        screenshot_path = Path(homepage.screenshot_path).resolve()
        evidence_dir = (Path(config.project_dir) / "evidence").resolve()
        relative_path = screenshot_path.relative_to(evidence_dir).as_posix()
        return tuple(
            item["evidence_id"]
            for item in list_evidence(config.project_id)
            if item.get("file_path") == relative_path
            and isinstance(item.get("evidence_id"), str)
            and verify_evidence(config.project_id, item["evidence_id"])
        )
    except (OSError, ValueError, KeyError, TypeError):
        return ()
