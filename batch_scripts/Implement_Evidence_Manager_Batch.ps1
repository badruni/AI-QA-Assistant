#requires -Version 5.1
$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$RequiredPaths = @(".git", "core", "modules", "tests", "docs")
foreach ($item in $RequiredPaths) {
    if (-not (Test-Path (Join-Path $ProjectRoot $item))) {
        throw "Jalankan script dari root proyek. Tidak ditemukan: $item"
    }
}

$NewFiles = @(
    "core/evidence_manager.py",
    "tests/test_evidence_manager.py"
)
foreach ($file in $NewFiles) {
    if (Test-Path (Join-Path $ProjectRoot $file)) {
        throw "File sudah ada; script tidak akan menimpa: $file"
    }
}

$BackupName = "before_evidence_manager_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path $ProjectRoot ("backups\" + $BackupName)
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$Touched = @(
    "docs/PROJECT_SETUP_GUIDE.md",
    "docs/PORTABLE_SETUP_GUIDE.md"
)
foreach ($file in $Touched) {
    $source = Join-Path $ProjectRoot $file
    if (-not (Test-Path $source)) {
        throw "Dokumentasi wajib tidak ditemukan: $file"
    }
    $target = Join-Path $BackupDir $file
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
    Copy-Item $source $target
}

$EvidenceManager = @'
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
'@

$EvidenceTests = @'
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import evidence_manager, project_manager


class EvidenceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-TEST"
        self.project_dir = self.root / self.project_id
        (self.project_dir / "evidence" / "screenshots").mkdir(parents=True)
        (self.project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.project_patch = patch.object(
            evidence_manager, "PROJECTS_DIR", self.root
        )
        self.project_patch.start()
        self.addCleanup(self.project_patch.stop)
        self.manager_patch = patch.object(
            project_manager, "PROJECTS_DIR", self.root
        )
        self.manager_patch.start()
        self.addCleanup(self.manager_patch.stop)
        self.image = self.project_dir / "evidence" / "screenshots" / "shot.png"
        self.image.write_bytes(b"test-image-bytes")

    def test_registers_metadata_and_relative_path(self):
        record = evidence_manager.register_evidence(
            self.project_id,
            self.image,
            "screenshot",
            "generic_uat",
            page_url="https://example.test/a?token=secret#section",
            related_finding_ids=["F-001"],
            metadata={"password": "must-not-leak", "viewport": "1365x768"},
        )
        self.assertTrue(record["evidence_id"].startswith("EV-"))
        self.assertEqual(record["file_path"], "screenshots/shot.png")
        self.assertEqual(record["page_url"], "https://example.test/a")
        self.assertEqual(record["metadata"]["password"], "[REDACTED]")
        self.assertEqual(record["related_finding_ids"], ["F-001"])

    def test_index_is_written_and_listing_returns_record(self):
        record = evidence_manager.register_evidence(
            self.project_id, self.image, "screenshot", "website_discovery"
        )
        index = self.project_dir / "evidence" / "evidence_index.json"
        self.assertTrue(index.is_file())
        payload = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(payload["project_id"], self.project_id)
        self.assertEqual(len(evidence_manager.list_evidence(self.project_id)), 1)
        self.assertEqual(payload["evidence"][0]["evidence_id"], record["evidence_id"])

    def test_verifies_integrity_and_detects_modified_file(self):
        record = evidence_manager.register_evidence(
            self.project_id, self.image, "screenshot", "generic_uat"
        )
        self.assertTrue(evidence_manager.verify_evidence(
            self.project_id, record["evidence_id"]
        ))
        self.image.write_bytes(b"changed")
        self.assertFalse(evidence_manager.verify_evidence(
            self.project_id, record["evidence_id"]
        ))

    def test_rejects_file_outside_project_evidence(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"not evidence")
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, outside, "screenshot", "generic_uat"
            )

    def test_rejects_missing_file(self):
        missing = self.project_dir / "evidence" / "screenshots" / "missing.png"
        with self.assertRaises(FileNotFoundError):
            evidence_manager.register_evidence(
                self.project_id, missing, "screenshot", "generic_uat"
            )

    def test_rejects_unknown_evidence_type(self):
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, self.image, "video", "generic_uat"
            )

    def test_rejects_invalid_project_id(self):
        with self.assertRaises(ValueError):
            evidence_manager.list_evidence("../bad")

    def test_does_not_overwrite_corrupt_index(self):
        index = self.project_dir / "evidence" / "evidence_index.json"
        index.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            evidence_manager.register_evidence(
                self.project_id, self.image, "screenshot", "generic_uat"
            )
        self.assertEqual(index.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
'@

Set-Content -Path (Join-Path $ProjectRoot "core/evidence_manager.py") -Value $EvidenceManager -Encoding UTF8
Set-Content -Path (Join-Path $ProjectRoot "tests/test_evidence_manager.py") -Value $EvidenceTests -Encoding UTF8

$ProjectDoc = Join-Path $ProjectRoot "docs/PROJECT_SETUP_GUIDE.md"
$PortableDoc = Join-Path $ProjectRoot "docs/PORTABLE_SETUP_GUIDE.md"

$ProjectSection = @'

## Evidence Management

Evidence disimpan terpisah per proyek di `projects/<project_id>/evidence/`.
Modul `core/evidence_manager.py` menyediakan registrasi metadata evidence,
indeks `evidence_index.json`, path relatif, SHA-256, daftar evidence, dan
verifikasi integritas file. Jenis file yang didukung saat ini adalah screenshot
dan attachment. File harus sudah ada dan berada di dalam folder evidence proyek.
Metadata sensitif seperti password, token, cookie, credential, authorization,
dan API key disamarkan. Modul ini belum mengubah alur pembuatan screenshot
Discovery maupun Generic UAT; integrasi keduanya dilakukan pada tahap berikutnya.
'@

$PortableSection = @'

## Evidence Management

Evidence Management menyimpan metadata evidence per proyek pada
`evidence/evidence_index.json`. File evidence tetap berada di folder proyek dan
tidak dipindahkan oleh modul registrasi. Indeks mencatat ID unik, sumber, jenis,
waktu UTC, path relatif, ukuran file, SHA-256, URL halaman yang telah disanitasi,
dan relasi finding bila tersedia. Jalankan pengujian dengan:
`python -m unittest tests.test_evidence_manager -v`.
'@

foreach ($entry in @(
    @{ Path = $ProjectDoc; Marker = "## Evidence Management"; Section = $ProjectSection },
    @{ Path = $PortableDoc; Marker = "## Evidence Management"; Section = $PortableSection }
)) {
    $content = [System.IO.File]::ReadAllText($entry.Path)
    if (-not $content.Contains($entry.Marker)) {
        $content = $content.TrimEnd() + "`r`n" + $entry.Section + "`r`n"
        [System.IO.File]::WriteAllText(
            $entry.Path,
            $content,
            [System.Text.UTF8Encoding]::new($false)
        )
    }
}

Write-Host "`n=== FOCUSED TESTS ==="
& .\.venv-scanner\Scripts\python.exe -m unittest tests.test_evidence_manager -v
if ($LASTEXITCODE -ne 0) { throw "Evidence Manager tests gagal. Backup: $BackupDir" }

Write-Host "`n=== COMPILE CHECK ==="
& .\.venv-scanner\Scripts\python.exe -m py_compile core/evidence_manager.py tests/test_evidence_manager.py
if ($LASTEXITCODE -ne 0) { throw "Compile check gagal. Backup: $BackupDir" }

Write-Host "`n=== DIFF CHECK ==="
git --no-pager diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup: $BackupDir" }

Write-Host "`nEvidence Management batch tahap 1 selesai."
Write-Host "Backup: $BackupDir"
Write-Host "File baru: core/evidence_manager.py, tests/test_evidence_manager.py"
Write-Host "Catatan: integrasi ke Discovery/UAT belum dilakukan."
