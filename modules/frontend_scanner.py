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

from core.playwright_request_guard import PlaywrightRequestGuard
from core.project_manager import get_project, validate_project_id, validate_url
from core.request_safety import (
    RequestSafetyController,
    RequestSafetyStop,
)
from core.result_status import ResultStatus

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"


def _looks_like_waf_block_page(page_title, page_text):
    """Mendeteksi indikator kuat halaman blokir WAF."""

    content = f"{page_title} {page_text}".casefold()

    if "bot_headless" in content:
        return True

    return "request blocked" in content and "bot detected" in content


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

    project_dir = PROJECTS_DIR / project_id

    if not project_dir.is_dir():
        raise FileNotFoundError("Folder proyek tidak ditemukan.")

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


def inspect_images(config, timeout_ms=30000):
    """Memeriksa gambar pada homepage tanpa melewati request guard."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = RequestSafetyController(
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

                page.goto(
                    config.base_url,
                    wait_until="load",
                    timeout=timeout_ms,
                )

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
                context.close()

        finally:
            browser.close()

    results = []
    seen_urls = set()

    for image in images:
        image_url = image["url"]

        if not image_url or image_url in seen_urls:
            continue

        seen_urls.add(image_url)

        if not guard.is_allowed_url(image_url):
            results.append(
                ImageInspectionResult(
                    image_url=image_url,
                    http_status=None,
                    status=ResultStatus.INCONCLUSIVE,
                    message="Gambar eksternal tidak diperiksa.",
                )
            )
            continue

        http_status = image_responses.get(image_url)

        if http_status is not None and http_status >= 400:
            results.append(
                ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.FAILED,
                    message=f"Gambar mengembalikan HTTP {http_status}.",
                )
            )

        elif (
            image["complete"]
            and image["naturalWidth"] > 0
            and image["naturalHeight"] > 0
        ):
            results.append(
                ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.PASSED,
                    message="Gambar berhasil dimuat dan didekode browser.",
                )
            )

        elif image["complete"] and image["currentSrc"]:
            results.append(
                ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.FAILED,
                    message="Gambar selesai dimuat tetapi gagal didekode browser.",
                )
            )

        else:
            results.append(
                ImageInspectionResult(
                    image_url=image_url,
                    http_status=http_status,
                    status=ResultStatus.INCONCLUSIVE,
                    message="Gambar belum selesai dimuat atau lazy loading belum terpicu.",
                )
            )

    return results


def inspect_homepage(config, timeout_ms=30000):
    """Memeriksa homepage proyek menggunakan Playwright."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = RequestSafetyController(
        max_requests_per_minute=config.max_requests_per_minute,
        stop_after_consecutive_403=config.stop_after_consecutive_403,
    )

    guard = PlaywrightRequestGuard(
        controller=controller,
        base_url=config.base_url,
    )

    screenshot_dir = config.project_dir / "evidence" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    screenshot_file = screenshot_dir / f"homepage_{timestamp}.png"

    screenshot_path = None
    http_status = None
    http_status_text = ""
    response_preview = ""
    page_title = ""
    final_url = config.base_url

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

                        if http_status in (401, 403):
                            status = ResultStatus.ACCESS_RESTRICTED
                            message = f"Homepage membatasi akses. HTTP {http_status}."

                        elif _looks_like_waf_block_page(
                            page_title,
                            page_text,
                        ):
                            status = ResultStatus.ACCESS_RESTRICTED
                            message = (
                                "Halaman menunjukkan indikator blokir "
                                "WAF berdasarkan konten yang ditampilkan."
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
                    status = ResultStatus.TIMEOUT
                    message = "Pemeriksaan homepage melewati batas waktu."

                    final_url = page.url

                except PlaywrightError:
                    status = ResultStatus.BLOCKED
                    message = (
                        "Navigasi homepage gagal atau diblokir oleh mekanisme keamanan."
                    )

                    final_url = page.url

                # Simpan screenshot jika browser masih memiliki halaman.
                try:
                    page.screenshot(
                        path=str(screenshot_file),
                        full_page=True,
                        timeout=10000,
                    )

                    if screenshot_file.is_file():
                        screenshot_path = screenshot_file

                except PlaywrightError:
                    screenshot_path = None

            finally:
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
    )


