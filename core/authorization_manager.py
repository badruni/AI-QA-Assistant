"""Project-scoped authorization records for safe QA scanning.

This module records permission only. It never configures Cloudflare/WAF or
bypasses access controls; callers must stop when access remains restricted.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from core import project_manager
from core.path_safety import resolve_project_path
from core.security import sanitize_text

SCHEMA_VERSION = 1
AUTHORIZATION_DIRECTORY = "authorization"
AUTHORIZATION_FILE = "authorization.json"


def _now():
    return datetime.now(timezone.utc)


def _parse_datetime(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} wajib berupa tanggal ISO 8601.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field_name} bukan tanggal ISO 8601 yang valid.") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} harus menyertakan zona waktu.")
    return parsed.astimezone(timezone.utc)


def _safe_text(value, field_name, max_length=500, required=True):
    if not isinstance(value, str):
        raise ValueError(f"{field_name} harus berupa teks.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{field_name} wajib diisi.")
    value = sanitize_text(value)
    if len(value) > max_length:
        raise ValueError(f"{field_name} maksimal {max_length} karakter.")
    return value


def _validate_scope(scope):
    if not isinstance(scope, (list, tuple)) or not scope:
        raise ValueError("Scope otorisasi harus berupa daftar yang tidak kosong.")
    result = []
    for item in scope:
        item = _safe_text(item, "Scope", max_length=100)
        if item not in result:
            result.append(item)
    return result


def _validate_target_url(target_url):
    normalized = project_manager.validate_url(target_url)
    parsed = urlsplit(normalized)
    if parsed.query or parsed.fragment:
        raise ValueError("Target otorisasi tidak boleh mengandung query atau fragment URL.")
    return normalized


def _authorization_path(project_id):
    project_dir = project_manager.get_project_directory(project_id)
    directory = resolve_project_path(project_dir, AUTHORIZATION_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    return resolve_project_path(project_dir, AUTHORIZATION_DIRECTORY, AUTHORIZATION_FILE)


def _empty_document(project_id):
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "current": None,
        "history": [],
    }


def _read_document(project_id):
    path = _authorization_path(project_id)
    if not path.exists():
        return _empty_document(project_id)
    with path.open("r", encoding="utf-8") as file:
        document = json.load(file)
    if not isinstance(document, dict):
        raise ValueError("Format data otorisasi tidak valid.")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Versi data otorisasi tidak didukung.")
    if document.get("project_id") != project_id:
        raise ValueError("Identitas proyek pada data otorisasi tidak sesuai.")
    if not isinstance(document.get("history"), list):
        raise ValueError("Riwayat otorisasi tidak valid.")
    if document.get("current") is not None and not isinstance(document["current"], dict):
        raise ValueError("Data otorisasi aktif tidak valid.")
    return document


def _atomic_write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".authorization_", suffix=".tmp", delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(document, file, indent=4, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def create_authorization(
    project_id, target_url, authorized_by, scope, expires_at,
    admin_access_confirmed=False
):
    """Create/replace authorization and append an audit event."""
    project_manager.validate_project_id(project_id)
    target_url = _validate_target_url(target_url)
    authorized_by = _safe_text(authorized_by, "Nama pemberi otorisasi")
    scope = _validate_scope(scope)
    expiry = _parse_datetime(expires_at, "Masa berlaku")
    now = _now()
    if expiry <= now:
        raise ValueError("Masa berlaku otorisasi harus berada di masa depan.")
    if not isinstance(admin_access_confirmed, bool):
        raise ValueError("Konfirmasi administrator harus bernilai boolean.")

    document = _read_document(project_id)
    previous = document.get("current")
    record = {
        "authorization_id": os.urandom(16).hex(),
        "status": "active",
        "target_url": target_url,
        "authorized_by": authorized_by,
        "scope": scope,
        "created_at": now.isoformat(),
        "expires_at": expiry.isoformat(),
        "admin_access_confirmed": admin_access_confirmed,
    }
    document["current"] = record
    document["history"].append({
        "event": "created" if previous is None else "replaced",
        "timestamp": now.isoformat(),
        "authorization_id": record["authorization_id"],
        "previous_authorization_id": (
            previous.get("authorization_id") if isinstance(previous, dict) else None
        ),
        "authorized_by": authorized_by,
    })
    _atomic_write(_authorization_path(project_id), document)
    return record.copy()


def get_authorization(project_id):
    """Return a copy of the current authorization, or None."""
    project_manager.validate_project_id(project_id)
    current = _read_document(project_id).get("current")
    return current.copy() if isinstance(current, dict) else None


def list_authorization_history(project_id):
    """Return a copy of this project's authorization audit history."""
    project_manager.validate_project_id(project_id)
    return [item.copy() for item in _read_document(project_id)["history"]]


def validate_authorization(
    project_id, target_url, required_scope=None, require_admin_confirmation=False
):
    """Return (allowed, reason) for the requested target and scope."""
    project_manager.validate_project_id(project_id)
    try:
        target_url = _validate_target_url(target_url)
    except ValueError:
        return False, "invalid_target"
    if not isinstance(require_admin_confirmation, bool):
        return False, "invalid_admin_confirmation_requirement"

    current = get_authorization(project_id)
    if current is None:
        return False, "authorization_missing"
    if current.get("status") != "active":
        return False, "authorization_inactive"
    try:
        expiry = _parse_datetime(current.get("expires_at"), "Masa berlaku")
    except ValueError:
        return False, "authorization_invalid"
    if expiry <= _now():
        return False, "authorization_expired"
    if current.get("target_url") != target_url:
        return False, "target_not_authorized"
    if require_admin_confirmation and current.get("admin_access_confirmed") is not True:
        return False, "admin_access_not_confirmed"

    if required_scope is not None:
        required = [required_scope] if isinstance(required_scope, str) else required_scope
        if not isinstance(required, (list, tuple)):
            return False, "invalid_required_scope"
        granted = current.get("scope", [])
        if not isinstance(granted, list) or any(item not in granted for item in required):
            return False, "scope_not_authorized"
    return True, "authorized"


def revoke_authorization(project_id, revoked_by, reason=""):
    """Revoke active authorization and append an audit event."""
    project_manager.validate_project_id(project_id)
    revoked_by = _safe_text(revoked_by, "Nama pencabut otorisasi")
    safe_reason = _safe_text(reason, "Alasan pencabutan", max_length=500, required=False)
    document = _read_document(project_id)
    current = document.get("current")
    if not isinstance(current, dict) or current.get("status") != "active":
        raise ValueError("Tidak ada otorisasi aktif yang dapat dicabut.")

    now = _now()
    current.update({
        "status": "revoked",
        "revoked_at": now.isoformat(),
        "revoked_by": revoked_by,
        "revocation_reason": safe_reason,
    })
    document["history"].append({
        "event": "revoked",
        "timestamp": now.isoformat(),
        "authorization_id": current.get("authorization_id"),
        "revoked_by": revoked_by,
        "reason": safe_reason,
    })
    _atomic_write(_authorization_path(project_id), document)
    return current.copy()
