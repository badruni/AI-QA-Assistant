$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path
$ViewerPath = Join-Path $ProjectRoot "core\document_viewer.py"
$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"

if (-not (Test-Path $ViewerPath)) { throw "File core\document_viewer.py tidak ditemukan. Jalankan dari root repository." }
if (-not (Test-Path $Python)) { throw "Python scanner tidak ditemukan: $Python" }

$BackupName = "before_document_viewer_toc_alignment_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupRoot = Join-Path $ProjectRoot "backups\$BackupName"
New-Item -ItemType Directory -Path (Join-Path $BackupRoot "core") -Force | Out-Null
Copy-Item $ViewerPath (Join-Path $BackupRoot "core\document_viewer.py")
Write-Host "Backup dibuat: $BackupRoot" -ForegroundColor Cyan

$PatchPath = Join-Path $env:TEMP "patch_document_viewer_toc_alignment.py"
@'
from pathlib import Path

path = Path("core/document_viewer.py")
source = path.read_text(encoding="utf-8")

toc_start_marker = "        # Contents page generated from semantic section headings."
toc_end_marker = "        for section in self.content[\"sections\"]:\n            section_start_pages.append((section[\"title\"], len(pages)))"
start = source.find(toc_start_marker)
end = source.find(toc_end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("Blok awal Daftar Isi tidak cocok; file tidak diubah.")
end += len(toc_end_marker)

new_toc = """        # Contents page: title, dotted leader, and page number are separate elements.
        add_text("Daftar Isi", "h1", after=18)
        toc_rows = []
        toc_font = self._fonts["body"]
        toc_line_h = max(toc_font.metrics("linespace") + 3, 14)
        for section_index, section in enumerate(self.content["sections"]):
            ensure(toc_line_h + 8)
            row = {
                "kind": "toc_row",
                "x": MARGIN_X,
                "y": y,
                "width": CONTENT_W,
                "title": section["title"],
                "page_number": "",
                "font": "body",
            }
            operations.append(row)
            toc_rows.append(row)
            y += toc_line_h + 8
        new_page()

        for section_index, section in enumerate(self.content["sections"]):
            section_start_pages.append((section_index, len(pages)))"""
source = source[:start] + new_toc + source[end:]

final_start_marker = "        # Append logical page references to the contents entries."
final_end_marker = "        return pages or [[]]"
start = source.find(final_start_marker)
end = source.find(final_end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("Blok pengisian nomor halaman Daftar Isi tidak cocok; file tidak diubah.")

new_final = """        # Fill page numbers after pagination determines actual section pages.
        for section_index, page_number in section_start_pages:
            if section_index < len(toc_rows):
                toc_rows[section_index]["page_number"] = str(page_number)
"""
source = source[:start] + new_final + source[end:]

anchor = '            elif op["kind"] == "table_row":'
draw_block = """            elif op["kind"] == "toc_row":
                base_font = self._fonts[op["font"]]
                font_size = max(7, int(base_font.cget("size") * scale))
                font = ("Arial", font_size)
                title = op["title"]
                page_label = str(op.get("page_number", ""))
                left_x = sx(op["x"])
                right_x = sx(op["x"] + op["width"])
                row_y = sy(op["y"])
                self.canvas.create_text(
                    left_x, row_y, anchor="nw", text=title,
                    font=font, fill=TEXT
                )
                self.canvas.create_text(
                    right_x, row_y, anchor="ne", text=page_label,
                    font=font, fill=TEXT
                )
                title_width = base_font.measure(title) * scale
                page_width = base_font.measure(page_label) * scale
                leader_start = left_x + title_width + max(5, int(8 * scale))
                leader_end = right_x - page_width - max(5, int(8 * scale))
                if leader_end > leader_start:
                    leader_y = row_y + max(
                        5, int(base_font.metrics("linespace") * scale * 0.72)
                    )
                    self.canvas.create_line(
                        leader_start, leader_y, leader_end, leader_y,
                        fill="#555555", width=1, dash=(1, 2)
                    )
            elif op["kind"] == "table_row":"""
if anchor not in source:
    raise SystemExit("Anchor table_row tidak ditemukan; file tidak diubah.")
source = source.replace(anchor, draw_block, 1)

path.write_text(source, encoding="utf-8")
print("Daftar Isi diperbarui: judul kiri, dotted leader dinamis, nomor halaman rata kanan.")
'@
Set-Content -Path $PatchPath -Encoding UTF8

try {
    & $Python $PatchPath
    if ($LASTEXITCODE -ne 0) { throw "Patch Python gagal." }

    Write-Host "`n========== VERIFIKASI SINTAKS ==========" -ForegroundColor Cyan
    & $Python -m py_compile $ViewerPath
    if ($LASTEXITCODE -ne 0) { throw "Verifikasi sintaks gagal." }

    Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
    & $Python -m unittest tests.test_document_content_model tests.test_documentation_generator -v
    if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal." }

    Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
    git diff --check
    if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal." }

    Write-Host "`nBATCH SELESAI: Daftar Isi dirapikan." -ForegroundColor Green
    Write-Host "Backup: $BackupRoot"
    Write-Host "Catatan: draft tersimpan tidak diubah; verifikasi visual tetap diperlukan."
}
finally {
    Remove-Item $PatchPath -Force -ErrorAction SilentlyContinue
}
