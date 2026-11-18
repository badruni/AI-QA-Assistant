from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from core.project_manager import PROJECTS_DIR, get_project, validate_project_id


_SENSITIVE_KEY_PARTS = (
    "password", "passwd", "token", "secret", "cookie",
    "credential", "authorization", "api_key", "apikey",
)


# Hanya metrik inspeksi yang dikenal yang dikecualikan dari redaksi.
_SAFE_METRIC_KEYS = {
    "navigation_count",
    "form_count",
    "card_count",
    "link_count",
    "button_count",
    "input_count",
    "image_count",
    "links_without_href",
    "links_without_name",
    "buttons_without_name",
    "inputs_without_label",
    "images_without_alt",
    "password_fields",
    "otp_fields",
    "login_forms",
}


def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")

    if normalized in _SAFE_METRIC_KEYS:
        return False

    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)

def _safe_url(value):
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return "[URL_REDACTED]"
        host = parsed.hostname
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except (TypeError, ValueError):
        return "[URL_REDACTED]"


def _to_json_safe(value, project_dir, key=None):
    if key is not None and _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_json_safe(
                getattr(value, item.name), project_dir, item.name
            )
            for item in fields(value)
        }
    if isinstance(value, dict):
        return {
            str(item_key): _to_json_safe(item_value, project_dir, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item, project_dir, key) for item in value]
    if isinstance(value, Path):
        try:
            return value.resolve().relative_to(project_dir.resolve()).as_posix()
        except (OSError, ValueError):
            return value.name
    if isinstance(value, str):
        if key and (key.lower().endswith("_url") or key.lower() == "url"):
            return _safe_url(value)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def save_inspection_report(project_id, inspection_type, result):
    # Simpan hasil inspeksi ke JSON unik secara atomik.
    validate_project_id(project_id)
    if inspection_type not in ("generic_uat", "authentication_discovery"):
        raise ValueError("Jenis inspeksi laporan tidak dikenal.")
    get_project(project_id)

    project_dir = PROJECTS_DIR / project_id
    reports_dir = project_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc)
    payload = {
        "schema_version": 1,
        "inspection_type": inspection_type,
        "generated_at": timestamp.isoformat(),
        "project_id": project_id,
        "result": _to_json_safe(result, project_dir),
    }

    stamp = timestamp.strftime("%Y%m%dT%H%M%S_%fZ")
    report_path = reports_dir / (
        f"{inspection_type}_{stamp}_{uuid4().hex[:8]}.json"
    )
    temporary_path = report_path.with_suffix(".json.tmp")
    try:
        with temporary_path.open("x", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
        temporary_path.replace(report_path)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return report_path
