$ErrorActionPreference = "Stop"

# Jalankan dari root repository AI-QA-Assistant.
$RequiredFiles = @(
    ".\modules\frontend_scanner.py",
    ".\tests\test_evidence_integration.py",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File. Jalankan dari root repository."
    }
}

$Python = ".\.venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = ".\backups\before_frontend_evidence_integration_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$FilesToBackup = @(
    ".\modules\frontend_scanner.py",
    ".\tests\test_evidence_integration.py",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($File in $FilesToBackup) {
    $Destination = Join-Path $BackupDir $File.Substring(2)
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item $File $Destination
}
Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$PatchScript = @'
from pathlib import Path

scanner_path = Path("modules/frontend_scanner.py")
scanner = scanner_path.read_text(encoding="utf-8")

old = """from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
"""
new = """import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
"""
if scanner.count(old) != 1:
    raise SystemExit("Pola import tidak sesuai; scanner tidak diubah.")
scanner = scanner.replace(old, new, 1)

old = "from core.result_status import ResultStatus\n"
new = old + "from core.evidence_manager import register_evidence\n"
if scanner.count(old) != 1:
    raise SystemExit("Import ResultStatus tidak ditemukan secara unik.")
scanner = scanner.replace(old, new, 1)

anchor = '''PROJECTS_DIR = ROOT / "projects"


def _looks_like_waf_block_page'''
replacement = '''PROJECTS_DIR = ROOT / "projects"


def _register_screenshot_evidence(
    project_id, screenshot_path, page_url, title, metadata=None,
):
    """Register a created screenshot; registry failure must not fail inspection."""
    try:
        register_evidence(
            project_id=project_id,
            file_path=screenshot_path,
            evidence_type="screenshot",
            source="frontend_scanner",
            page_url=page_url,
            title=title or "",
            metadata=metadata or {},
        )
        return True
    except Exception:
        logging.getLogger(__name__).warning(
            "Screenshot evidence registration failed; inspection continues."
        )
        return False


def _looks_like_waf_block_page'''
if scanner.count(anchor) != 1:
    raise SystemExit("Lokasi helper tidak ditemukan secara unik.")
scanner = scanner.replace(anchor, replacement, 1)

old = """                    if screenshot_file.is_file():
                        screenshot_path = screenshot_file

                except PlaywrightError:
"""
new = """                    if screenshot_file.is_file():
                        screenshot_path = screenshot_file
                        _register_screenshot_evidence(
                            config.project_id,
                            screenshot_path,
                            final_url,
                            page_title,
                            {"inspection": "frontend_homepage"},
                        )

                except PlaywrightError:
"""
if scanner.count(old) != 1:
    raise SystemExit("Lokasi setelah pembuatan screenshot tidak ditemukan secara unik.")
scanner = scanner.replace(old, new, 1)
scanner_path.write_text(scanner, encoding="utf-8", newline="")

test_path = Path("tests/test_frontend_scanner_evidence_integration.py")
if test_path.exists():
    raise SystemExit("File test target sudah ada; tidak akan ditimpa.")

test_source = '''import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import frontend_scanner


class FrontendScannerEvidenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.screenshot = Path(self.temp.name) / "homepage.png"
        self.screenshot.write_bytes(b"verified homepage screenshot")

    def test_registers_homepage_screenshot_metadata(self):
        with patch.object(frontend_scanner, "register_evidence") as register:
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/",
                "Example Home", {"inspection": "frontend_homepage"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_HOME")
        self.assertEqual(kwargs["file_path"], self.screenshot)
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "frontend_scanner")
        self.assertEqual(kwargs["page_url"], "https://example.test/")
        self.assertEqual(kwargs["title"], "Example Home")
        self.assertEqual(kwargs["metadata"], {"inspection": "frontend_homepage"})

    def test_registration_failure_is_non_fatal(self):
        with patch.object(
            frontend_scanner, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/",
                "Example Home",
            )
        self.assertFalse(result)

    def test_empty_title_and_metadata_use_safe_defaults(self):
        with patch.object(frontend_scanner, "register_evidence") as register:
            result = frontend_scanner._register_screenshot_evidence(
                "PROJECT_HOME", self.screenshot, "https://example.test/", None,
            )
        self.assertTrue(result)
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["title"], "")
        self.assertEqual(kwargs["metadata"], {})


if __name__ == "__main__":
    unittest.main()
'''
test_path.write_text(test_source, encoding="utf-8", newline="")

for name in ("docs/PROJECT_SETUP_GUIDE.md", "docs/PORTABLE_SETUP_GUIDE.md"):
    path = Path(name)
    content = path.read_text(encoding="utf-8")
    old = "- Screenshot hasil Website Discovery dan Generic UAT didaftarkan ke `evidence/evidence_index.json` melalui"
    new = "- Screenshot hasil Frontend Homepage Scanner, Website Discovery, dan Generic UAT didaftarkan ke `evidence/evidence_index.json` melalui"
    if content.count(old) != 1:
        raise SystemExit(f"Baris dokumentasi tidak ditemukan secara unik: {name}")
    content = content.replace(old, new, 1)
    content = content.replace(
        "integrasi keduanya dilakukan pada tahap berikutnya.",
        "integrasi screenshot dilakukan setelah file berhasil dibuat.",
    )
    path.write_text(content, encoding="utf-8", newline="")

print("Patch kode, test, dan dokumentasi selesai.")
'@

Write-Host "`n=== APPLY PATCH ==="
$PatchScript | & $Python -
if ($LASTEXITCODE -ne 0) {
    throw "Patch gagal. Periksa file; backup tersedia di $BackupDir"
}

Write-Host "`n=== RUN FOCUSED TESTS ==="
& $Python -m unittest tests.test_frontend_scanner_evidence_integration tests.test_evidence_integration -v
if ($LASTEXITCODE -ne 0) {
    throw "Focused tests gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== COMPILE CHECK ==="
& $Python -m compileall -q modules\frontend_scanner.py tests\test_frontend_scanner_evidence_integration.py
if ($LASTEXITCODE -ne 0) {
    throw "Compile check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== DIFF CHECK ==="
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== IMPLEMENTATION SUMMARY ===" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "Homepage Scanner mendaftarkan screenshot yang berhasil dibuat."
Write-Host "Focused tests, compile check, dan diff check selesai."
Write-Host "Full test suite dan scan live belum dijalankan."
