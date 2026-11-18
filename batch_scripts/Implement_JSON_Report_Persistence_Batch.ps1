#requires -Version 5.1
$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$RequiredFiles = @(
    "agent.py",
    "core\project_manager.py",
    "modules\generic_uat_inspection.py",
    "modules\authentication_discovery.py",
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path (Join-Path $ProjectRoot $File) -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File. Jalankan script dari root repository."
    }
}

$GitStatus = @(git status --porcelain)
if ($LASTEXITCODE -ne 0) { throw "Tidak dapat membaca status Git." }

# Izinkan hanya file batch ini yang berstatus untracked.
# Perubahan lain tetap menghentikan proses agar tidak tertimpa.
$UnexpectedChanges = @(
    $GitStatus | Where-Object {
        $_ -notmatch '^\?\? Implement_JSON_Report_Persistence_Batch\.ps1$'
    }
)
if ($UnexpectedChanges.Count -gt 0) {
    Write-Host "Perubahan Git selain batch script terdeteksi:" -ForegroundColor Yellow
    $UnexpectedChanges | ForEach-Object { Write-Host $_ }
    throw "Working tree memiliki perubahan lain. Amankan atau tinjau terlebih dahulu."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "backups\before_json_report_persistence_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$BackupFiles = @(
    "agent.py",
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $BackupFiles) {
    $Destination = Join-Path $BackupDir $File
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item (Join-Path $ProjectRoot $File) $Destination
}

$PythonScript = @'
from pathlib import Path

root = Path.cwd()

report_manager = r"""from dataclasses import fields, is_dataclass
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


def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")
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
            file.write("\\n")
        temporary_path.replace(report_path)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return report_path
"""

test_module = r"""import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import report_manager


class ReportManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "QA-TEST"
        project_dir = self.root / self.project_id
        (project_dir / "reports").mkdir(parents=True)
        (project_dir / "project_config.json").write_text(
            json.dumps({"project_id": self.project_id}), encoding="utf-8"
        )
        self.project_dir = project_dir
        self.projects_patch = patch.object(report_manager, "PROJECTS_DIR", self.root)
        self.projects_patch.start()
        self.addCleanup(self.projects_patch.stop)

    def test_writes_unique_json_report_and_sanitizes_url(self):
        result = {
            "status": "PASSED",
            "pages": [{
                "page_url": "https://example.test/a?token=secret#part",
                "access_token": "should-not-leak",
            }],
        }
        first = report_manager.save_inspection_report(
            self.project_id, "generic_uat", result
        )
        second = report_manager.save_inspection_report(
            self.project_id, "generic_uat", result
        )
        self.assertTrue(first.is_file())
        self.assertTrue(second.is_file())
        self.assertNotEqual(first, second)
        payload = json.loads(first.read_text(encoding="utf-8"))
        page = payload["result"]["pages"][0]
        self.assertEqual(page["page_url"], "https://example.test/a")
        self.assertEqual(page["access_token"], "[REDACTED]")

    def test_path_is_stored_relative_to_project(self):
        evidence = self.project_dir / "evidence" / "screenshots" / "shot.png"
        evidence.parent.mkdir(parents=True)
        evidence.write_bytes(b"image")
        path = report_manager.save_inspection_report(
            self.project_id,
            "authentication_discovery",
            {"evidence_path": evidence},
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["result"]["evidence_path"],
            "evidence/screenshots/shot.png",
        )

    def test_rejects_unknown_inspection_type(self):
        with self.assertRaises(ValueError):
            report_manager.save_inspection_report(
                self.project_id, "other", {}
            )

    def test_rejects_invalid_project_id(self):
        with self.assertRaises(ValueError):
            report_manager.save_inspection_report("../bad", "generic_uat", {})


if __name__ == "__main__":
    unittest.main()
"""

module_path = root / "core" / "report_manager.py"
test_path = root / "tests" / "test_report_manager.py"
if module_path.exists() or test_path.exists():
    raise SystemExit(
        "report_manager.py atau test_report_manager.py sudah ada; "
        "script tidak akan menimpa file."
    )
module_path.write_text(report_manager, encoding="utf-8")
test_path.write_text(test_module, encoding="utf-8")

agent_path = root / "agent.py"
agent = agent_path.read_text(encoding="utf-8")
import_anchor = "from core.result_status import ResultStatus\n"
if agent.count(import_anchor) != 1:
    raise SystemExit("Import ResultStatus tidak ditemukan secara unik.")
