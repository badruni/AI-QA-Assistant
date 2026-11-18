#requires -Version 5.1
$ErrorActionPreference = "Stop"

# Run from the AI-QA-Assistant repository root.
$ProjectRoot = (Get-Location).Path
$GitIgnore = Join-Path $ProjectRoot ".gitignore"

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git") -PathType Container)) {
    throw "Folder .git tidak ditemukan. Jalankan script dari root repository."
}
if (-not (Test-Path -LiteralPath $GitIgnore -PathType Leaf)) {
    throw ".gitignore tidak ditemukan."
}

$OriginalBytes = [System.IO.File]::ReadAllBytes($GitIgnore)
$OriginalHash = (Get-FileHash -LiteralPath $GitIgnore -Algorithm SHA256).Hash

# Decode UTF-8 while preserving whether the file has a UTF-8 BOM.
$HasBom = $OriginalBytes.Length -ge 3 -and
    $OriginalBytes[0] -eq 0xEF -and $OriginalBytes[1] -eq 0xBB -and $OriginalBytes[2] -eq 0xBF
$Utf8 = New-Object System.Text.UTF8Encoding($HasBom)
$Content = $Utf8.GetString($OriginalBytes)

$Lines = [System.Collections.Generic.List[string]]::new()
foreach ($line in ($Content -split "`r?`n")) {
    $Lines.Add($line)
}

$RuleIndexes = @()
$CommentIndexes = @()

for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i].Trim() -eq "/batch_scripts/") {
        $RuleIndexes += $i
    }
    if ($Lines[$i].Trim() -eq "# Local development batch scripts") {
        $CommentIndexes += $i
    }
}

if ($RuleIndexes.Count -eq 0) {
    Write-Host "Aturan /batch_scripts/ tidak ditemukan. Tidak ada perubahan." -ForegroundColor Yellow
    exit 0
}
if ($RuleIndexes.Count -gt 1) {
    throw "Ditemukan lebih dari satu aturan /batch_scripts/. Hentikan untuk pemeriksaan manual."
}

# Remove the broad ignore rule and its immediately preceding matching comment only.
$RuleIndex = $RuleIndexes[0]
$Lines.RemoveAt($RuleIndex)

foreach ($commentIndex in $CommentIndexes) {
    # Account for the removed rule shifting later line positions.
    $adjustedIndex = $commentIndex
    if ($commentIndex -gt $RuleIndex) { $adjustedIndex-- }

    if ($adjustedIndex -ge 0 -and $adjustedIndex -lt $Lines.Count) {
        $isOnlyWhitespaceBetween = $true
        for ($j = $adjustedIndex + 1; $j -lt $Lines.Count; $j++) {
            if (-not [string]::IsNullOrWhiteSpace($Lines[$j])) {
                $isOnlyWhitespaceBetween = $false
            }
            break
        }

        if ($isOnlyWhitespaceBetween) {
            $Lines.RemoveAt($adjustedIndex)
        }
    }
}

# Preserve the original newline convention.
$Newline = "`n"
if ($Content.Contains("`r`n")) { $Newline = "`r`n" }

$NewContent = [string]::Join($Newline, $Lines)
if ($Content.EndsWith("`n") -or $Content.EndsWith("`r")) {
    $NewContent = $NewContent.TrimEnd("`r", "`n") + $Newline
}

if ($NewContent -eq $Content) {
    throw "Tidak ada perubahan efektif yang dapat dibuat. File asli dipertahankan."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "backups\before_gitignore_batch_scripts_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$BackupFile = Join-Path $BackupDir ".gitignore"
Copy-Item -LiteralPath $GitIgnore -Destination $BackupFile

$BackupHash = (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash
if ($BackupHash -ne $OriginalHash) {
    throw "Hash backup .gitignore tidak cocok. File asli tidak diubah."
}

$TempFile = Join-Path $env:TEMP ("gitignore_" + [guid]::NewGuid().ToString() + ".tmp")

try {
    [System.IO.File]::WriteAllText($TempFile, $NewContent, $Utf8)

    if ((Get-FileHash -LiteralPath $GitIgnore -Algorithm SHA256).Hash -ne $OriginalHash) {
        throw ".gitignore berubah sejak pemeriksaan awal. Penggantian dibatalkan."
    }

    Copy-Item -LiteralPath $TempFile -Destination $GitIgnore -Force
}
finally {
    if (Test-Path -LiteralPath $TempFile) {
        Remove-Item -LiteralPath $TempFile -Force
    }
}

$FinalContent = [System.IO.File]::ReadAllText($GitIgnore, [System.Text.Encoding]::UTF8)
if ($FinalContent -match '(?m)^\s*/batch_scripts/\s*$') {
    throw "Aturan /batch_scripts/ masih ditemukan setelah perubahan. Backup: $BackupDir"
}

Write-Host "`nGITIGNORE DIPERBARUI" -ForegroundColor Green
Write-Host "Backup: $BackupFile"
Write-Host "Hash backup: $BackupHash"
Write-Host "Aturan /batch_scripts/ sudah dihapus."
Write-Host "Aturan ignore lainnya dipertahankan."
Write-Host "Staging area, kode aplikasi, dan batch script tidak diubah."
