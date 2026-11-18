#requires -Version 5.1
<#
AI QA Assistant - Documentation EOF cleanup
Run from repository root:
  .\batch_scripts\Fix_Documentation_EOF_Batch.ps1
#>
$ErrorActionPreference = "Stop"

$Target = ".\docs\PROJECT_SETUP_GUIDE.md"
if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) {
    throw "File tidak ditemukan: $Target"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = ".\backups\before_documentation_eof_cleanup_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item -LiteralPath $Target -Destination (Join-Path $BackupDir "PROJECT_SETUP_GUIDE.md")

# Normalize only trailing blank lines; preserve all document content and use UTF-8.
$Content = [System.IO.File]::ReadAllText((Resolve-Path $Target), [System.Text.Encoding]::UTF8)
$Content = $Content.TrimEnd("`r", "`n") + "`r`n"
[System.IO.File]::WriteAllText((Resolve-Path $Target), $Content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "`n========== VERIFY EOF CLEANUP ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check masih menemukan masalah. Backup: $BackupDir"
}

Write-Host "`n========== BACKUP ==========" -ForegroundColor Cyan
Write-Host $BackupDir
Write-Host "`nPerapian EOF selesai; isi dokumentasi selain whitespace akhir tidak diubah." -ForegroundColor Green
