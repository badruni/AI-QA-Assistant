#requires -Version 5.1
$ErrorActionPreference = "Stop"

# Run from the AI-QA-Assistant repository root.
$Root = (Get-Location).Path
$GitDir = Join-Path $Root ".git"
$GitIgnore = Join-Path $Root ".gitignore"

if (-not (Test-Path -LiteralPath $GitDir -PathType Container)) {
    throw "Folder .git tidak ditemukan. Jalankan script dari root repository."
}
if (-not (Test-Path -LiteralPath $GitIgnore -PathType Leaf)) {
    throw ".gitignore tidak ditemukan."
}

$RequiredLocalItems = @(
    "batch_scripts\documentation_generator_source_review.zip",
    "batch_scripts\documentation_layout_source_review.zip",
    "batch_scripts\documentation_generator_source_review",
    "batch_scripts\documentation_layout_source_20261118_154020"
)

foreach ($item in $RequiredLocalItems) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $item))) {
        throw "Item source review tidak ditemukan: $item. Tidak ada perubahan."
    }
}

$OriginalHash = (Get-FileHash -LiteralPath $GitIgnore -Algorithm SHA256).Hash
$Bytes = [System.IO.File]::ReadAllBytes($GitIgnore)
$HasBom = $Bytes.Length -ge 3 -and
    $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF

$Reader = New-Object System.IO.StreamReader($GitIgnore, [System.Text.Encoding]::UTF8, $true)
try { $Content = $Reader.ReadToEnd() } finally { $Reader.Dispose() }

$Rules = @(
    "/batch_scripts/documentation_generator_source_review/",
    "/batch_scripts/documentation_layout_source_20261118_154020/",
    "/batch_scripts/documentation_generator_source_review.zip",
    "/batch_scripts/documentation_layout_source_review.zip"
)

$MissingRules = @($Rules | Where-Object {
    $escaped = [regex]::Escape($_)
    $Content -notmatch "(?m)^$escaped\s*$"
})

if ($MissingRules.Count -eq 0) {
    Write-Host "Semua aturan pengecualian source review sudah tersedia. Tidak ada perubahan." -ForegroundColor Yellow
    exit 0
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\before_source_review_gitignore_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$BackupFile = Join-Path $BackupDir ".gitignore"
Copy-Item -LiteralPath $GitIgnore -Destination $BackupFile

if ((Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash -ne $OriginalHash) {
    throw "Verifikasi backup .gitignore gagal. File asli tidak diubah."
}

$Newline = "`n"
if ($Content.Contains("`r`n")) { $Newline = "`r`n" }

$Addition = @(
    "",
    "# Local source-review archives and extracted snapshots (keep out of Git)",
    $MissingRules
) -join $Newline

$NewContent = $Content.TrimEnd("`r", "`n") + $Addition + $Newline
$Encoding = New-Object System.Text.UTF8Encoding($HasBom)
$TempFile = Join-Path $env:TEMP ("gitignore_source_review_" + [guid]::NewGuid().ToString() + ".tmp")

try {
    [System.IO.File]::WriteAllText($TempFile, $NewContent, $Encoding)

    if ((Get-FileHash -LiteralPath $GitIgnore -Algorithm SHA256).Hash -ne $OriginalHash) {
        throw ".gitignore berubah setelah backup. Penggantian dibatalkan."
    }

    Copy-Item -LiteralPath $TempFile -Destination $GitIgnore -Force
}
finally {
    if (Test-Path -LiteralPath $TempFile) {
        Remove-Item -LiteralPath $TempFile -Force
    }
}

$FinalContent = [System.IO.File]::ReadAllText($GitIgnore, [System.Text.Encoding]::UTF8)
$Unmatched = @($Rules | Where-Object {
    $escaped = [regex]::Escape($_)
    $FinalContent -notmatch "(?m)^$escaped\s*$"
})

if ($Unmatched.Count -gt 0) {
    throw "Verifikasi aturan ignore gagal: $($Unmatched -join ', '). Backup: $BackupFile"
}

Write-Host "`nATURAN SOURCE REVIEW BERHASIL DITAMBAHKAN" -ForegroundColor Green
Write-Host "Backup: $BackupFile"
Write-Host "`nAturan yang aktif:"
$Rules | ForEach-Object { Write-Host "  $_" }
Write-Host "`nFolder dan ZIP tetap dipertahankan secara lokal."
Write-Host "Staging area dan file aplikasi tidak diubah."
