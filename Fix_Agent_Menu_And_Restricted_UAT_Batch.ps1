[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path

Write-Host "=== AI QA Assistant: Integration Fix Batch ===" -ForegroundColor Cyan

$Required = @(
    "agent.py",
    "core\result_status.py",
    "modules\website_discovery.py",
    "modules\generic_uat_inspection.py",
    "tests"
)
foreach ($item in $Required) {
    if (-not (Test-Path (Join-Path $ProjectRoot $item))) {
        throw "File/folder wajib tidak ditemukan: $item. Jalankan dari root proyek."
    }
}

$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "backups\before_integration_fix_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

Copy-Item (Join-Path $ProjectRoot "agent.py") (Join-Path $BackupDir "agent.py")
$TestPath = Join-Path $ProjectRoot "tests\test_agent_menu_and_restriction.py"
if (Test-Path $TestPath) {
    Copy-Item $TestPath (Join-Path $BackupDir "test_agent_menu_and_restriction.py")
}

Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$AgentPath = Join-Path $ProjectRoot "agent.py"
$Agent = [System.IO.File]::ReadAllText($AgentPath, [System.Text.Encoding]::UTF8)

# Fix 1: import ResultStatus explicitly.
if ($Agent -notmatch '(?m)^from core\.result_status import ResultStatus\s*$') {
    $anchor = 'from core.logger import ('
    if (-not $Agent.Contains($anchor)) {
        throw "Import anchor 'from core.logger import (' tidak ditemukan. Tidak ada perubahan lanjutan."
    }
    $Agent = $Agent.Replace(
        $anchor,
        "from core.result_status import ResultStatus`r`n`r`n$anchor"
    )
}

# Fix 2: synchronize visible menu labels with existing handlers.
$oldMenuLine = '    print("6. Keluar")'
$newMenuLines = @'
    print("6. Jalankan Authentication Discovery")
    print("7. Keluar")
'@.TrimEnd()
if ($Agent.Contains($oldMenuLine)) {
    $Agent = $Agent.Replace($oldMenuLine, $newMenuLines)
}
elseif (
    $Agent -notmatch '(?m)^\s*print\("6\. Jalankan Authentication Discovery"\)\s*$' -or
    $Agent -notmatch '(?m)^\s*print\("7\. Keluar"\)\s*$'
) {
    throw "Baris menu tidak cocok dengan kondisi yang diharapkan. Periksa agent.py; perubahan dibatalkan."
}

# Guard: make sure visible labels and handlers agree before writing.
if ($Agent -notmatch '(?m)^\s*print\("6\. Jalankan Authentication Discovery"\)\s*$') {
    throw "Label menu 6 belum terpasang."
}
if ($Agent -notmatch '(?m)^\s*print\("7\. Keluar"\)\s*$') {
    throw "Label menu 7 belum terpasang."
}
if ($Agent -notmatch '(?m)^\s*elif choice == "6":\s*\r?\n\s*active_project_id = run_authentication_discovery\(active_project_id\)') {
    throw "Handler pilihan 6 tidak sesuai ekspektasi. Periksa agent.py."
}
if ($Agent -notmatch '(?m)^\s*elif choice == "7":') {
    throw "Handler pilihan 7 tidak ditemukan."
}

[System.IO.File]::WriteAllText(
    $AgentPath,
    $Agent,
    [System.Text.UTF8Encoding]::new($false)
)

$TestContent = @'
import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import agent
from core.result_status import ResultStatus


class AgentMenuIntegrationTests(unittest.TestCase):
    def test_menu_labels_match_authentication_and_exit_handlers(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            agent.show_menu("001")

        menu = output.getvalue()
        self.assertIn("6. Jalankan Authentication Discovery", menu)
        self.assertIn("7. Keluar", menu)
        self.assertNotIn("6. Keluar", menu)


class GenericUATRestrictedIntegrationTests(unittest.TestCase):
    def test_access_restricted_stops_before_generic_uat_inspection(self):
        config = SimpleNamespace(project_id="001")
        discovery = SimpleNamespace(
            status=ResultStatus.ACCESS_RESTRICTED,
            pages=(object(),),
            stopped_reason="HTTP 403",
        )

        with (
            patch.object(agent, "load_scanner_config", return_value=config),
            patch.object(agent, "discover_website", return_value=discovery),
            patch.object(agent, "inspect_generic_uat") as inspect_mock,
            patch.object(agent, "log_warning") as warning_mock,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            returned_project = agent.run_generic_uat_inspection("001")

        self.assertEqual(returned_project, "001")
        inspect_mock.assert_not_called()
        warning_mock.assert_called_once()
        self.assertIn("dihentikan", output.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
'@

[System.IO.File]::WriteAllText(
    $TestPath,
    $TestContent,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "`nPerubahan diterapkan." -ForegroundColor Green

Write-Host "`n[1/4] Compile check..." -ForegroundColor Cyan
& $Python -m py_compile agent.py tests\test_agent_menu_and_restriction.py
if ($LASTEXITCODE -ne 0) {
    throw "Compile check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n[2/4] Integration regression tests..." -ForegroundColor Cyan
& $Python -m unittest tests.test_agent_menu_and_restriction -v
if ($LASTEXITCODE -ne 0) {
    throw "Integration tests gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n[3/4] Authentication Discovery tests..." -ForegroundColor Cyan
& $Python -m unittest tests.test_authentication_discovery -v
if ($LASTEXITCODE -ne 0) {
    throw "Authentication Discovery tests gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n[4/4] Git whitespace check..." -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== BATCH SELESAI: MENUNGGU VERIFIKASI PENGGUNA ===" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "Perubahan: import ResultStatus, label menu 6/7, integration regression tests."
Write-Host "Tidak ada website yang diakses oleh test."
Write-Host "Belum ada commit atau push."
