#requires -Version 5.1
$ErrorActionPreference = "Stop"

# Run this script from the AI-QA-Assistant repository root.
$ProjectRoot = (Get-Location).Path
$RequiredRootItems = @("agent.py", "core", "modules", "tests", "batch_scripts")

foreach ($item in $RequiredRootItems) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $item))) {
        throw "Repository root tidak valid atau item wajib tidak ditemukan: $item"
    }
}

$SourceFiles = @(
    "content_model_source.txt",
    "docx_renderer_source.txt",
    "viewer_source.txt"
)

$Missing = @(
    $SourceFiles | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $_) -PathType Leaf)
    }
)

if ($Missing.Count -gt 0) {
    throw "File sumber tidak lengkap. Tidak ada perubahan dilakukan: $($Missing -join ', ')"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveDir = Join-Path $ProjectRoot "backups\source_review_texts_$Stamp"

if (Test-Path -LiteralPath $ArchiveDir) {
    throw "Folder arsip sudah ada; hentikan agar tidak menimpa data: $ArchiveDir"
}

New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null

try {
    $Manifest = @()

    foreach ($name in $SourceFiles) {
        $source = Join-Path $ProjectRoot $name
        $destination = Join-Path $ArchiveDir $name

        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        Copy-Item -LiteralPath $source -Destination $destination

        $archiveHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash

        if ($sourceHash -ne $archiveHash) {
            throw "Verifikasi hash gagal untuk $name. File sumber asli dipertahankan."
        }

        $Manifest += [PSCustomObject]@{
            File = $name
            SHA256 = $sourceHash
            SizeBytes = (Get-Item -LiteralPath $source).Length
            ArchiveVerified = $true
        }
    }

    $ManifestPath = Join-Path $ArchiveDir "ARCHIVE_MANIFEST.csv"
    $Manifest | Export-Csv -LiteralPath $ManifestPath -NoTypeInformation -Encoding UTF8

    # Verify the manifest exists before removing only the three verified root copies.
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Manifest tidak berhasil dibuat. File sumber asli dipertahankan."
    }

    foreach ($name in $SourceFiles) {
        $source = Join-Path $ProjectRoot $name
        $destination = Join-Path $ArchiveDir $name

        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            throw "File arsip tidak ditemukan: $destination. File sumber asli dipertahankan."
        }

        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $archiveHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash

        if ($sourceHash -ne $archiveHash) {
            throw "Hash berubah sebelum pemindahan $name. File sumber asli dipertahankan."
        }
    }

    foreach ($name in $SourceFiles) {
        Remove-Item -LiteralPath (Join-Path $ProjectRoot $name) -Force
    }

    Write-Host "`nARSIP BERHASIL DIVERIFIKASI" -ForegroundColor Green
    Write-Host "Lokasi: $ArchiveDir"
    Write-Host "`nManifest:"
    Import-Csv -LiteralPath $ManifestPath | Format-Table -AutoSize

    Write-Host "`nFile sumber di root yang tersisa:"
    foreach ($name in $SourceFiles) {
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot $name)) {
            Write-Host "MASIH ADA: $name" -ForegroundColor Yellow
        } else {
            Write-Host "Sudah diarsipkan: $name"
        }
    }

    Write-Host "`nTidak ada kode aplikasi, batch script, test, atau arsip ZIP yang diubah."
}
catch {
    Write-Host "`nTerjadi kesalahan: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Folder arsip yang sudah dibuat dipertahankan untuk pemeriksaan: $ArchiveDir"
    Write-Host "File sumber asli tidak dihapus kecuali proses verifikasi seluruh file sudah selesai."
    throw
}
