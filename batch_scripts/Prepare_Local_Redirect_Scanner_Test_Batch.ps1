$ErrorActionPreference = "Stop"

Write-Host "=== PREPARE LOCAL REDIRECT SCANNER TEST ===" -ForegroundColor Cyan

$ProjectId = "LOCAL_SCANNER_TEST"
$ExpectedBaseUrl = "http://127.0.0.1:8000"
$TargetBaseUrl = "http://127.0.0.1:8000/redirect"

$ProjectDir = Join-Path (Get-Location) "projects\LOCAL_SCANNER_TEST"
$ConfigPath = Join-Path $ProjectDir "project_config.json"
$RedirectServerPath = Join-Path (Get-Location) "local_test_site\redirect_test_server.py"

if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Konfigurasi proyek tidak ditemukan: $ConfigPath"
}

if (-not (Test-Path -LiteralPath $RedirectServerPath -PathType Leaf)) {
    throw "File redirect test server tidak ditemukan: $RedirectServerPath"
}

$Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

if ($Config.project_id -ne $ProjectId) {
    throw "Project ID tidak sesuai. Tidak ada perubahan yang dilakukan."
}

if ($Config.base_url -ne $ExpectedBaseUrl) {
    throw "Base URL saat ini bukan nilai yang diharapkan ($ExpectedBaseUrl). Tidak ada perubahan."
}

if (-not ($Config.scan -is [System.Management.Automation.PSCustomObject])) {
    throw "Struktur konfigurasi scan tidak valid. Tidak ada perubahan."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = Join-Path $ProjectDir "project_config.before_redirect_$Timestamp.json"

if (Test-Path -LiteralPath $BackupPath) {
    throw "File backup sudah ada: $BackupPath"
}

# Simpan konfigurasi asli sebelum melakukan perubahan.
Copy-Item -LiteralPath $ConfigPath -Destination $BackupPath

# Simpan nilai scan untuk memastikan pengaturan lain tidak berubah.
$ScanBefore = $Config.scan | ConvertTo-Json -Depth 20 -Compress

# Ubah hanya base_url.
$Config.base_url = $TargetBaseUrl
$JsonOutput = $Config | ConvertTo-Json -Depth 20
$TempPath = Join-Path $ProjectDir "project_config.redirect.tmp"

try {
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($TempPath, $JsonOutput + [Environment]::NewLine, $Utf8NoBom)
    Move-Item -LiteralPath $TempPath -Destination $ConfigPath -Force
}
finally {
    if (Test-Path -LiteralPath $TempPath) {
        Remove-Item -LiteralPath $TempPath -Force
    }
}

# Baca ulang dan verifikasi hasil perubahan.
$Verified = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$ScanAfter = $Verified.scan | ConvertTo-Json -Depth 20 -Compress

if ($Verified.project_id -ne $ProjectId) {
    throw "Verifikasi gagal: Project ID berubah."
}

if ($Verified.base_url -ne $TargetBaseUrl) {
    throw "Verifikasi gagal: Base URL tidak sesuai."
}

if ($ScanBefore -ne $ScanAfter) {
    throw "Verifikasi gagal: pengaturan scan ikut berubah. Pulihkan konfigurasi dari backup: $BackupPath"
}

Write-Host ""
Write-Host "Konfigurasi berhasil disiapkan untuk tes redirect." -ForegroundColor Green
Write-Host "Project ID : $($Verified.project_id)"
Write-Host "Base URL   : $($Verified.base_url)"
Write-Host "Backup     : $BackupPath"
Write-Host "Pengaturan scan: tidak berubah."
Write-Host "File server redirect tersedia: $RedirectServerPath"
Write-Host ""
Write-Host "Belum ada scanner yang dijalankan."
