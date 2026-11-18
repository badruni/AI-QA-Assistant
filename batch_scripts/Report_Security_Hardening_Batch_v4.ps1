# Batch: harden report warning output and metric redaction allowlist.
# Run from the AI-QA-Assistant repository root in PowerShell.
$ErrorActionPreference = "Stop"

$RequiredFiles = @(
    ".\agent.py",
    ".\core\report_manager.py",
    ".\tests\test_report_manager.py",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\docs\PORTABLE_SETUP_GUIDE.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File. Pastikan terminal berada di root repository."
    }
}

# Guard: jangan menimpa pekerjaan lain yang belum diperiksa.
$Status = @(git status --short)
$Allowed = @(
    " M .gitignore",
    "D  Fix_Agent_Menu_And_Restricted_UAT_Batch.ps1",
    "D  Fix_Generic_UAT_Review_Batch.ps1",
    "D  Implement_Authentication_Discovery_Batch.ps1",
    "D  Implement_Generic_UAT_Batch.ps1",
    "D  Setup_QA_Demo_SauceDemo_Batch.ps1",
    " M agent.py",
    " M docs/PORTABLE_SETUP_GUIDE.md",
    " M docs/PROJECT_SETUP_GUIDE.md",
    "?? core/report_manager.py",
    "?? tests/test_report_manager.py"
)
$Unexpected = @($Status | Where-Object { $_ -notin $Allowed })
if ($Unexpected.Count -gt 0) {
    Write-Host "Git status memiliki perubahan di luar yang sudah kita review:" -ForegroundColor Yellow
    $Unexpected | ForEach-Object { Write-Host $_ }
    throw "Batch dihentikan untuk melindungi perubahan yang belum diperiksa."
}

$BackupName = "before_report_security_hardening_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path ".\backups" $BackupName
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

foreach ($File in $RequiredFiles) {
    $Destination = Join-Path $BackupDir $File
    $Parent = Split-Path $Destination -Parent
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    Copy-Item $File $Destination
}
Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$ReportPath = ".\core\report_manager.py"
$ReportCode = Get-Content $ReportPath -Raw

$OldSensitive = @'
_SENSITIVE_KEY_PARTS = (
    "password", "passwd", "token", "secret", "cookie",
    "credential", "authorization", "api_key", "apikey",
)
'@
$NewSensitive = @'
_SENSITIVE_KEY_PARTS = (
    "password", "passwd", "token", "secret", "cookie",
    "credential", "authorization", "api_key", "apikey",
)

# Hanya metrik DOM yang memang dihasilkan scanner yang boleh melewati redaksi.
# Jangan gunakan pengecualian umum berdasarkan suffix seperti "_fields"/"_count".
_SAFE_METRIC_KEYS = {
    "navigation_count",
    "form_count",
    "card_count",
    "link_count",
    "button_count",
    "input_count",
    "image_count",
    "links_without_href",
    "links_without_name",
    "buttons_without_name",
    "inputs_without_label",
    "images_without_alt",
    "password_fields",
    "otp_fields",
    "login_forms",
}
'@

if (-not $ReportCode.Contains($OldSensitive)) {
    throw "Blok _SENSITIVE_KEY_PARTS tidak cocok dengan versi file saat ini. Tidak ada perubahan diterapkan."
}
$ReportCode = $ReportCode.Replace($OldSensitive, $NewSensitive)

$OldFunction = @'
def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")

    # Nama field metrik hasil inspeksi bukan nilai rahasia.
    # Contoh: password_fields=1 adalah jumlah elemen DOM, bukan password.
    if normalized.endswith(("_fields", "_count")):
        return False

    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
'@
$NewFunction = @'
def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")

    # Pengecualian hanya untuk nama metrik inspeksi yang dikenal.
    if normalized in _SAFE_METRIC_KEYS:
        return False

    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)
'@

if (-not $ReportCode.Contains($OldFunction)) {
    throw "Fungsi _is_sensitive_key tidak cocok dengan versi file saat ini. Tidak ada perubahan diterapkan."
}
$ReportCode = $ReportCode.Replace($OldFunction, $NewFunction)
Set-Content -Path $ReportPath -Value $ReportCode -Encoding utf8

