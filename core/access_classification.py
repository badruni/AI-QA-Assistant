"""Conservative classification of observed access restrictions.

This module records indicators only. It never retries, alters browser identity,
or attempts to solve or bypass a security challenge.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessClassification:
    restricted: bool
    classification: str
    provider: str = "none"
    indicators: tuple[str, ...] = ()


def classify_access_restriction(http_status=None, title="", body_text=""):
    """Return safe indicator codes without retaining page content."""
    title_text = title if isinstance(title, str) else ""
    visible_text = body_text if isinstance(body_text, str) else ""
    normalized_title = title_text.casefold()
    normalized_body = visible_text.casefold()
    content = f"{normalized_title} {normalized_body}"

    cloudflare_markers = (
        "cloudflare", "cf-chl-", "challenge-platform", "cf-turnstile",
    )
    challenge_phrases = (
        "checking your browser", "verify you are human",
        "performing security verification", "security check",
    )
    bot_block = (
        "bot_headless" in content
        or ("request blocked" in content and "bot detected" in content)
    )
    challenge_matches = tuple(
        phrase for phrase in challenge_phrases if phrase in content
    )
    cloudflare_matches = tuple(
        marker for marker in cloudflare_markers if marker in content
    )
    just_a_moment_challenge = (
        normalized_title.strip().startswith("just a moment")
        and any(phrase in normalized_body for phrase in (
            "checking your browser", "verify you are human",
        ))
    )
    cloudflare_challenge_title = (
        bool(cloudflare_matches)
        and normalized_title.strip().startswith("just a moment")
    )
    cloudflare_block_phrases = (
        "you have been blocked", "attention required", "error 1020",
        "being rate limited",
    )
    cloudflare_block = bool(cloudflare_matches) and any(
        phrase in content for phrase in cloudflare_block_phrases
    )

    if (
        cloudflare_matches and (challenge_matches or cloudflare_challenge_title)
    ) or just_a_moment_challenge:
        indicators = ["challenge_phrase"]
        if cloudflare_matches:
            indicators.append("cloudflare_marker")
        if just_a_moment_challenge or cloudflare_challenge_title:
            indicators.append("cloudflare_challenge_title")
        return AccessClassification(
            True, "CLOUDFLARE_CHALLENGE", "cloudflare", tuple(indicators)
        )

    if cloudflare_block and http_status != 429:
        return AccessClassification(
            True, "CLOUDFLARE_WAF_BLOCK", "cloudflare",
            ("cloudflare_marker", "block_page_phrase"),
        )

    if cloudflare_matches and http_status in (401, 403, 429):
        return AccessClassification(
            True, "CLOUDFLARE_ACCESS_RESTRICTED", "cloudflare",
            ("cloudflare_marker", f"http_{http_status}"),
        )

    if bot_block:
        indicators = ("headless_marker",) if "bot_headless" in content else (
            "request_blocked", "bot_detected",
        )
        return AccessClassification(True, "WAF_BLOCK", "unknown", indicators)

    if "access denied" in content and any(
        phrase in content for phrase in (
            "security policy", "firewall", "automated request",
        )
    ):
        return AccessClassification(
            True, "WAF_BLOCK", "unknown",
            ("access_denied", "security_context"),
        )

    if challenge_matches:
        return AccessClassification(
            True, "SECURITY_CHALLENGE", "unknown", ("challenge_phrase",)
        )

    if http_status in (401, 403):
        return AccessClassification(
            True, "HTTP_ACCESS_RESTRICTED", "unknown",
            (f"http_{http_status}",),
        )

    if http_status == 429:
        return AccessClassification(
            True, "HTTP_RATE_LIMITED", "unknown", ("http_429",)
        )

    return AccessClassification(False, "NONE")
