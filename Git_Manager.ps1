[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor DarkCyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor DarkCyan
}

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$GitArgs)
    $output = & git @GitArgs 2>&1
    $exitCode = $LASTEXITCODE
    if ($output) { $output | ForEach-Object { Write-Host $_ } }
    if ($exitCode -ne 0) {
        throw "Perintah Git gagal (exit code $exitCode): git $($GitArgs -join ' ')"
    }
    return $output
}

function Test-GitRepository {
    & git rev-parse --show-toplevel *> $null
    if ($LASTEXITCODE -ne 0) { throw "Folder ini bukan Git repository." }
    $script:RepoRoot = (& git rev-parse --show-toplevel).Trim()
    Set-Location $script:RepoRoot
}

function Show-GitStatus {
    Write-Section "GIT STATUS"
    Invoke-Git -GitArgs @("status", "--short", "--branch") | Out-Null
    Write-Host "`nBranch:"
    Invoke-Git -GitArgs @("branch", "--show-current") | Out-Null
    Write-Host "Remote:"
    Invoke-Git -GitArgs @("remote", "-v") | Out-Null
    Write-Host "`nCommit terbaru:"
    Invoke-Git -GitArgs @("log", "-5", "--oneline", "--decorate") | Out-Null
}

function Get-BackupPaths {
    $paths = @("agent.py", "core", "modules", "tests", "docs", "config", ".gitignore")
    foreach ($path in $paths) {
        if (Test-Path (Join-Path $script:RepoRoot $path)) { $path }
    }

    $allowedPrefixes = @("Implement_", "Fix_", "Setup_", "Git_Manager")
    Get-ChildItem -LiteralPath $script:RepoRoot -File -Filter "*.ps1" |
        Where-Object {
            $name = $_.Name
            foreach ($prefix in $allowedPrefixes) {
                if ($name.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
            }
            return $false
        } | ForEach-Object { $_.Name }
}

function Invoke-PushPendingCommits {
    Write-Section "PUSH COMMIT KE GITHUB"

    $upstream = & git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $upstream) {
        Write-Host "Branch belum memiliki upstream. Push dihentikan; atur upstream secara manual terlebih dahulu." -ForegroundColor Yellow
        return
    }

    $aheadCount = & git rev-list --count "$($upstream.Trim())..HEAD"
    if ($LASTEXITCODE -ne 0) { throw "Gagal memeriksa jumlah commit yang belum di-push." }
    $aheadCount = [int]$aheadCount

    if ($aheadCount -le 0) {
        Write-Host "Tidak ada commit lokal yang tertinggal dari remote. Branch sudah sinkron." -ForegroundColor Green
        return
    }

    Write-Host "Upstream : $($upstream.Trim())"
    Write-Host "Commit yang belum di-push: $aheadCount" -ForegroundColor Yellow
    Invoke-Git -GitArgs @("log", "--oneline", "$($upstream.Trim())..HEAD") | Out-Null
    $confirmation = Read-Host "Push $aheadCount commit ke upstream sekarang? (Y/N)"
    if ($confirmation -in @("Y", "y")) {
        Invoke-Git -GitArgs @("push") | Out-Null
        Write-Host "Push berhasil." -ForegroundColor Green
    } else {
        Write-Host "Push dilewati. Commit tetap tersimpan lokal." -ForegroundColor Yellow
    }
}

function Invoke-Backup {
    param([switch]$PushAfterCommit)
    Write-Section "BACKUP KODE KE GIT"

    & git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Ada file yang sudah di-stage sebelumnya. Periksa git status dan selesaikan staging tersebut sebelum memakai Git Manager."
    }

    $status = & git status --porcelain
    if (-not $status) {
        Write-Host "Tidak ada perubahan baru untuk di-commit." -ForegroundColor Yellow
        if ($PushAfterCommit) {
            # Tetap periksa commit lokal yang mungkin belum dikirim ke remote.
            Invoke-PushPendingCommits
        }
        return
    }

    $paths = @(Get-BackupPaths)
    Write-Host "File/folder allowlist yang akan di-stage:"
    foreach ($path in $paths) { Write-Host "  - $path" }
    Write-Host "`nFolder projects/, logs/, reports/, backups/, evidence, virtual environment, dan file .env tidak dimasukkan oleh allowlist."
    $confirmation = Read-Host "Lanjutkan staging file allowlist? (Y/N)"
    if ($confirmation -notin @("Y", "y")) { Write-Host "Backup dibatalkan."; return }
    if ($paths.Count -eq 0) { throw "Tidak ada path allowlist yang tersedia." }

    Invoke-Git -GitArgs (@("add", "--") + $paths) | Out-Null
    Write-Section "FILE YANG AKAN DI-COMMIT"
    Invoke-Git -GitArgs @("diff", "--cached", "--name-status") | Out-Null

    $message = Read-Host "Pesan backup (kosong = otomatis)"
    if ([string]::IsNullOrWhiteSpace($message)) { $message = "Backup: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" }
    $confirmation = Read-Host "Buat commit dengan file staged di atas? (Y/N)"
    if ($confirmation -notin @("Y", "y")) {
        Write-Host "Commit dibatalkan. File tetap berada dalam staging Git." -ForegroundColor Yellow
        return
    }

    Invoke-Git -GitArgs @("commit", "-m", $message) | Out-Null
    Write-Host "Backup commit berhasil dibuat." -ForegroundColor Green

    if ($PushAfterCommit) {
        Invoke-PushPendingCommits
    }
}

