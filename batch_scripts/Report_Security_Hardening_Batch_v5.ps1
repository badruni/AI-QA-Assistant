# Batch: Report Security Hardening (regex-anchored, validated)
# Run from repository root. Batch scripts are stored in /batch_scripts (gitignored).
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
        throw "File wajib tidak ditemukan: $File"
    }
}

# Expected repository state reviewed with the user. Stop on any unrelated changes.
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
$Status = @(git status --short)
$Unexpected = @($Status | Where-Object { $_ -notin $Allowed })
if ($Unexpected.Count -gt 0) {
    Write-Host "Git status memiliki perubahan yang belum direview:" -ForegroundColor Yellow
    $Unexpected | ForEach-Object { Write-Host $_ }
    throw "Batch dihentikan untuk melindungi perubahan lain."
}

# Create a timestamped backup before editing.
$BackupName = "before_report_security_hardening_v5_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path ".\backups" $BackupName
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
foreach ($File in $RequiredFiles) {
    $Destination = Join-Path $BackupDir $File
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item $File $Destination
}
Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

# --- report_manager.py: replace only the function, not the tuple formatting. ---
$ReportPath = ".\core\report_manager.py"
$ReportCode = Get-Content $ReportPath -Raw
$FunctionPattern = '(?ms)^def _is_sensitive_key\(key\):.*?(?=^def _safe_url\()'
$FunctionMatches = [regex]::Matches($ReportCode, $FunctionPattern)
if ($FunctionMatches.Count -ne 1) {
    throw "Tidak ditemukan tepat satu fungsi _is_sensitive_key sebelum _safe_url. File tidak diubah lebih lanjut."
}

$ReplacementFunction = @'
# Hanya metrik inspeksi yang dikenal yang dikecualikan dari redaksi.
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


def _is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")

    if normalized in _SAFE_METRIC_KEYS:
        return False

    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


'@
$ReportCode = [regex]::Replace($ReportCode, $FunctionPattern, $ReplacementFunction, 1)
Set-Content -Path $ReportPath -Value $ReportCode -Encoding utf8

# --- agent.py: warning output must not print raw exception details. ---
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
    throw "Baris warning yang diharapkan tidak ditemukan di agent.py."
}
Set-Content -Path $AgentPath -Value $AgentCodeNew -Encoding utf8

# --- test: explicit allowlist; sensitive names with suffixes remain redacted. ---
$TestPath = ".\tests\test_report_manager.py"
$TestCode = Get-Content $TestPath -Raw
$Anchor = '    def test_rejects_unknown_inspection_type(self):'
if (-not $TestCode.Contains($Anchor)) {
    throw "Anchor test_rejects_unknown_inspection_type tidak ditemukan."
}
if ($TestCode.Contains("test_only_known_inspection_metrics_bypass_sensitive_redaction")) {
    throw "Regression test hardening sudah ada; hentikan agar tidak menggandakan test."
}
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
$TestCode = $TestCode.Replace($Anchor, $AddedTest)
Set-Content -Path $TestPath -Value $TestCode -Encoding utf8

# --- docs: explain explicit metric allowlist. ---
foreach ($Doc in @(".\docs\PROJECT_SETUP_GUIDE.md", ".\docs\PORTABLE_SETUP_GUIDE.md")) {
    $Content = Get-Content $Doc -Raw
    $OldPhrase = "authorization, atau API key akan disamarkan. Screenshot tetap berada di folder"
    $NewPhrase = "authorization, atau API key akan disamarkan. Hanya nama metrik inspeksi yang diizinkan secara eksplisit yang dikecualikan. Screenshot tetap berada di folder"
    if (-not $Content.Contains($OldPhrase)) {
        throw "Teks dokumentasi redaksi tidak ditemukan pada $Doc."
    }
    $Content = $Content.Replace($OldPhrase, $NewPhrase)
    Set-Content -Path $Doc -Value $Content -Encoding utf8
}

Write-Host "`n=== REPORT MANAGER TESTS ===" -ForegroundColor Cyan
& ".\.venv-scanner\Scripts\python.exe" -m unittest tests.test_report_manager -v
if ($LASTEXITCODE -ne 0) { throw "Report Manager tests gagal. Backup: $BackupDir" }

Write-Host "`n=== COMPILE CHECK ===" -ForegroundColor Cyan
& ".\.venv-scanner\Scripts\python.exe" -m py_compile .\agent.py .\core\report_manager.py .\tests\test_report_manager.py
if ($LASTEXITCODE -ne 0) { throw "Compile check gagal. Backup: $BackupDir" }

Write-Host "`n=== DIFF CHECK ===" -ForegroundColor Cyan
git --no-pager diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup: $BackupDir" }

Write-Host "`nBatch berhasil. Backup: $BackupDir" -ForegroundColor Green
Write-Host "Belum ada commit atau push." -ForegroundColor Yellow
