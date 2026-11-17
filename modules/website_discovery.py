from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.playwright_request_guard import PlaywrightRequestGuard
from core.request_safety import RequestSafetyController
from core.result_status import ResultStatus

DEFAULT_MAX_PAGES = 20


@dataclass(frozen=True)
class DiscoveredPage:
    url: str
    final_url: str
    title: str
    http_status: int | None
    status: ResultStatus
    page_type: str
    component_counts: dict
    internal_links: tuple
    screenshot_path: Path | None
    message: str


@dataclass(frozen=True)
class WebsiteDiscoveryResult:
    project_id: str
    start_url: str
    status: ResultStatus
    pages: tuple
    max_pages: int
    completed: bool
    stopped_reason: str
    message: str


def _normalize_internal_url(href, current_url, guard):
    if not isinstance(href, str) or not href.strip():
        return None
    try:
        target = urljoin(current_url, href.strip())
        parsed = urlsplit(target)
        if parsed.scheme.lower() not in ("http", "https"):
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        if not guard.is_allowed_url(target):
            return None
        return urlunsplit((
            parsed.scheme.lower(), parsed.netloc, parsed.path or "/",
            parsed.query, "",
        ))
    except (TypeError, ValueError):
        return None


def _inspect_components(page):
    return page.evaluate("""() => {
        const count = selector => document.querySelectorAll(selector).length;
        return {
            headings: count('h1, h2, h3, h4, h5, h6'),
            navigation: count('nav, [role="navigation"]'),
            links: count('a[href]'),
            buttons: count('button, input[type="button"], input[type="submit"], [role="button"]'),
            forms: count('form'),
            inputs: count('input, textarea, select, [contenteditable="true"]'),
            images: count('img, picture'),
            card_candidates: count('article, [class*="card" i], [class*="tile" i]')
        };
    }""")


def _classify_page(url, components):
    """Klasifikasi konservatif berdasarkan token URL dan komponen DOM."""
    import re

    path = urlsplit(url).path.casefold()
    tokens = set(re.findall(r"[a-z0-9]+", path))

    if not tokens:
        return "homepage"

    product_tokens = {"product", "products", "produk", "item", "items"}
    article_tokens = {
        "article", "articles", "artikel", "blog",
        "news", "berita",
    }

    if tokens & product_tokens:
        return "product"

    if tokens & article_tokens:
        return "article"

    if components.get("forms", 0):
        return "form"

    if components.get("card_candidates", 0) >= 2:
        return "listing"

    return "unknown"


