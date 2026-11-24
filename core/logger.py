from core.security import sanitize_text as sanitize_sensitive_text
from core.path_safety import resolve_project_directory, resolve_project_path
from datetime import datetime
from pathlib import Path
import re
import threading
import traceback

from core.data_paths import PROJECTS_DIR, SYSTEM_LOG_DIR

MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
_WRITE_LOCK = threading.Lock()

# Informasi yang tidak boleh tersimpan dalam log.
SENSITIVE_KEYS = (
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token",
    "api_key", "apikey",
    "authorization", "cookie", "set-cookie",
    "secret", "client_secret", "signature", "accesskeyid",
    "privatekey", "authentication",
    "session", "sessionid",
    "username", "user_name"
)

_KEY_PATTERN = "|".join(re.escape(key) for key in SENSITIVE_KEYS)

# Menyaring format: password="rahasia" atau "password": "rahasia"
_QUOTED_SECRET = re.compile(
    rf"""(?i)(["']?(?:{_KEY_PATTERN})["']?\s*[:=]\s*)"""
    r"""(["']).*?\2"""
)

# Menyaring format: password=rahasia
_UNQUOTED_SECRET = re.compile(
    rf"""(?i)\b(?:{_KEY_PATTERN})\b\s*[:=]\s*[^\s,;&}}\]]+"""
)

# Menyaring token autentikasi dan parameter URL sensitif.
_BEARER_PATTERN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"
)

_URL_SECRET = re.compile(
    rf"(?i)([?&](?:{_KEY_PATTERN})=)[^&#\s]+"
)


def sanitize_text(value):
    """Menyaring data sensitif sebelum ditulis ke file log."""
    text = str(value)

    text = _QUOTED_SECRET.sub(r"\1[REDACTED]", text)
    text = _UNQUOTED_SECRET.sub("[REDACTED]", text)
    text = _BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    text = _URL_SECRET.sub(r"\1[REDACTED]", text)

    return text



def _get_log_path(folder, prefix, incoming_size=0):
    """Menentukan file log harian berdasarkan batas ukuran."""
    folder.mkdir(parents=True, exist_ok=True)

    date_label = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{prefix}_{date_label}"
    part = 1

    while True:
        if part == 1:
            filename = f"{base_name}.txt"
        else:
            filename = f"{base_name}_part{part}.txt"

        path = folder / filename

        if not path.exists():
            return path

        current_size = path.stat().st_size

        if current_size + incoming_size <= MAX_LOG_SIZE:
            return path

        part += 1


    while True:
        if part == 1:
            filename = f"{base_name}.txt"
        else:
            filename = f"{base_name}_part{part}.txt"

        path = folder / filename

        if not path.exists():
            return path

        if path.stat().st_size < MAX_LOG_SIZE:
            return path

        part += 1


def _write_record(folder, prefix, content):
    """Menambahkan satu catatan ke file log."""
    safe_content = sanitize_sensitive_text(content)
    record = safe_content.rstrip() + "\n\n"
    encoded_size = len(record.encode("utf-8"))

    try:
        with _WRITE_LOCK:
            path = _get_log_path(folder, prefix, encoded_size)

            # Jika satu catatan sendiri melebihi batas, tulis sebagai
            # satu file tersendiri. Batas ukuran adalah target rotasi.
            if encoded_size > MAX_LOG_SIZE:
                timestamp = datetime.now().strftime("%H%M%S_%f")
                path = folder / (
                    f"{prefix}_{datetime.now():%Y-%m-%d}_"
                    f"oversize_{timestamp}.txt"
                )

            with path.open("a", encoding="utf-8") as file:
                file.write(record)

    except OSError as error:
        print(
            "[LOG ERROR] Tidak dapat menulis log. "
            f"Periksa izin folder dan ruang penyimpanan. Detail: {error}"
        )


