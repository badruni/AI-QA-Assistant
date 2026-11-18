$ErrorActionPreference = "Stop"
Write-Host "=== AI QA Assistant: Evidence Integration Batch ===" -ForegroundColor Cyan

$ProjectRoot = (Get-Location).Path
foreach ($Item in @(".git", "core", "modules", "tests", "docs")) {
    if (-not (Test-Path (Join-Path $ProjectRoot $Item))) {
        throw "Jalankan script dari root proyek. Item tidak ditemukan: $Item"
    }
}
$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Python scanner tidak ditemukan: $Python" }

$Targets = @(
    "modules\website_discovery.py",
    "modules\generic_uat_inspection.py",
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md"
)
foreach ($Target in $Targets) {
    if (-not (Test-Path (Join-Path $ProjectRoot $Target))) { throw "File wajib tidak ditemukan: $Target" }
}
if (Test-Path ".\tests\test_evidence_integration.py") {
    throw "tests\test_evidence_integration.py sudah ada; script tidak akan menimpanya."
}

$BackupName = "before_evidence_integration_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path $ProjectRoot ("backups\\" + $BackupName)
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
foreach ($Target in $Targets) {
    $Destination = Join-Path $BackupDir $Target
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item (Join-Path $ProjectRoot $Target) $Destination
}
Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$PythonCode = @'
from pathlib import Path

root = Path.cwd()

def update_module(relative_path, source_name, page_url_expr, title_expr, metadata_expr, function_anchor):
    path = root / relative_path
    text = path.read_text(encoding="utf-8")
    if "import logging\n" not in text:
        marker = "from dataclasses import dataclass\n"
        if marker not in text:
            raise RuntimeError(f"Import anchor tidak ditemukan: {relative_path}")
        text = text.replace(marker, "import logging\n" + marker, 1)

    evidence_import = "from core.evidence_manager import register_evidence\n"
    if evidence_import not in text:
        marker = "from core.result_status import ResultStatus\n"
        if marker not in text:
            raise RuntimeError(f"Evidence import anchor tidak ditemukan: {relative_path}")
        text = text.replace(marker, marker + evidence_import, 1)

    if "def _register_screenshot_evidence(" not in text:
        helper = (
            "def _register_screenshot_evidence(\n"
            "    project_id, screenshot_path, page_url, title, metadata=None,\n"
            "):\n"
            "    try:\n"
            "        register_evidence(\n"
            "            project_id=project_id,\n"
            "            file_path=screenshot_path,\n"
            '            evidence_type="screenshot",\n'
            f'            source="{source_name}",\n'
            "            page_url=page_url,\n"
            '            title=title or "",\n'
            "            metadata=metadata or {},\n"
            "        )\n"
            "        return True\n"
            "    except Exception:\n"
            "        logging.getLogger(__name__).warning(\n"
            '            "Screenshot evidence registration failed; inspection continues."\n'
            "        )\n"
            "        return False\n\n\n"
        )
        if function_anchor not in text:
            raise RuntimeError(f"Function anchor tidak ditemukan: {function_anchor}")
        text = text.replace(function_anchor, helper + function_anchor, 1)

    screenshot_anchor = (
        "                        except PlaywrightError:\n"
        "                            screenshot_path = None\n"
    )
    registration = (
        screenshot_anchor
        + "                        if screenshot_path is not None:\n"
        + "                            _register_screenshot_evidence(\n"
        + "                                config.project_id,\n"
        + "                                screenshot_path,\n"
        + f"                                {page_url_expr},\n"
        + f"                                {title_expr},\n"
        + f"                                {metadata_expr},\n"
        + "                            )\n"
    )
    if registration not in text:
        if text.count(screenshot_anchor) != 1:
            raise RuntimeError(f"Screenshot anchor tidak unik/tidak ditemukan: {relative_path}")
        text = text.replace(screenshot_anchor, registration, 1)
    path.write_text(text, encoding="utf-8", newline="\n")

update_module(
    "modules/website_discovery.py", "website_discovery",
    "target_url", "title", '{"page_type": page_type}', "def discover_website("
)
update_module(
    "modules/generic_uat_inspection.py", "generic_uat_inspection",
    "discovered.url", "discovered.title", '{"inspection": "generic_uat"}',
    "def inspect_generic_uat("
)

