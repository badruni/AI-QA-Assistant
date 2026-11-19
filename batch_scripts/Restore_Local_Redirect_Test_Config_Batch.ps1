$ErrorActionPreference = "Stop"

Write-Host "=== RESTORE LOCAL REDIRECT TEST CONFIGURATION ===" -ForegroundColor Cyan

$ProjectId = "LOCAL_SCANNER_TEST"
$ExpectedTestUrl = "http://127.0.0.1:8000/redirect"
$ExpectedOriginalUrl = "http://127.0.0.1:8000"
$ProjectDir = Join-Path (Get-Location) "projects\LOCAL_SCANNER_TEST"
$ConfigPath = Join-Path $ProjectDir "project_config.json"
$BackupPath = Join-Path $ProjectDir "project_config.before_redirect_20261118_224530.json"

if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Konfigurasi aktif tidak ditemukan: $ConfigPath"
}
if (-not (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
    throw "Backup konfigurasi tidak ditemukan: $BackupPath"
}

$Current = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Backup = Get-Content -LiteralPath $BackupPath -Raw -Encoding UTF8 | ConvertFrom-Json

if ($Current.project_id -ne $ProjectId -or $Backup.project_id -ne $ProjectId) {
    throw "Project ID tidak cocok. Tidak ada perubahan."
}
if ($Current.base_url -ne $ExpectedTestUrl) {
    throw "Base URL aktif bukan URL tes yang diharapkan. Tidak ada perubahan."
}
if ($Backup.base_url -ne $ExpectedOriginalUrl) {
    throw "Base URL di backup tidak sesuai. Tidak ada perubahan."
}

# Simpan salinan konfigurasi tes sebelum pemulihan.
$AfterTestPath = Join-Path $ProjectDir "project_config.after_redirect_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
Copy-Item -LiteralPath $ConfigPath -Destination $AfterTestPath

# Pulihkan konfigurasi asli melalui file sementara.
$TempPath = Join-Path $ProjectDir "project_config.restore.tmp"
try {
    Copy-Item -LiteralPath $BackupPath -Destination $TempPath
    Move-Item -LiteralPath $TempPath -Destination $ConfigPath -Force
}
finally {
    if (Test-Path -LiteralPath $TempPath) {
        Remove-Item -LiteralPath $TempPath -Force
    }
}

$Restored = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Restored.project_id -ne $ProjectId -or $Restored.base_url -ne $ExpectedOriginalUrl) {
    throw "Verifikasi pemulihan gagal. Periksa backup: $BackupPath"
}

Write-Host ""
Write-Host "Konfigurasi berhasil dipulihkan." -ForegroundColor Green
Write-Host "Project ID          : $($Restored.project_id)"
Write-Host "Base URL             : $($Restored.base_url)"
Write-Host "Backup sumber        : $BackupPath"
Write-Host "Salinan konfigurasi tes: $AfterTestPath"
Write-Host "Pengaturan scan       : dipulihkan dari backup."