function Show-CommitHistory {
    Write-Section "RIWAYAT COMMIT (20 TERAKHIR)"
    Invoke-Git -GitArgs @("log", "-20", "--date=short", "--pretty=format:%h  %ad  %s") | Out-Null
}

function Invoke-Restore {
    Write-Section "RESTORE DARI COMMIT"
    $status = & git status --porcelain
    if ($status) {
        Write-Host "Restore dihentikan karena working tree belum bersih." -ForegroundColor Yellow
        Write-Host "Buat backup/commit terlebih dahulu. Perubahan lokal tidak akan dibuang."
        Invoke-Git -GitArgs @("status", "--short", "--branch") | Out-Null
        return
    }

    $entries = @(& git log -20 --format="%H|%h|%ad|%s" --date=short)
    if ($LASTEXITCODE -ne 0 -or $entries.Count -eq 0) { throw "Riwayat commit tidak tersedia." }
    Write-Host "Pilih commit tujuan:"
    for ($i = 0; $i -lt $entries.Count; $i++) {
        $parts = $entries[$i] -split "\|", 4
        Write-Host ("{0}. {1}  {2}  {3}" -f ($i + 1), $parts[1], $parts[2], $parts[3])
    }

    $selection = Read-Host "Nomor commit (0 untuk batal)"
    if ($selection -notmatch '^\d+$') { Write-Host "Pilihan tidak valid."; return }
    $number = [int]$selection
    if ($number -eq 0) { Write-Host "Restore dibatalkan."; return }
    if ($number -lt 1 -or $number -gt $entries.Count) { Write-Host "Nomor commit di luar daftar."; return }

    $parts = $entries[$number - 1] -split "\|", 4
    $targetHash = $parts[0]
    $targetShort = $parts[1]
    $targetMessage = $parts[3]
    Write-Host "`nFile TERTRACK akan disamakan dengan commit:"
    Write-Host "$targetShort - $targetMessage" -ForegroundColor Yellow
    Write-Host "File lokal yang di-ignore seperti projects/, logs/, dan backups/ tidak dihapus atau dipulihkan."
    $confirmation = Read-Host "Ketik RESTORE untuk melanjutkan"
    if ($confirmation -cne "RESTORE") { Write-Host "Restore dibatalkan."; return }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $recoveryBranch = "recovery/before-restore-$timestamp"
    Invoke-Git -GitArgs @("branch", $recoveryBranch, "HEAD") | Out-Null
    Write-Host "Recovery branch dibuat: $recoveryBranch" -ForegroundColor Green

    Invoke-Git -GitArgs @("restore", "--source", $targetHash, "--staged", "--worktree", "--", ".") | Out-Null
    Write-Host "`nStatus setelah restore:"
    Invoke-Git -GitArgs @("status", "--short", "--branch") | Out-Null

    $confirmation = Read-Host "Simpan kondisi restore sebagai commit baru? (Y/N)"
    if ($confirmation -in @("Y", "y")) {
        Invoke-Git -GitArgs @("commit", "-m", "Restore tracked files to $targetShort") | Out-Null
        Write-Host "Restore disimpan sebagai commit baru. Riwayat lama tetap dipertahankan." -ForegroundColor Green
    } else {
        Write-Host "Restore diterapkan ke working tree/index tetapi belum di-commit. Recovery branch: $recoveryBranch"
    }
    Write-Host "Push tidak dilakukan otomatis setelah restore."
}

try {
    Test-GitRepository
    while ($true) {
        Write-Section "AI QA ASSISTANT - GIT MANAGER"
        Write-Host "Repository : $script:RepoRoot"
        Write-Host "Branch     : $((& git branch --show-current).Trim())"
        Write-Host "`n1. Backup (Commit)"
        Write-Host "2. Backup + Push ke GitHub"
        Write-Host "3. Restore dari Commit"
        Write-Host "4. Lihat Riwayat Backup"
        Write-Host "5. Periksa Git Status"
        Write-Host "6. Keluar`n"
        $choice = Read-Host "Pilih menu"
        try {
            switch ($choice) {
                "1" { Invoke-Backup }
                "2" { Invoke-Backup -PushAfterCommit }
                "3" { Invoke-Restore }
                "4" { Show-CommitHistory }
                "5" { Show-GitStatus }
                "6" { Write-Host "Git Manager ditutup."; return }
                default { Write-Host "Pilihan tidak valid." -ForegroundColor Yellow }
            }
        } catch { Write-Host "`n[ERROR] $($_.Exception.Message)" -ForegroundColor Red }
        if ($choice -ne "6") { [void](Read-Host "Tekan Enter untuk kembali ke menu") }
    }
} catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