agent = agent.replace(
    import_anchor,
    import_anchor + "from core.report_manager import save_inspection_report\n",
    1,
)

auth_anchor = "        result = inspect_authentication(config, discovery)\n"
auth_replacement = """        result = inspect_authentication(config, discovery)
        try:
            report_path = save_inspection_report(
                active_project_id, "authentication_discovery", result
            )
            print("Laporan JSON :", report_path)
        except Exception as report_error:
            print("[WARNING] Laporan Authentication Discovery gagal disimpan:", report_error)
            log_warning(
                "Authentication Discovery",
                "Hasil inspeksi tersedia, tetapi laporan JSON gagal disimpan."
            )
"""
if agent.count(auth_anchor) != 1:
    raise SystemExit("Titik integrasi Authentication Discovery tidak ditemukan.")
agent = agent.replace(auth_anchor, auth_replacement, 1)

uat_anchor = "        result = inspect_generic_uat(config, discovery)\n"
uat_replacement = """        result = inspect_generic_uat(config, discovery)
        try:
            report_path = save_inspection_report(
                active_project_id, "generic_uat", result
            )
            print("Laporan JSON :", report_path)
        except Exception as report_error:
            print("[WARNING] Laporan Generic UAT gagal disimpan:", report_error)
            log_warning(
                "Generic UAT Inspection",
                "Hasil inspeksi tersedia, tetapi laporan JSON gagal disimpan."
            )
"""
if agent.count(uat_anchor) != 1:
    raise SystemExit("Titik integrasi Generic UAT tidak ditemukan.")
agent = agent.replace(uat_anchor, uat_replacement, 1)
agent_path.write_text(agent, encoding="utf-8")

doc_note = """

## Penyimpanan Laporan Inspeksi JSON

Hasil Generic UAT Inspection dan Authentication Discovery disimpan otomatis
sebagai file JSON terpisah di `projects/<PROJECT_ID>/reports/`. Setiap eksekusi
menghasilkan nama file unik sehingga laporan sebelumnya tidak ditimpa.
Laporan memuat tipe inspeksi, versi skema, waktu UTC, ID proyek, dan hasil
terstruktur. URL pada field URL disimpan tanpa query string maupun fragment.
Field yang namanya mengindikasikan password, token, secret, cookie, credential,
authorization, atau API key akan disamarkan. Screenshot tetap berada di folder
evidence dan dirujuk dengan path relatif jika berada di dalam folder proyek.
Jika penyimpanan laporan gagal, hasil inspeksi tetap ditampilkan dan aplikasi
memberikan peringatan.
"""
for relative in (
    "docs/PROJECT_SETUP_GUIDE.md",
    "docs/PORTABLE_SETUP_GUIDE.md",
):
    path = root / relative
    original = path.read_text(encoding="utf-8-sig")
    if "Penyimpanan Laporan Inspeksi JSON" not in original:
        path.write_text(
            original.rstrip() + "\n" + doc_note,
            encoding="utf-8",
        )

print("Modul laporan, unit test, integrasi agent, dan dokumentasi berhasil ditulis.")
'@

$TempPython = Join-Path $env:TEMP "implement_json_report_persistence_$Stamp.py"
Set-Content -Path $TempPython -Value $PythonScript -Encoding UTF8

try {
    & ".\.venv-scanner\Scripts\python.exe" $TempPython
    if ($LASTEXITCODE -ne 0) { throw "Tahap implementasi gagal. Periksa error Python di atas." }

    & ".\.venv-scanner\Scripts\python.exe" -m py_compile .\core\report_manager.py .\agent.py .\tests\test_report_manager.py
    if ($LASTEXITCODE -ne 0) { throw "Python compile check gagal." }

    & ".\.venv-scanner\Scripts\python.exe" -m unittest tests.test_report_manager tests.test_agent_menu_and_restriction tests.test_authentication_discovery tests.test_generic_uat_inspection -v
    if ($LASTEXITCODE -ne 0) { throw "Unit test gagal. Jangan commit; kirim output untuk diagnosis." }

    Write-Host "`n=== GIT STATUS ===" -ForegroundColor Cyan
    git status --short
    Write-Host "`nBackup tersedia di: $BackupDir" -ForegroundColor Green
    Write-Host "Implementasi dan focused tests selesai. Belum ada commit/push."
}
finally {
    Remove-Item $TempPython -Force -ErrorAction SilentlyContinue
}
