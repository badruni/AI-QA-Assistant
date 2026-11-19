[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact="High")]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path
$StatePath = Join-Path $ProjectRoot "batch_scripts\.request_safety_delivery_state.json"
if (-not (Test-Path $StatePath)) { throw "State file tidak ditemukan; rollback otomatis tidak dapat dilanjutkan." }

$State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if ($State.project_root -ne $ProjectRoot) { throw "Project root tidak cocok." }

$NewFiles = @(
    "tests\test_request_safety_delivery.py",
    "docs\FEATURE_01_REQUEST_SAFETY.md"
)
foreach ($RelativePath in $NewFiles) {
    $Target = Join-Path $ProjectRoot $RelativePath
    if (Test-Path -LiteralPath $Target) {
        if ($PSCmdlet.ShouldProcess($Target, "Hapus file yang dibuat oleh Feature 01 batch")) {
            Remove-Item -LiteralPath $Target -Force
        }
    }
}

Write-Host "File tambahan Feature 01 dihapus jika disetujui."
Write-Host "Backup sumber asli dipertahankan di: $($State.backup_root)"
Write-Host "Tidak ada file produksi yang perlu dipulihkan karena batch ini tidak mengubahnya."
