
import re


# Kata kunci yang dianggap mengandung informasi sensitif.
SECRET_KEYS = (
    r"password|passwd|pwd|token|access_token|refresh_token|"
    r"api[_-]?key|authorization|proxy-authorization|cookie|"
    r"set-cookie|secret|client_secret|session(?:id)?|"
    r"username|user_name"
)


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
    rf"(?i)([?&](?:{SECRET_KEYS})=)[^&#\s]+"
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
