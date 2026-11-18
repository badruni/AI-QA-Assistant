#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$TestFile = Join-Path $Root "tests\test_report_manager.py"
$PythonExe = Join-Path $Root ".venv-scanner\Scripts\python.exe"

if (-not (Test-Path $TestFile -PathType Leaf)) {
    throw "File test_report_manager.py tidak ditemukan. Jalankan dari root repository."
}
if (-not (Test-Path $PythonExe -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $PythonExe"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\before_report_manager_test_fix_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item $TestFile (Join-Path $BackupDir "test_report_manager.py")

$PatchScript = @'
from pathlib import Path

path = Path("tests/test_report_manager.py")
text = path.read_text(encoding="utf-8")

old_import = "from core import report_manager\n"
new_import = "from core import project_manager, report_manager\n"
if text.count(old_import) != 1:
    raise SystemExit("Import anchor tidak ditemukan secara unik.")
text = text.replace(old_import, new_import, 1)

old_patch = (
    '        self.projects_patch = patch.object(report_manager, "PROJECTS_DIR", self.root)\n'
    '        self.projects_patch.start()\n'
    '        self.addCleanup(self.projects_patch.stop)\n'
)
new_patch = (
    '        self.projects_patch = patch.object(report_manager, "PROJECTS_DIR", self.root)\n'
    '        self.projects_patch.start()\n'
    '        self.addCleanup(self.projects_patch.stop)\n'
    '\n'
    '        self.project_manager_patch = patch.object(\n'
    '            project_manager, "PROJECTS_DIR", self.root\n'
    '        )\n'
    '        self.project_manager_patch.start()\n'
    '        self.addCleanup(self.project_manager_patch.stop)\n'
)
if text.count(old_patch) != 1:
    raise SystemExit("Patch setup anchor tidak ditemukan secara unik.")
text = text.replace(old_patch, new_patch, 1)

path.write_text(text, encoding="utf-8")
print("Test fixture berhasil diperbaiki: kedua modul memakai PROJECTS_DIR sementara yang sama.")
'@

$TempScript = Join-Path $env:TEMP "fix_report_manager_test_$Stamp.py"
Set-Content -Path $TempScript -Value $PatchScript -Encoding UTF8

try {
    & $PythonExe $TempScript
    if ($LASTEXITCODE -ne 0) { throw "Perbaikan test fixture gagal." }

    & $PythonExe -m py_compile .\tests\test_report_manager.py
    if ($LASTEXITCODE -ne 0) { throw "Compile check test gagal." }

    & $PythonExe -m unittest tests.test_report_manager -v
    if ($LASTEXITCODE -ne 0) { throw "Unit test report manager masih gagal. Kirim traceback lengkap." }

    Write-Host "`n=== GIT STATUS ===" -ForegroundColor Cyan
    git status --short
    Write-Host "`nBackup test tersedia di: $BackupDir" -ForegroundColor Green
    Write-Host "Perbaikan hanya mengubah test fixture; kode produksi tidak diubah."
}
finally {
    Remove-Item $TempScript -Force -ErrorAction SilentlyContinue
}
