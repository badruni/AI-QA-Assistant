#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$ModuleFile = Join-Path $Root "core\report_manager.py"
$PythonExe = Join-Path $Root ".venv-scanner\Scripts\python.exe"

if (-not (Test-Path $ModuleFile -PathType Leaf)) {
    throw "core\report_manager.py tidak ditemukan. Jalankan dari root repository."
}
if (-not (Test-Path $PythonExe -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $PythonExe"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\before_report_json_newline_fix_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item $ModuleFile (Join-Path $BackupDir "report_manager.py")

$PatchScript = @'
from pathlib import Path

path = Path("core/report_manager.py")
text = path.read_text(encoding="utf-8")

old = '            file.write("\\\\n")'
new = '            file.write("\\n")'

if text.count(old) != 1:
    print("Isi file_write yang ditemukan:")
    for line in text.splitlines():
        if "file.write" in line:
            print(repr(line))
    raise SystemExit(
        "Baris newline tidak cocok persis; file tidak diubah."
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Baris penulisan newline berhasil diperbaiki.")
'@

$TempScript = Join-Path $env:TEMP "fix_report_json_newline_$Stamp.py"
Set-Content -Path $TempScript -Value $PatchScript -Encoding UTF8

try {
    & $PythonExe $TempScript
    if ($LASTEXITCODE -ne 0) { throw "Patch newline gagal." }

    & $PythonExe -m py_compile .\core\report_manager.py
    if ($LASTEXITCODE -ne 0) { throw "Compile check gagal." }

    & $PythonExe -m unittest tests.test_report_manager -v
    if ($LASTEXITCODE -ne 0) { throw "Report Manager tests masih gagal. Kirim traceback lengkap." }

    Write-Host "`n=== GIT STATUS ===" -ForegroundColor Cyan
    git status --short
    Write-Host "`nBackup tersedia di: $BackupDir" -ForegroundColor Green
    Write-Host "Newline fix dan 4 focused tests berhasil."
}
finally {
    Remove-Item $TempScript -Force -ErrorAction SilentlyContinue
}
