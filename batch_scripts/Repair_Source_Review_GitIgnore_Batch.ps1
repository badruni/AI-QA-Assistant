#requires -Version 5.1
$ErrorActionPreference = "Stop"

# Run from the AI-QA-Assistant repository root.
$Root = (Get-Location).Path
$GitIgnore = Join-Path $Root ".gitignore"

if (-not (Test-Path -LiteralPath (Join-Path $Root ".git") -PathType Container)) {
    throw "Folder .git tidak ditemukan. Jalankan script dari root repository."
}
if (-not (Test-Path -LiteralPath $GitIgnore -PathType Leaf)) {
    throw ".gitignore tidak ditemukan."
}

$OriginalHash = (Get-FileHash -LiteralPath $GitIgnore -Algorithm SHA256).Hash
$Bytes = [System.IO.File]::ReadAllBytes($GitIgnore)
$HasBom = $Bytes.Length -ge 3 -and
    $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF

$Reader = New-Object System.IO.StreamReader($GitIgnore, [System.Text.Encoding]::UTF8, $true)
try { $Content = $Reader.ReadToEnd() } finally { $Reader.Dispose() }

$BadLine = "System.Object[]"
$BadCount = ([regex]::Matches($Content, '(?m)^System\.Object\[\]\s*$')).Count

if ($BadCount -eq 0) {
    Write-Host "Teks System.Object[] tidak ditemukan. Tidak ada perubahan." -ForegroundColor Yellow
    exit 0
}
if ($BadCount -ne 1) {
    throw "Ditemukan $BadCount baris System.Object[]. Hentikan untuk pemeriksaan manual."
}

$RequiredRules = @(
    "/batch_scripts/documentation_generator_source_review/",
    "/batch_scripts/documentation_layout_source_20261118_154020/",
    "/batch_scripts/documentation_generator_source_review.zip",
    "/batch_scripts/documentation_layout_source_review.zip"
)

$Newline = "`n"
if ($Content.Contains("`r`n")) { $Newline = "`r`n" }

$RuleBlock = @(
    "# Local source-review archives and extracted snapshots (keep out of Git)"
    "/batch_scripts/documentation_generator_source_review/"
    "/batch_scripts/documentation_layout_source_20261118_154020/"
    "/batch_scripts/documentation_generator_source_review.zip"
    "/batch_scripts/documentation_layout_source_review.zip"
) -join $Newline

$NewContent = [regex]::Replace(
    $Content,
    '(?m)^System\.Object\[\]\s*$',
    [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $RuleBlock },
    1
)

if ($NewContent -eq $Content -or $NewContent -match '(?m)^System\.Object\[\]\s*$') {
    throw "Perbaikan teks tidak berhasil disiapkan. File asli tidak diubah."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\before_source_review_gitignore_repair_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$BackupFile = Join-Path $BackupDir ".gitignore"
Copy-Item -LiteralPath $GitIgnore -Destination $BackupFile

if ((Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash -ne $OriginalHash) {
    throw "Hash backup tidak cocok. File asli tidak diubah."
}

$Encoding = New-Object System.Text.UTF8Encoding($HasBom)
$TempFile = Join-Path $env:TEMP ("gitignore_repair_" + [guid]::NewGuid().ToString() + ".tmp")

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

$FinalReader = New-Object System.IO.StreamReader($GitIgnore, [System.Text.Encoding]::UTF8, $true)
try { $FinalContent = $FinalReader.ReadToEnd() } finally { $FinalReader.Dispose() }

$Missing = @($RequiredRules | Where-Object {
    $escaped = [regex]::Escape($_)
    $FinalContent -notmatch "(?m)^$escaped\s*$"
})

if ($FinalContent -match '(?m)^System\.Object\[\]\s*$' -or $Missing.Count -gt 0) {
    throw "Verifikasi akhir gagal. Backup tersedia di: $BackupFile"
}

Write-Host "`nPERBAIKAN .gitignore BERHASIL" -ForegroundColor Green
Write-Host "Backup: $BackupFile"
Write-Host "Teks System.Object[] sudah dihapus."
Write-Host "Empat aturan source-review sudah tercatat:"
$RequiredRules | ForEach-Object { Write-Host "  $_" }
Write-Host "Aturan lain tetap dipertahankan."
Write-Host "Staging area dan file proyek tidak diubah."
