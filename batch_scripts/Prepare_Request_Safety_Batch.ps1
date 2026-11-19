[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path
$Required = @(
    "core\request_safety.py",
    "core\playwright_request_guard.py",
    "modules\frontend_scanner.py",
    "tests\test_request_safety.py",
    "tests\test_playwright_request_guard.py"
)

Write-Host "=== FEATURE 01: PREPARE ===" -ForegroundColor Cyan
foreach ($RelativePath in $Required) {
    $FullPath = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $FullPath -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $RelativePath"
    }
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "backups\feature_01_request_safety_$Timestamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$BackupFiles = @(
    "core\request_safety.py",
    "core\playwright_request_guard.py",
    "modules\frontend_scanner.py",
    "tests\test_request_safety.py",
    "tests\test_playwright_request_guard.py"
)

foreach ($RelativePath in $BackupFiles) {
    $Source = Join-Path $ProjectRoot $RelativePath
    $Destination = Join-Path $BackupRoot $RelativePath
    $DestinationDirectory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination
}

$Manifest = [ordered]@{
    feature = "Feature 01 - Request Safety & Rate Limit"
    created_at = (Get-Date).ToString("o")
    project_root = $ProjectRoot
    backup_root = $BackupRoot
    backed_up_files = $BackupFiles
    planned_new_files = @(
        "tests\test_request_safety_delivery.py",
        "docs\FEATURE_01_REQUEST_SAFETY.md"
    )
}
$StatePath = Join-Path $ProjectRoot "batch_scripts\.request_safety_delivery_state.json"
$Manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding UTF8

Write-Host "Pemeriksaan awal: OK" -ForegroundColor Green
Write-Host "Backup dibuat: $BackupRoot" -ForegroundColor Green
Write-Host "State file: $StatePath"
Write-Host "Belum ada file aplikasi yang diubah."