test_text = r'''import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import website_discovery, generic_uat_inspection


class EvidenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.screenshot = Path(self.temp.name) / "shot.png"
        self.screenshot.write_bytes(b"verified screenshot fixture")

    def test_discovery_registers_screenshot_metadata(self):
        with patch.object(website_discovery, "register_evidence") as register:
            result = website_discovery._register_screenshot_evidence(
                "PROJECT_A", self.screenshot, "https://example.test/",
                "Home", {"page_type": "homepage"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_A")
        self.assertEqual(kwargs["file_path"], self.screenshot)
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "website_discovery")
        self.assertEqual(kwargs["page_url"], "https://example.test/")
        self.assertEqual(kwargs["metadata"], {"page_type": "homepage"})

    def test_generic_uat_registers_screenshot_metadata(self):
        with patch.object(generic_uat_inspection, "register_evidence") as register:
            result = generic_uat_inspection._register_screenshot_evidence(
                "PROJECT_B", self.screenshot, "https://example.test/account",
                "Account", {"inspection": "generic_uat"},
            )
        self.assertTrue(result)
        register.assert_called_once()
        kwargs = register.call_args.kwargs
        self.assertEqual(kwargs["project_id"], "PROJECT_B")
        self.assertEqual(kwargs["evidence_type"], "screenshot")
        self.assertEqual(kwargs["source"], "generic_uat_inspection")
        self.assertEqual(kwargs["page_url"], "https://example.test/account")

    def test_discovery_registration_failure_is_non_fatal(self):
        with patch.object(
            website_discovery, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            self.assertFalse(website_discovery._register_screenshot_evidence(
                "PROJECT_A", self.screenshot, "https://example.test/", "Home",
            ))

    def test_generic_uat_registration_failure_is_non_fatal(self):
        with patch.object(
            generic_uat_inspection, "register_evidence",
            side_effect=OSError("sensitive internal detail"),
        ):
            self.assertFalse(generic_uat_inspection._register_screenshot_evidence(
                "PROJECT_B", self.screenshot, "https://example.test/", "Home",
            ))


if __name__ == "__main__":
    unittest.main()
'''
(root / "tests/test_evidence_integration.py").write_text(test_text, encoding="utf-8", newline="\n")

doc_marker = "## Evidence Management — screenshot registry integration"
doc_section = (
    "\n\n## Evidence Management — screenshot registry integration\n\n"
    "- Screenshot hasil Website Discovery dan Generic UAT didaftarkan ke "
    "`evidence/evidence_index.json` melalui `core/evidence_manager.py`.\n"
    "- File screenshot tetap disimpan di `evidence/screenshots/`; integrasi "
    "tidak memindahkan atau menghapus evidence yang sudah ada.\n"
    "- Registrasi dilakukan hanya setelah screenshot berhasil dibuat. "
    "Kegagalan pencatatan tidak menggagalkan proses inspeksi dan hanya "
    "menghasilkan peringatan generik tanpa detail exception.\n"
    "- Metadata menyimpan sumber inspeksi dan URL halaman yang disanitasi "
    "oleh Evidence Manager.\n"
)
for relative in ("docs/PROJECT_SETUP_GUIDE.md", "docs/PORTABLE_SETUP_GUIDE.md"):
    path = root / relative
    content = path.read_text(encoding="utf-8-sig")
    if doc_marker not in content:
        path.write_text(content.rstrip() + doc_section, encoding="utf-8", newline="\n")
print("Source integration and documentation updates completed.")
'@

Write-Host "`n=== APPLY INTEGRATION ===" -ForegroundColor Cyan
$PythonCode | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Penerapan perubahan gagal. Backup: $BackupDir" }

Write-Host "`n=== FOCUSED TESTS ===" -ForegroundColor Cyan
& $Python -m unittest tests.test_evidence_integration tests.test_evidence_manager tests.test_website_discovery tests.test_generic_uat_inspection -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Backup: $BackupDir" }

Write-Host "`n=== COMPILE CHECK ===" -ForegroundColor Cyan
& $Python -m py_compile .\modules\website_discovery.py .\modules\generic_uat_inspection.py .\core\evidence_manager.py .\tests\test_evidence_integration.py
if ($LASTEXITCODE -ne 0) { throw "Compile check gagal. Backup: $BackupDir" }

Write-Host "`n=== FULL TEST SUITE ===" -ForegroundColor Cyan
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Full test suite gagal. Backup: $BackupDir" }

Write-Host "`n=== DIFF CHECK ===" -ForegroundColor Cyan
git --no-pager diff --check
if ($LASTEXITCODE -ne 0) { throw "Git diff check gagal. Backup: $BackupDir" }

Write-Host "`nEvidence Integration batch selesai." -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "File baru: tests\test_evidence_integration.py"
Write-Host "Catatan: screenshot lama tidak dipindahkan atau dihapus."
