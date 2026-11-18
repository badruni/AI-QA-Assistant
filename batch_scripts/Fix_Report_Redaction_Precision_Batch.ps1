#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$ModuleFile = Join-Path $Root "core\report_manager.py"
$TestFile = Join-Path $Root "tests\test_report_manager.py"
$PythonExe = Join-Path $Root ".venv-scanner\Scripts\python.exe"

foreach ($File in @($ModuleFile, $TestFile, $PythonExe)) {
    if (-not (Test-Path $File -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File"
    }
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\before_report_redaction_precision_fix_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item $ModuleFile (Join-Path $BackupDir "report_manager.py")
Copy-Item $TestFile (Join-Path $BackupDir "test_report_manager.py")

$PatchScript = @'
from pathlib import Path

module_path = Path("core/report_manager.py")
module_text = module_path.read_text(encoding="utf-8")

old_function = '''def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
'''
new_function = '''def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")

    # Nama field metrik hasil inspeksi bukan nilai rahasia.
    # Contoh: password_fields=1 adalah jumlah elemen DOM, bukan password.
    if normalized.endswith(("_fields", "_count")):
        return False

    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
'''
if module_text.count(old_function) != 1:
    raise SystemExit("Fungsi _is_sensitive_key tidak cocok; modul tidak diubah.")
module_path.write_text(
    module_text.replace(old_function, new_function, 1),
    encoding="utf-8",
)

test_path = Path("tests/test_report_manager.py")
test_text = test_path.read_text(encoding="utf-8")

old_data = '''            "pages": [{
                "page_url": "https://example.test/a?token=secret#part",
                "access_token": "should-not-leak",
            }],
'''
new_data = '''            "pages": [{
                "page_url": "https://example.test/a?token=secret#part",
                "access_token": "should-not-leak",
                "signals": {
                    "password_fields": 1,
                    "password": "should-not-leak-either",
                },
            }],
'''
if test_text.count(old_data) != 1:
    raise SystemExit("Data uji sanitasi tidak cocok; test tidak diubah.")
test_text = test_text.replace(old_data, new_data, 1)

old_assert = '''        self.assertEqual(page["access_token"], "[REDACTED]")
'''
new_assert = '''        self.assertEqual(page["access_token"], "[REDACTED]")
        self.assertEqual(page["signals"]["password_fields"], 1)
        self.assertEqual(page["signals"]["password"], "[REDACTED]")
'''
if test_text.count(old_assert) != 1:
    raise SystemExit("Assertion sanitasi tidak cocok; test tidak diubah.")
test_text = test_text.replace(old_assert, new_assert, 1)
test_path.write_text(test_text, encoding="utf-8")

print("Aturan sanitasi diperketat dan regression test ditambahkan.")
'@

$TempScript = Join-Path $env:TEMP "fix_report_redaction_precision_$Stamp.py"
Set-Content -Path $TempScript -Value $PatchScript -Encoding UTF8

try {
    & $PythonExe $TempScript
    if ($LASTEXITCODE -ne 0) { throw "Patch sanitasi gagal." }

    & $PythonExe -m py_compile .\core\report_manager.py .\tests\test_report_manager.py
    if ($LASTEXITCODE -ne 0) { throw "Compile check gagal." }

    & $PythonExe -m unittest tests.test_report_manager -v
    if ($LASTEXITCODE -ne 0) { throw "Report Manager tests gagal. Kirim traceback lengkap." }

    Write-Host "`n=== GIT STATUS ===" -ForegroundColor Cyan
    git status --short
    Write-Host "`nBackup tersedia di: $BackupDir" -ForegroundColor Green
    Write-Host "Sanitasi dan regression tests berhasil."
}
finally {
    Remove-Item $TempScript -Force -ErrorAction SilentlyContinue
}