def discover_website(config, max_pages=DEFAULT_MAX_PAGES, timeout_ms=30000):
    """Read-only discovery halaman internal dan komponen DOM."""
    if isinstance(max_pages, bool) or not isinstance(max_pages, int):
        raise ValueError("max_pages harus berupa bilangan bulat.")
    if not 1 <= max_pages <= DEFAULT_MAX_PAGES:
        raise ValueError(f"max_pages harus berada antara 1 dan {DEFAULT_MAX_PAGES}.")
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise ValueError("timeout_ms harus berupa bilangan bulat.")
    if timeout_ms < 1000:
        raise ValueError("timeout_ms minimal 1000 milidetik.")

    controller = RequestSafetyController(
        config.max_requests_per_minute,
        config.stop_after_consecutive_403,
    )
    guard = PlaywrightRequestGuard(controller, config.base_url)
    screenshots_dir = Path(config.project_dir) / "evidence" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    queue = [config.base_url]
    queued = {config.base_url}
    visited = set()
    results = []
    stopped_reason = ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            service_workers="block",
            viewport={"width": 1365, "height": 768},
        )
        guard.install(context)
        page = context.new_page()
        try:
            while queue and len(results) < max_pages:
                target_url = queue.pop(0)
                if target_url in visited:
                    continue
                visited.add(target_url)

                title = ""
                final_url = target_url
                http_status = None
                status = ResultStatus.INCONCLUSIVE
                page_type = "unknown"
                counts = {}
                internal_links = []
                screenshot_path = None
                message = ""

                try:
                    response = page.goto(
                        target_url, wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                    final_url = page.url or target_url
                    if response is not None:
                        http_status = response.status
                    title = page.title()
                    body = page.locator("body").inner_text(timeout=3000)
                    lower = (title + " " + body).casefold()
                    waf = (
                        "bot_headless" in lower
                        or ("request blocked" in lower and "bot detected" in lower)
                        or "verify you are human" in lower
                        or "checking your browser" in lower
                    )

                    if waf:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = "Indikator challenge/blokir keamanan terdeteksi."
                    elif http_status in (401, 403):
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = f"Akses dibatasi (HTTP {http_status})."
                    elif http_status is not None and http_status >= 400:
                        status = ResultStatus.FAILED
                        message = f"Halaman merespons HTTP {http_status}."
                    elif controller.is_stopped:
                        status = ResultStatus.ACCESS_RESTRICTED
                        message = controller.stop_reason or "Scanner dihentikan oleh kontrol keamanan."
                    elif response is None:
                        status = ResultStatus.INCONCLUSIVE
                        message = "Tidak ada respons navigasi yang dapat diverifikasi."
                    else:
                        status = ResultStatus.PASSED
                        message = "Halaman berhasil dimuat dan diperiksa."

                    if status == ResultStatus.PASSED:
                        counts = _inspect_components(page)
                        page_type = _classify_page(target_url, counts)
                        hrefs = page.locator("a[href]").evaluate_all(
                            "nodes => nodes.map(node => node.getAttribute('href'))"
                        )
                        for href in hrefs:
                            found = _normalize_internal_url(href, final_url, guard)
                            if found and found not in queued and found not in visited:
                                queued.add(found)
                                internal_links.append(found)
                                queue.append(found)

                        screenshot_path = screenshots_dir / (
                            f"discovery_{timestamp}_{len(results) + 1:02d}.png"
                        )
                        try:
                            page.screenshot(
                                path=str(screenshot_path), full_page=True,
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
                        message = controller.stop_reason or "Scanner dihentikan demi keamanan."
                    else:
                        status = ResultStatus.BLOCKED
                        message = f"Navigasi browser gagal ({type(error).__name__})."

                results.append(DiscoveredPage(
                    url=target_url, final_url=final_url, title=title,
                    http_status=http_status, status=status, page_type=page_type,
                    component_counts=counts, internal_links=tuple(internal_links),
                    screenshot_path=screenshot_path, message=message,
                ))

                if status == ResultStatus.ACCESS_RESTRICTED:
                    stopped_reason = message
                    break
                if controller.is_stopped:
                    stopped_reason = controller.stop_reason or "Scanner dihentikan demi keamanan."
                    break
        finally:
            context.close()
            browser.close()

    if stopped_reason:
        overall = ResultStatus.ACCESS_RESTRICTED
        completed = False
        message = "Discovery dihentikan karena pembatasan akses atau keamanan."
    elif queue:
        overall = ResultStatus.NEEDS_REVIEW
        completed = False
        stopped_reason = f"Batas {max_pages} halaman tercapai; masih ada {len(queue)} URL dalam antrean."
        message = "Discovery belum lengkap karena batas maksimum halaman tercapai."
    elif any(item.status != ResultStatus.PASSED for item in results):
        overall = ResultStatus.NEEDS_REVIEW
        completed = False
        message = "Discovery selesai berjalan, tetapi sebagian halaman perlu ditinjau."
    else:
        overall = ResultStatus.PASSED
        completed = True
        message = "Discovery selesai untuk halaman yang berhasil ditemukan."

    return WebsiteDiscoveryResult(
        project_id=config.project_id, start_url=config.base_url,
        status=overall, pages=tuple(results), max_pages=max_pages,
        completed=completed, stopped_reason=stopped_reason, message=message,
    )
