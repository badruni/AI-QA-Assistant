"""Project-scoped evidence registration and integrity helpers."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from core.project_manager import PROJECTS_DIR, get_project, validate_project_id


_INDEX_NAME = "evidence_index.json"
_ALLOWED_TYPES = {"screenshot", "attachment"}
_SENSITIVE_PARTS = (
    "password", "passwd", "token", "secret", "cookie",
    "credential", "authorization", "api_key", "apikey",
)


def _safe_url(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return "[URL_REDACTED]"
        host = parsed.hostname
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme.lower(), host, parsed.path, "", ""))
    except ValueError:
        return "[URL_REDACTED]"


def _safe_metadata(value, key=None):
    if key is not None:
        normalized = str(key).lower().replace("-", "_")
        if any(part in normalized for part in _SENSITIVE_PARTS):
            return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(item_key): _safe_metadata(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe_metadata(item, key) for item in value]
    if isinstance(value, Path):
        return value.name
    if isinstance(value, str):
        if key and (key.lower().endswith("_url") or key.lower() == "url"):
            return _safe_url(value)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ValueError("Metadata evidence hanya boleh berisi data JSON sederhana.")


def _project_evidence_dir(project_id):
    validate_project_id(project_id)
    get_project(project_id)
    project_dir = (PROJECTS_DIR / project_id).resolve()
    evidence_dir = project_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return project_dir, evidence_dir.resolve()


def _load_index(index_path, project_id):
    if not index_path.exists():
        return {
            "schema_version": 1,
            "project_id": project_id,
            "evidence": [],
        }
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Evidence index tidak dapat dibaca; file tidak diubah.") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("project_id") != project_id
        or not isinstance(payload.get("evidence"), list)
    ):
        raise ValueError("Struktur atau identitas evidence index tidak valid.")
    return payload


def _write_index_atomic(index_path, payload):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=index_path.parent,
            prefix=".evidence_index_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, index_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def register_evidence(
    project_id,
    file_path,
    evidence_type,
    source,
    page_url=None,
    title="",
    related_finding_ids=(),
    metadata=None,
):
    """Register an existing file located inside this project's evidence folder."""
    if evidence_type not in _ALLOWED_TYPES:
        raise ValueError("evidence_type harus 'screenshot' atau 'attachment'.")
    if not isinstance(source, str) or not source.strip() or len(source) > 64:
        raise ValueError("source wajib berupa teks 1-64 karakter.")
    if not isinstance(title, str):
        raise ValueError("title harus berupa teks.")
    if page_url is not None and not isinstance(page_url, str):
        raise ValueError("page_url harus berupa teks atau None.")
    if not isinstance(related_finding_ids, (list, tuple)):
        raise ValueError("related_finding_ids harus berupa list atau tuple.")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata harus berupa dictionary.")

    project_dir, evidence_dir = _project_evidence_dir(project_id)
    original_path = Path(file_path)
    if original_path.is_symlink():
        raise ValueError("Symlink tidak diizinkan sebagai evidence.")
    candidate = original_path.resolve()
    try:
        relative_path = candidate.relative_to(evidence_dir)
    except ValueError:
        raise ValueError("File evidence harus berada di folder evidence proyek.") from None
    if not candidate.is_file():
        raise FileNotFoundError("File evidence tidak ditemukan.")

    digest = hashlib.sha256()
    with candidate.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    finding_ids = []
    for finding_id in related_finding_ids:
        if not isinstance(finding_id, str) or not finding_id.strip():
            raise ValueError("Setiap finding ID harus berupa teks non-kosong.")
        finding_ids.append(finding_id.strip())

    timestamp = datetime.now(timezone.utc)
    record = {
        "evidence_id": f"EV-{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}",
        "project_id": project_id,
        "evidence_type": evidence_type,
        "source": source.strip(),
        "title": title.strip(),
        "page_url": _safe_url(page_url) if page_url else None,
        "file_path": relative_path.as_posix(),
        "file_size": candidate.stat().st_size,
        "sha256": digest.hexdigest(),
        "created_at": timestamp.isoformat(),
        "related_finding_ids": finding_ids,
        "metadata": _safe_metadata(metadata or {}),
    }

    index_path = evidence_dir / _INDEX_NAME
    payload = _load_index(index_path, project_id)
    if any(item.get("evidence_id") == record["evidence_id"] for item in payload["evidence"]):
        raise RuntimeError("Evidence ID duplikat; silakan ulangi registrasi.")
    payload["evidence"].append(record)
    _write_index_atomic(index_path, payload)
    return record


def list_evidence(project_id):
    """Return registered evidence metadata without modifying stored files."""
    _, evidence_dir = _project_evidence_dir(project_id)
    payload = _load_index(evidence_dir / _INDEX_NAME, project_id)
    return tuple(payload["evidence"])


def verify_evidence(project_id, evidence_id):
    """Verify that the indexed file still exists and matches its SHA-256."""
    _, evidence_dir = _project_evidence_dir(project_id)
    payload = _load_index(evidence_dir / _INDEX_NAME, project_id)
    record = next(
        (item for item in payload["evidence"] if item.get("evidence_id") == evidence_id),
        None,
    )
    if record is None:
        raise KeyError("Evidence ID tidak ditemukan.")
    candidate = (evidence_dir / record["file_path"]).resolve()
    try:
        candidate.relative_to(evidence_dir)
    except ValueError:
        return False
    if not candidate.is_file() or candidate.is_symlink():
        return False
    digest = hashlib.sha256()
    with candidate.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == record.get("sha256")