def write_log(
    level,
    activity,
    explanation,
    causes=None,
    actions=None,
    exception=None
):
    """Menulis System Log."""
    now = datetime.now()

    lines = [
        "=" * 60,
        "AI QA ASSISTANT - SYSTEM LOG",
        "=" * 60,
        f"Tanggal       : {now:%Y-%m-%d}",
        f"Waktu         : {now:%H:%M:%S}",
        f"Status        : {level.upper()}",
        f"Aktivitas     : {activity}",
        "",
        "PENJELASAN:",
        explanation,
    ]

    if causes:
        lines.extend(["", "KEMUNGKINAN PENYEBAB:"])
        lines.extend(f"- {item}" for item in causes)

    if actions:
        lines.extend(["", "SARAN PENANGANAN:"])
        lines.extend(
            f"{index}. {item}"
            for index, item in enumerate(actions, start=1)
        )

    if exception:
        lines.extend(["", "DETAIL TEKNIS:", str(exception)])

    lines.extend(["=" * 60, ""])

    _write_record(SYSTEM_LOG_DIR, "system_log", "\n".join(lines))


def write_project_log(
    project_id,
    level,
    activity,
    explanation,
    causes=None,
    actions=None,
    exception=None
):
    """Menulis Project Log ke folder website yang sesuai."""
    # Mencegah nama project digunakan untuk keluar dari folder projects.
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(project_id)):
        log_error(
            "Menulis Project Log",
            "Project ID tidak valid. Project Log tidak ditulis."
        )
        return

    try:
        project_folder = resolve_project_directory(
            PROJECTS_DIR,
            project_id,
            require_exists=False
        )
    except (ValueError, OSError):
        log_error(
            "Menulis Project Log",
            "Folder proyek tidak aman. Project Log tidak ditulis."
        )
        return

    log_folder = project_folder / "logs"

    now = datetime.now()

    lines = [
        "=" * 60,
        "AI QA ASSISTANT - PROJECT LOG",
        "=" * 60,
        f"Tanggal       : {now:%Y-%m-%d}",
        f"Waktu         : {now:%H:%M:%S}",
        f"Project ID    : {project_id}",
        f"Status        : {level.upper()}",
        f"Aktivitas     : {activity}",
        "",
        "PENJELASAN:",
        explanation,
    ]

    if causes:
        lines.extend(["", "KEMUNGKINAN PENYEBAB:"])
        lines.extend(f"- {item}" for item in causes)

    if actions:
        lines.extend(["", "SARAN PENANGANAN:"])
        lines.extend(
            f"{index}. {item}"
            for index, item in enumerate(actions, start=1)
        )

    if exception:
        lines.extend(["", "DETAIL TEKNIS:", str(exception)])

    lines.extend(["=" * 60, ""])

    _write_record(log_folder, "project_log", "\n".join(lines))


def log_info(activity, explanation):
    write_log("INFO", activity, explanation)


def log_warning(activity, explanation, actions=None):
    write_log(
        "WARNING", activity, explanation, actions=actions
    )


def log_error(
    activity,
    explanation,
    causes=None,
    actions=None,
    exception=None
):
    write_log(
        "ERROR", activity, explanation,
        causes=causes, actions=actions, exception=exception
    )


def log_exception(activity, exception, explanation, actions=None):
    technical_details = "".join(
        traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        )
    )

    log_error(
        activity=activity,
        explanation=explanation,
        causes=[
            "Terjadi kesalahan saat aplikasi menjalankan proses.",
            "Lihat DETAIL TEKNIS untuk informasi error."
        ],
        actions=actions or [
            "Baca System Log terbaru.",
            "Periksa file dan konfigurasi yang terkait.",
            "Jika belum terselesaikan, kirim log kepada developer."
        ],
        exception=technical_details
    )


def project_log_info(project_id, activity, explanation):
    write_project_log(project_id, "INFO", activity, explanation)


def project_log_warning(
    project_id, activity, explanation, actions=None
):
    write_project_log(
        project_id, "WARNING", activity, explanation,
        actions=actions
    )


def project_log_error(
    project_id, activity, explanation,
    causes=None, actions=None, exception=None
):
    write_project_log(
        project_id, "ERROR", activity, explanation,
        causes=causes, actions=actions, exception=exception
    )


def project_log_exception(
    project_id, activity, exception, explanation, actions=None
):
    technical_details = "".join(
        traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        )
    )

    project_log_error(
        project_id=project_id,
        activity=activity,
        explanation=explanation,
        causes=[
            "Terjadi kesalahan saat pemeriksaan website.",
            "Lihat DETAIL TEKNIS untuk informasi error."
        ],
        actions=actions or [
            "Baca Project Log terbaru.",
            "Periksa kembali konfigurasi project.",
            "Jika belum terselesaikan, kirim log kepada developer."
        ],
        exception=technical_details
    )
