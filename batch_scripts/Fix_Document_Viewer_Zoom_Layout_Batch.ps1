$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$ViewerPath = Join-Path $Root "core\document_viewer.py"
$Python = Join-Path $Root ".venv-scanner\Scripts\python.exe"

if (-not (Test-Path $ViewerPath -PathType Leaf)) {
    throw "core\document_viewer.py tidak ditemukan. Jalankan dari root proyek."
}
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Source = [System.IO.File]::ReadAllText($ViewerPath, [System.Text.Encoding]::UTF8)

$Required = @(
    "self.zoom = 1.0",
    "def _draw_page(self):",
    "def _set_zoom(self, delta):"
)
foreach ($Pattern in $Required) {
    if (-not $Source.Contains($Pattern)) {
        throw "Pola yang diharapkan tidak ditemukan: $Pattern. Tidak ada perubahan dilakukan."
    }
}

$BackupName = "before_document_viewer_layout_fix_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path $Root "backups\$BackupName"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item $ViewerPath (Join-Path $BackupDir "document_viewer.py") -Force
Write-Host "Backup dibuat: $BackupDir"

# Use integer zoom state to avoid floating-point accumulation.
$Source = $Source.Replace("self.zoom = 1.0", "self.zoom_percent = 100")
$Source = $Source.Replace("int(794 * self.zoom)", "int(794 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(1123 * self.zoom)", "int(1123 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(76 * self.zoom)", "int(76 * self.zoom_percent / 100)")
$Source = $Source.Replace("(460 * self.zoom)", "(460 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(10 * self.zoom)", "int(10 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(24 * self.zoom)", "int(24 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(14 * self.zoom)", "int(14 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(9 * self.zoom)", "int(9 * self.zoom_percent / 100)")
$Source = $Source.Replace("int(19 * self.zoom)", "int(19 * self.zoom_percent / 100)")
$Source = $Source.Replace('int(self.zoom * 100)', 'self.zoom_percent')

$OldZoom = @'
    def _set_zoom(self, delta):
        self.zoom = min(1.5, max(0.6, self.zoom + delta))
        self._draw_page()
'@
$NewZoom = @'
    def _set_zoom(self, delta):
        # Store zoom as an integer percentage; never accumulate float fractions.
        step = 10 if delta > 0 else -10
        self.zoom_percent = min(150, max(60, self.zoom_percent + step))
        self._draw_page()
'@
if (-not $Source.Contains($OldZoom)) {
    throw "Implementasi _set_zoom tidak cocok dengan pola yang diharapkan. File belum ditulis."
}
$Source = $Source.Replace($OldZoom, $NewZoom)

# Replace fixed line advance with actual canvas text bounds so wrapped lines do not overlap.
$OldDrawLine = @'
            self.canvas.create_text(x, y, anchor="nw", text=text, font=font, fill="#111111", width=width - 2 * margin)
            y += int(19 * self.zoom_percent / 100)
'@
$NewDrawLine = @'
            text_id = self.canvas.create_text(
                x, y, anchor="nw", text=text, font=font,
                fill="#111111", width=max(100, width - 2 * margin)
            )
            text_bounds = self.canvas.bbox(text_id)
            if text_bounds:
                # Advance by the actual rendered height, including wrapped lines.
                y = text_bounds[3] + max(4, int(5 * self.zoom_percent / 100))
            else:
                y += max(18, int(20 * self.zoom_percent / 100))
'@
if (-not $Source.Contains($OldDrawLine)) {
    throw "Baris render teks tidak cocok dengan pola yang diharapkan. File belum ditulis."
}
$Source = $Source.Replace($OldDrawLine, $NewDrawLine)

# Add explicit zoom bounds and recalculate the page scroll region after drawing.
$OldRegion = '        self.canvas.configure(scrollregion=(0, 0, width + 80, height + 80))'
$NewRegion = '        self.canvas.configure(scrollregion=(0, 0, width + 80, height + 80))'
if (-not $Source.Contains($OldRegion)) {
    throw "Pengaturan scrollregion tidak ditemukan. File belum ditulis."
}

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ViewerPath, $Source, $Utf8NoBom)

Write-Host "`nMenjalankan syntax check Document Viewer..."
& $Python -m py_compile $ViewerPath
if ($LASTEXITCODE -ne 0) {
    throw "Syntax check gagal. Backup tersedia di $BackupDir"
}

Write-Host "`nMenjalankan pemeriksaan diff..."
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Periksa output di atas."
}

Write-Host "`nPerbaikan zoom dan jarak teks selesai."
Write-Host "Zoom: 60%-150%, interval 10%, nilai integer."
Write-Host "Teks: jarak vertikal mengikuti tinggi hasil render."
Write-Host "Backup: $BackupDir"
Write-Host "Syntax check: PASSED"
