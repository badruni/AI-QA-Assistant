
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


# Kata kunci yang dianggap mengandung informasi sensitif.
SECRET_KEYS = (
    r"password|passwd|pwd|token|access_token|refresh_token|"
    r"api[_-]?key|authorization|proxy-authorization|cookie|"
    r"set-cookie|secret|client_secret|session(?:id)?|"
    r"username|user_name|credentials?|signature|accesskeyid|"
    r"privatekey|auth(?:entication)?"
)

SENSITIVE_QUERY_MARKERS = (
    "password", "passwd", "pwd", "token", "apikey", "secret",
    "credential", "authorization", "cookie", "session", "signature",
    "accesskeyid", "privatekey", "authentication",
)


def is_sensitive_parameter_name(name):
    """Recognize common credential and signed-URL query parameter names."""
    normalized = re.sub(r"[^a-z0-9]", "", str(name).casefold())
    return normalized == "sig" or any(
        marker in normalized for marker in SENSITIVE_QUERY_MARKERS
    ) or normalized.startswith("auth")


def has_sensitive_url_query(value):
    """Return whether an HTTP URL carries a known sensitive query key."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return any(
            is_sensitive_parameter_name(key)
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
        )
    except ValueError:
        return False


def sanitize_url(value):
    """Redact known sensitive URL values while retaining ordinary query data.

    Fragments are omitted because they are not needed for an HTTP request and
    are commonly used to carry client-side authentication tokens.
    """
    if not isinstance(value, str):
        return "[URL_REDACTED]"
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return "[URL_REDACTED]"
        host = parsed.hostname
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        if parsed.port:
            host = f"{host}:{parsed.port}"
        safe_query = []
        for key, item in parse_qsl(parsed.query, keep_blank_values=True):
            if is_sensitive_parameter_name(key):
                item = "[REDACTED]"
            else:
                item = sanitize_text(item)
            safe_query.append((key, item))
        return urlunsplit((parsed.scheme.lower(), host, parsed.path,
                           urlencode(safe_query, doseq=True, safe="[]"), ""))
    except (TypeError, ValueError):
        return "[URL_REDACTED]"


# Menyamarkan pola key=value atau key: value.
KEY_VALUE_PATTERN = re.compile(
    rf"""(?i)(["']?(?:{SECRET_KEYS})["']?\s*[:=]\s*)"""
    r"""(?:"[^"]*"|'[^']*'|[^\s,;&}}\]]+)"""
)


# Menyamarkan header autentikasi.
SENSITIVE_HEADER_PATTERN = re.compile(
    r"(?im)^(\s*(?:cookie|set-cookie|authorization|"
    r"proxy-authorization)\s*:\s*).*$"
)


# Menyamarkan username/password di URL.
URL_CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(https?://)[^/\s@]+@"
)


# Menyamarkan Bearer dan Basic token.
AUTH_TOKEN_PATTERN = re.compile(
    r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+"
)


# Menyamarkan JWT.
JWT_PATTERN = re.compile(
    r"\beyJ[A-Za-z0-9_-]{5,}\."
    r"[A-Za-z0-9_-]{5,}\."
    r"[A-Za-z0-9_-]{5,}\b"
)


# Menyamarkan parameter sensitif pada URL.
URL_SECRET_PATTERN = re.compile(
    r"(?i)([?&](?:[^?&=]*(?:password|passwd|pwd|token|api[-_]?key|"
    r"authorization|cookie|secret|credential|session|signature|"
    r"accesskeyid|privatekey|authentication)[^?&=]*|sig)=)"
    r"[^&#\s]+"
)


def sanitize_text(value):
    """
    Menyamarkan pola informasi sensitif dalam teks.
    Fungsi ini tidak menjamin seluruh rahasia dapat terdeteksi.
    """

    text = str(value)

    text = SENSITIVE_HEADER_PATTERN.sub(
        r"\1[REDACTED]",
        text
    )

    text = URL_CREDENTIAL_PATTERN.sub(
        r"\1[REDACTED]@",
        text
    )

    text = AUTH_TOKEN_PATTERN.sub(
        "[REDACTED AUTH TOKEN]",
        text
    )

    text = JWT_PATTERN.sub(
        "[REDACTED JWT]",
        text
    )

    text = URL_SECRET_PATTERN.sub(
        r"\1[REDACTED]",
        text
    )

    text = KEY_VALUE_PATTERN.sub(
        r"\1[REDACTED]",
        text
    )

    return text
