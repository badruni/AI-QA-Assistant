"""Versioned, project-isolated storage for QA documentation drafts."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from core.project_manager import PROJECTS_DIR, get_project, validate_project_id


DOCUMENT_TYPES = ("UAT", "User_Guide_Web", "User_Guide_CMS")
DOCUMENT_STATUSES = ("DRAFT", "NEEDS_REVIEW", "BLOCKED", "APPROVED")
_DOCUMENT_ID_PATTERN = re.compile(r"^DOC-[A-Za-z0-9_-]{1,80}$")
_SENSITIVE_PARTS = (
    "password", "passwd", "token", "secret", "cookie",
    "credential", "authorization", "api_key", "apikey",
)


def _now():
    return datetime.now(timezone.utc).isoformat()


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


def _safe_value(value, key=None):
    if key is not None:
        normalized = str(key).lower().replace("-", "_")
        if any(part in normalized for part in _SENSITIVE_PARTS):
            return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(k): _safe_value(v, str(k))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe_value(item, key) for item in value]
    if isinstance(value, Path):
        return value.name
    if isinstance(value, str):
        if key and (key.lower().endswith("_url") or key.lower() == "url"):
            return _safe_url(value)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise TypeError(
        f"Tipe data tidak didukung untuk dokumen: {type(value).__name__}"
    )


def _json_bytes(payload):
    return (
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _write_new_json(path, payload):
    """Create a JSON file without overwriting an existing version."""
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(_json_bytes(payload))
        # Hard-link creation is not portable on all Windows filesystems;
        # destination is checked immediately before atomic rename.
        if path.exists():
            raise FileExistsError(f"File dokumen sudah tersedia: {path.name}")
        temporary.rename(path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _atomic_replace_json(path, payload):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(_json_bytes(payload))
        temporary.replace(path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _project_dir(project_id):
    validate_project_id(project_id)
    get_project(project_id)
    root = PROJECTS_DIR.resolve()
    project_path = PROJECTS_DIR / project_id
    if project_path.is_symlink():
        raise ValueError("Folder proyek tidak boleh berupa symbolic link.")
    project_dir = project_path.resolve()
    try:
        project_dir.relative_to(root)
    except ValueError:
        raise ValueError("Path proyek berada di luar direktori proyek.") from None
    return project_dir


def _document_dir(project_id, document_id):
    if not isinstance(document_id, str) or not _DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise ValueError("Document ID tidak valid.")
    project_dir = _project_dir(project_id)
    docs_root = project_dir / "documentation"
    if docs_root.is_symlink():
        raise ValueError("Folder documentation tidak boleh berupa symbolic link.")
    target = docs_root / document_id
    resolved_root = docs_root.resolve()
    resolved_target = target.resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise ValueError("Path dokumen berada di luar folder documentation.") from None
    if target.is_symlink():
        raise ValueError("Folder dokumen tidak boleh berupa symbolic link.")
    return target


def _load_manifest(project_id, document_id):
    folder = _document_dir(project_id, document_id)
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Dokumen tidak ditemukan: {document_id}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("Manifest dokumen rusak atau tidak dapat dibaca.") from None
    if manifest.get("project_id") != project_id or manifest.get("document_id") != document_id:
        raise ValueError("Identitas dokumen tidak sesuai dengan folder.")
    return folder, manifest


def _validate_type(document_type):
    if document_type not in DOCUMENT_TYPES:
        raise ValueError("Jenis dokumen tidak dikenal.")
    return document_type


def _validate_status(status, allow_approved=False):
    allowed = DOCUMENT_STATUSES if allow_approved else (
        "DRAFT", "NEEDS_REVIEW", "BLOCKED"
    )
    if status not in allowed:
        raise ValueError("Status dokumen tidak valid untuk operasi ini.")
    return status


def _prepare_version(content, status, source_summary, unverified_sections):
    if not isinstance(content, (dict, list)):
        raise ValueError("Content dokumen harus berupa object atau array JSON.")
    if not isinstance(unverified_sections, list):
        raise ValueError("unverified_sections harus berupa list.")
    if not all(isinstance(item, str) for item in unverified_sections):
        raise ValueError("Setiap unverified section harus berupa teks.")
    safe_content = _safe_value(content)
    safe_sources = _safe_value(source_summary or {})
    safe_unverified = _safe_value(unverified_sections)
    payload = {
        "schema_version": 1,
        "status": _validate_status(status),
        "created_at": _now(),
        "content": safe_content,
        "source_summary": safe_sources,
        "unverified_sections": safe_unverified,
    }
    payload["content_sha256"] = hashlib.sha256(
        _json_bytes({
            "content": safe_content,
            "source_summary": safe_sources,
            "unverified_sections": safe_unverified,
        })
    ).hexdigest()
    return payload


def create_document(
    project_id,
    document_type,
    title,
    content,
    status="DRAFT",
    source_summary=None,
    unverified_sections=None,
):
    """Create a new document and its first immutable version."""
    project_dir = _project_dir(project_id)
    document_type = _validate_type(document_type)
    _validate_status(status)
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Judul dokumen wajib diisi.")

    docs_root = project_dir / "documentation"
    docs_root.mkdir(parents=True, exist_ok=True)
    if docs_root.is_symlink():
        raise ValueError("Folder documentation tidak boleh berupa symbolic link.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    document_id = f"DOC-{timestamp}-{uuid4().hex[:8]}"
    folder = docs_root / document_id
    folder.mkdir()
    try:
        version = _prepare_version(
            content, status, source_summary, unverified_sections or []
        )
        version_name = "v0001.json"
        _write_new_json(folder / version_name, version)
        manifest = {
            "schema_version": 1,
            "project_id": project_id,
            "document_id": document_id,
            "document_type": document_type,
            "title": title.strip(),
            "created_at": _now(),
            "updated_at": _now(),
            "current_version": 1,
            "versions": [{
                "version": 1,
                "file": version_name,
                "status": version["status"],
                "content_sha256": version["content_sha256"],
                "created_at": version["created_at"],
                "approved_at": None,
            }],
        }
        _write_new_json(folder / "manifest.json", manifest)
    except Exception:
        # Only remove the uniquely created document folder from this call.
        import shutil
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return get_document(project_id, document_id)


def create_version(
    project_id,
    document_id,
    content,
    status="DRAFT",
    source_summary=None,
    unverified_sections=None,
):
    """Append a new version; existing version files are never overwritten."""
    folder, manifest = _load_manifest(project_id, document_id)
    current = manifest["versions"][-1]
    if current["status"] != "APPROVED":
        raise ValueError(
            "Versi aktif harus disetujui terlebih dahulu sebelum membuat versi baru."
        )
    version_number = max(item["version"] for item in manifest["versions"]) + 1
    version = _prepare_version(
        content, status, source_summary, unverified_sections or []
    )
    version_name = f"v{version_number:04d}.json"
    _write_new_json(folder / version_name, version)
    manifest["versions"].append({
        "version": version_number,
        "file": version_name,
        "status": version["status"],
        "content_sha256": version["content_sha256"],
        "created_at": version["created_at"],
        "approved_at": None,
    })
    manifest["current_version"] = version_number
    manifest["updated_at"] = _now()
    _atomic_replace_json(folder / "manifest.json", manifest)
    return get_document(project_id, document_id)


def approve_document(project_id, document_id):
    """Explicitly approve the current version after all review flags are cleared."""
    folder, manifest = _load_manifest(project_id, document_id)
    version_number = manifest["current_version"]
    version_path = folder / f"v{version_number:04d}.json"
    try:
        version = json.loads(version_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("Versi dokumen tidak dapat dibaca.") from None

    if version.get("status") == "APPROVED":
        raise ValueError("Versi dokumen ini sudah disetujui.")
    if version.get("status") == "BLOCKED":
        raise ValueError("Dokumen berstatus BLOCKED tidak dapat disetujui.")
    if version.get("unverified_sections"):
        raise ValueError(
            "Dokumen masih memiliki bagian yang belum diverifikasi."
        )

    version["status"] = "APPROVED"
    version["approved_at"] = _now()
    _atomic_replace_json(version_path, version)
    entry = manifest["versions"][-1]
    entry["status"] = "APPROVED"
    entry["approved_at"] = version["approved_at"]
    manifest["updated_at"] = _now()
    _atomic_replace_json(folder / "manifest.json", manifest)
    return get_document(project_id, document_id)


def get_document(project_id, document_id):
    """Return manifest and current version content."""
    folder, manifest = _load_manifest(project_id, document_id)
    version_number = manifest.get("current_version")
    version_name = f"v{version_number:04d}.json"
    try:
        version = json.loads((folder / version_name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("Versi dokumen aktif rusak atau tidak dapat dibaca.") from None
    return {"manifest": manifest, "version": version}


def list_documents(project_id, document_type=None):
    """List documents for one project, optionally filtered by type."""
    project_dir = _project_dir(project_id)
    if document_type is not None:
        _validate_type(document_type)
    docs_root = project_dir / "documentation"
    if not docs_root.exists():
        return []
    if docs_root.is_symlink():
        raise ValueError("Folder documentation tidak boleh berupa symbolic link.")
    results = []
    for folder in sorted(docs_root.iterdir(), key=lambda item: item.name):
        if not folder.is_dir() or folder.is_symlink():
            continue
        if not _DOCUMENT_ID_PATTERN.fullmatch(folder.name):
            continue
        try:
            _, manifest = _load_manifest(project_id, folder.name)
        except (FileNotFoundError, ValueError):
            continue
        if document_type is None or manifest.get("document_type") == document_type:
            results.append({
                "document_id": manifest["document_id"],
                "document_type": manifest["document_type"],
                "title": manifest["title"],
                "current_version": manifest["current_version"],
                "status": manifest["versions"][-1]["status"],
                "updated_at": manifest["updated_at"],
            })
    return results