def inspect_links(config, timeout_ms=30000):
    """Memeriksa tautan homepage dengan pembatasan keamanan."""

    if not isinstance(config, ScannerConfig):
        raise TypeError("Konfigurasi scanner tidak valid.")

    if (
        isinstance(timeout_ms, bool)
        or not isinstance(timeout_ms, int)
        or timeout_ms < 1000
    ):
        raise ValueError("Timeout harus minimal 1000 milidetik.")

    controller = RequestSafetyController(
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

                page.goto(
                    config.base_url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )

                links = _extract_page_links(page)
                seen_urls = set()

                api_context = playwright.request.new_context(
                    timeout=timeout_ms,
                    max_redirects=0,
                )

                try:
                    for link in links:
                        link_type, link_url = _classify_link(
                            link["href"],
                            page.url,
                        )

                        if link_type in ("internal", "anchor"):
                            dedup_key = link_url
                        else:
                            dedup_key = (link_type, link_url)

                        if dedup_key in seen_urls:
                            continue

                        seen_urls.add(dedup_key)

                        http_status = None
                        stop_scan = False

                        if link_type == "internal":
                            if not guard.is_allowed_url(link_url):
                                status = ResultStatus.INCONCLUSIVE
                                message = (
                                    "Tautan tidak memenuhi pembatasan origin."
                                )
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
                                        controller.record_response(
                                            http_status
                                        )
                                    except RequestSafetyStop as exc:
                                        status = (
                                            ResultStatus.ACCESS_RESTRICTED
                                        )
                                        message = str(exc)
                                        stop_scan = True
                                    else:
                                        if 200 <= http_status < 300:
                                            status = ResultStatus.PASSED
                                            message = (
                                                "Tautan merespons HTTP "
                                                f"{http_status}."
                                            )
                                        elif http_status in (401, 403):
                                            status = (
                                                ResultStatus.ACCESS_RESTRICTED
                                            )
                                            message = (
                                                "Akses tautan dibatasi "
                                                f"(HTTP {http_status})."
                                            )
                                        elif 300 <= http_status < 400:
                                            status = (
                                                ResultStatus.INCONCLUSIVE
                                            )
                                            message = (
                                                "Redirect tidak diikuti "
                                                f"(HTTP {http_status})."
                                            )
                                        elif 400 <= http_status <= 599:
                                            status = ResultStatus.FAILED
                                            message = (
                                                "Tautan merespons HTTP "
                                                f"{http_status}."
                                            )
                                        else:
                                            status = (
                                                ResultStatus.INCONCLUSIVE
                                            )
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
                                    message = (
                                        "Pemeriksaan tautan melewati batas "
                                        "waktu."
                                    )

                                except PlaywrightError:
                                    status = ResultStatus.INCONCLUSIVE
                                    message = (
                                        "Request tidak dapat diselesaikan "
                                        "oleh Playwright."
                                    )

                        elif link_type == "external":
                            status = ResultStatus.INCONCLUSIVE
                            message = "Tautan eksternal tidak diperiksa."

                        elif link_type == "anchor":
                            anchor_id = link_url[1:]

                            anchor_exists = (
                                page.locator(
                                    f'[id="{anchor_id}"], '
                                    f'[name="{anchor_id}"]'
                                ).count() > 0
                            )

                            if anchor_exists:
                                status = ResultStatus.PASSED
                                message = (
                                    "Target anchor ditemukan pada halaman."
                                )
                            else:
                                status = ResultStatus.FAILED
                                message = (
                                    "Target anchor tidak ditemukan "
                                    "pada halaman."
                                )

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

                        if stop_scan:
                            break

                finally:
                    api_context.dispose()

            finally:
                context.close()

        finally:
            browser.close()

    return results
