#requires -Version 5.1
$ErrorActionPreference = "Stop"

# Run from the AI-QA-Assistant repository root.
$ProjectRoot = (Get-Location).Path
$Required = @(
    "docs\PROJECT_SETUP_GUIDE.md",
    "docs\PORTABLE_SETUP_GUIDE.md",
    "agent.py",
    "batch_scripts"
)

foreach ($item in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $item))) {
        throw "Repository root tidak valid atau item wajib tidak ditemukan: $item"
    }
}

$ProjectGuide = Join-Path $ProjectRoot "docs\PROJECT_SETUP_GUIDE.md"
$PortableGuide = Join-Path $ProjectRoot "docs\PORTABLE_SETUP_GUIDE.md"

function Read-TextFileWithEncoding {
    param([Parameter(Mandatory=$true)][string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $hasUtf8Bom = $bytes.Length -ge 3 -and
        $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF

    $encoding = New-Object System.Text.UTF8Encoding($hasUtf8Bom)
    $reader = New-Object System.IO.StreamReader($Path, [System.Text.Encoding]::UTF8, $true)
    try {
        $content = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }

    return @{
        Content = $content
        Encoding = $encoding
        HasUtf8Bom = $hasUtf8Bom
    }
}

$projectData = Read-TextFileWithEncoding -Path $ProjectGuide
$portableData = Read-TextFileWithEncoding -Path $PortableGuide

$projectMarker = "### Pengelolaan batch script"
$portableMarker = "- Simpan seluruh batch script pengembangan dan perbaikan di folder ``batch_scripts\``."

$projectAlreadyUpdated = $projectData.Content.Contains($projectMarker)
$portableAlreadyUpdated = $portableData.Content.Contains($portableMarker)

if ($projectAlreadyUpdated -and $portableAlreadyUpdated) {
    Write-Host "Dokumentasi sudah memuat aturan batch_scripts. Tidak ada perubahan." -ForegroundColor Yellow
    exit 0
}

if ($projectAlreadyUpdated -xor $portableAlreadyUpdated) {
    throw "Hanya satu dokumen sudah memuat marker. Hentikan untuk pemeriksaan manual; tidak ada perubahan."
}

$projectAnchor = "Periksa kebijakan perusahaan sebelum memindahkan data client, laporan, screenshot, atau evidence."
$portableAnchor = "- Backup data sebelum melakukan perubahan besar."

if (($projectData.Content.Split($projectAnchor).Count - 1) -ne 1) {
    throw "Anchor PROJECT_SETUP_GUIDE tidak ditemukan tepat satu kali. Tidak ada perubahan."
}
if (($portableData.Content.Split($portableAnchor).Count - 1) -ne 1) {
    throw "Anchor PORTABLE_SETUP_GUIDE tidak ditemukan tepat satu kali. Tidak ada perubahan."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "backups\before_batch_scripts_documentation_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

Copy-Item -LiteralPath $ProjectGuide -Destination (Join-Path $BackupDir "PROJECT_SETUP_GUIDE.md")
Copy-Item -LiteralPath $PortableGuide -Destination (Join-Path $BackupDir "PORTABLE_SETUP_GUIDE.md")

$backupProjectHash = (Get-FileHash -LiteralPath (Join-Path $BackupDir "PROJECT_SETUP_GUIDE.md") -Algorithm SHA256).Hash
$backupPortableHash = (Get-FileHash -LiteralPath (Join-Path $BackupDir "PORTABLE_SETUP_GUIDE.md") -Algorithm SHA256).Hash
$originalProjectHash = (Get-FileHash -LiteralPath $ProjectGuide -Algorithm SHA256).Hash
$originalPortableHash = (Get-FileHash -LiteralPath $PortableGuide -Algorithm SHA256).Hash

if ($backupProjectHash -ne $originalProjectHash -or $backupPortableHash -ne $originalPortableHash) {
    throw "Verifikasi backup gagal. Dokumen asli tidak diubah."
}

$projectAddition = @'

### Pengelolaan batch script

- Simpan seluruh batch script pengembangan dan perbaikan di folder `batch_scripts\`, bukan di root repository.
- Jalankan batch script dari root repository agar path relatif tetap sesuai.
- Simpan backup dan arsip di folder `backups\`.
- Jangan menghapus batch script lama atau arsip sumber sebelum memastikan penggantinya tersedia dan terverifikasi.
'@

$portableAddition = @'
- Simpan seluruh batch script pengembangan dan perbaikan di folder `batch_scripts\`, bukan di root repository.
- Jalankan batch script dari root repository agar path relatif tetap sesuai.
- Simpan backup dan arsip di folder `backups\`.
'@

$newProjectContent = $projectData.Content.Replace(
    $projectAnchor,
    $projectAnchor + $projectAddition
)
$newPortableContent = $portableData.Content.Replace(
    $portableAnchor,
    $portableAddition + "`r`n" + $portableAnchor
)

# Write to temporary files first, then replace the originals.
$tempProject = Join-Path $env:TEMP ("PROJECT_SETUP_GUIDE_" + [guid]::NewGuid().ToString() + ".md")
$tempPortable = Join-Path $env:TEMP ("PORTABLE_SETUP_GUIDE_" + [guid]::NewGuid().ToString() + ".md")

try {
    [System.IO.File]::WriteAllText($tempProject, $newProjectContent, $projectData.Encoding)
    [System.IO.File]::WriteAllText($tempPortable, $newPortableContent, $portableData.Encoding)

    # Re-check original hashes immediately before replacement.
    if ((Get-FileHash -LiteralPath $ProjectGuide -Algorithm SHA256).Hash -ne $originalProjectHash) {
        throw "PROJECT_SETUP_GUIDE berubah setelah backup. Penggantian dibatalkan."
    }
    if ((Get-FileHash -LiteralPath $PortableGuide -Algorithm SHA256).Hash -ne $originalPortableHash) {
        throw "PORTABLE_SETUP_GUIDE berubah setelah backup. Penggantian dibatalkan."
    }

    Copy-Item -LiteralPath $tempProject -Destination $ProjectGuide -Force
    Copy-Item -LiteralPath $tempPortable -Destination $PortableGuide -Force
}
finally {
    if (Test-Path -LiteralPath $tempProject) { Remove-Item -LiteralPath $tempProject -Force }
    if (Test-Path -LiteralPath $tempPortable) { Remove-Item -LiteralPath $tempPortable -Force }
}

$projectVerified = (Get-Content -LiteralPath $ProjectGuide -Raw).Contains($projectMarker)
$portableVerified = (Get-Content -LiteralPath $PortableGuide -Raw).Contains($portableMarker)

if (-not $projectVerified -or -not $portableVerified) {
    throw "Marker verifikasi tidak ditemukan setelah penulisan. Backup tersedia di: $BackupDir"
}

Write-Host "`nDOKUMENTASI DIPERBARUI" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "PROJECT_SETUP_GUIDE.md: marker ditemukan = $projectVerified"
Write-Host "PORTABLE_SETUP_GUIDE.md: marker ditemukan = $portableVerified"
Write-Host "`nAturan ditambahkan; kode aplikasi dan file Git lainnya tidak disentuh."