$AgentPath = ".\agent.py"
$AgentCode = Get-Content $AgentPath -Raw
$AgentCodeNew = $AgentCode.Replace(
    'print("[WARNING] Laporan Authentication Discovery gagal disimpan:", report_error)',
    'print("[WARNING] Laporan Authentication Discovery gagal disimpan. Hasil inspeksi tetap tersedia.")'
).Replace(
    'print("[WARNING] Laporan Generic UAT gagal disimpan:", report_error)',
    'print("[WARNING] Laporan Generic UAT gagal disimpan. Hasil inspeksi tetap tersedia.")'
)

if ($AgentCodeNew -eq $AgentCode) {
    throw "Baris warning agent.py tidak ditemukan. Tidak ada perubahan warning yang diterapkan."
}
Set-Content -Path $AgentPath -Value $AgentCodeNew -Encoding utf8

$TestPath = ".\tests\test_report_manager.py"
$TestCode = Get-Content $TestPath -Raw
$Anchor = @'
    def test_rejects_unknown_inspection_type(self):
'@
$AddedTest = @'
    def test_only_known_inspection_metrics_bypass_sensitive_redaction(self):
        self.assertFalse(report_manager._is_sensitive_key("password_fields"))
        self.assertFalse(report_manager._is_sensitive_key("form_count"))
        self.assertTrue(report_manager._is_sensitive_key("access_token_fields"))
        self.assertTrue(report_manager._is_sensitive_key("password_count"))

        result = {
            "signals": {
                "password_fields": 1,
                "access_token_fields": "must-not-leak",
                "password_count": "must-not-leak-either",
            }
        }
        path = report_manager.save_inspection_report(
            self.project_id, "authentication_discovery", result
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        signals = payload["result"]["signals"]
        self.assertEqual(signals["password_fields"], 1)
        self.assertEqual(signals["access_token_fields"], "[REDACTED]")
        self.assertEqual(signals["password_count"], "[REDACTED]")

    def test_rejects_unknown_inspection_type(self):
'@

if (-not $TestCode.Contains($Anchor)) {
    throw "Lokasi penambahan regression test tidak ditemukan. Tidak ada perubahan test yang diterapkan."
}
$TestCode = $TestCode.Replace($Anchor, $AddedTest)
Set-Content -Path $TestPath -Value $TestCode -Encoding utf8

# Documentation: describe allowlist rather than implying all suffix fields are safe.
foreach ($Doc in @(".\docs\PROJECT_SETUP_GUIDE.md", ".\docs\PORTABLE_SETUP_GUIDE.md")) {
    $Content = Get-Content $Doc -Raw
    $OldText = 'Field yang namanya mengindikasikan password, token, secret, cookie, credential,'
    $NewText = 'Field yang namanya mengindikasikan password, token, secret, cookie, credential,'
    if (-not $Content.Contains($OldText)) {
        throw "Bagian redaksi field tidak ditemukan pada $Doc."
    }
    $Content = $Content.Replace(
        'authorization, atau API key akan disamarkan. Screenshot tetap berada di folder',
        'authorization, atau API key akan disamarkan. Hanya nama metrik inspeksi yang diizinkan secara eksplisit yang dikecualikan. Screenshot tetap berada di folder'
    )
    Set-Content -Path $Doc -Value $Content -Encoding utf8
}

Write-Host "`n=== RUN REPORT MANAGER TESTS ===" -ForegroundColor Cyan
& ".\.venv-scanner\Scripts\python.exe" -m unittest tests.test_report_manager -v
if ($LASTEXITCODE -ne 0) {
    throw "Regression test gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== COMPILE CHECK ===" -ForegroundColor Cyan
& ".\.venv-scanner\Scripts\python.exe" -m py_compile .\agent.py .\core\report_manager.py .\tests\test_report_manager.py
if ($LASTEXITCODE -ne 0) {
    throw "Compile check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`n=== DIFF CHECK ===" -ForegroundColor Cyan
git --no-pager diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`nBatch selesai. Backup: $BackupDir" -ForegroundColor Green
Write-Host "Belum ada commit atau push." -ForegroundColor Yellow
