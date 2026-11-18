#requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Python = Join-Path $Root ".venv-scanner\Scripts\python.exe"
$Viewer = Join-Path $Root "core\document_viewer.py"
if (-not (Test-Path $Python -PathType Leaf)) { throw "Python scanner tidak ditemukan: $Python" }
if (-not (Test-Path $Viewer -PathType Leaf)) { throw "Document Viewer tidak ditemukan: $Viewer" }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Root "backups\before_document_viewer_zoom_layout_fix_$Stamp"
New-Item -ItemType Directory -Path (Join-Path $Backup "core") -Force | Out-Null
Copy-Item $Viewer (Join-Path $Backup "core\document_viewer.py")
Write-Host "Backup dibuat: $Backup" -ForegroundColor Green

$Patch = @'
from pathlib import Path

path = Path("core/document_viewer.py")
source = path.read_text(encoding="utf-8-sig")

old = 'add_text(self.project_id, "h2", after=8, align="center")'
new = 'add_text(self.project_id, "title", after=8, align="center")'
if old not in source:
    raise SystemExit("Anchor nama klien pada cover tidak ditemukan.")
source = source.replace(old, new, 1)

old = '''                            "cells": wrapped, "header": is_header,
                        })'''
new = '''                            "cells": wrapped, "header": is_header,
                            "line_height": line_height,
                        })'''
if old not in source:
    raise SystemExit("Anchor metadata tinggi baris tabel tidak ditemukan.")
source = source.replace(old, new, 1)

old = '''        for index, (title, page_number) in enumerate(section_start_pages):
            if index + 1 < len(toc_lines):
                toc_lines[index + 1]["text"] = f"{title}  ................................  {page_number + 1}"'''
new = '''        toc_font = self._fonts["body"]
        dot_width = max(1, toc_font.measure("."))
        for index, (title, page_number) in enumerate(section_start_pages):
            if index + 1 < len(toc_lines):
                page_label = str(page_number)
                occupied = toc_font.measure(title) + toc_font.measure(page_label) + toc_font.measure("  ")
                dot_count = max(3, int((CONTENT_W - occupied) / dot_width))
                toc_lines[index + 1]["text"] = f"{title}  {'.' * dot_count}  {page_label}"'''
if old not in source:
    raise SystemExit("Blok pengisian Daftar Isi tidak ditemukan.")
source = source.replace(old, new, 1)

old = 'font_size = max(7, int(base_font.cget("size") * scale))'
new = 'font_size = max(5, int(round(base_font.cget("size") * scale)))'
if old not in source:
    raise SystemExit("Anchor skala font teks tidak ditemukan.")
source = source.replace(old, new, 1)

old = '''                font = ("Arial", max(7, int((9 if op["header"] else 9) * scale)),
                        "bold" if op["header"] else "normal")'''
new = '''                font = ("Arial", max(5, int(round(9 * scale))),
                        "bold" if op["header"] else "normal")'''
if old not in source:
    raise SystemExit("Anchor skala font tabel tidak ditemukan.")
source = source.replace(old, new, 1)

old = '''                    line_y = y + max(5, int(6 * scale))
                    for line in lines:
                        self.canvas.create_text(
                            cursor + max(4, int(6 * scale)), line_y,
                            anchor="nw", text=line, font=font, fill=text_fill,
                            width=max(10, cell_w - int(12 * scale))
                        )
                        line_y += max(10, int(12 * scale))'''
new = '''                    horizontal_pad = max(2, int(round(6 * scale)))
                    vertical_pad = max(2, int(round(6 * scale)))
                    line_step = max(1, int(round(op.get("line_height", 15) * scale)))
                    for line_index, line in enumerate(lines):
                        line_y = y + vertical_pad + (line_index * line_step)
                        self.canvas.create_text(
                            cursor + horizontal_pad, line_y,
                            anchor="nw", text=line, font=font, fill=text_fill,
                            width=max(5, cell_w - (2 * horizontal_pad))
                        )'''
if old not in source:
    raise SystemExit("Anchor jarak teks tabel tidak ditemukan.")
source = source.replace(old, new, 1)

old = '''        for word in words:
            candidate = word if not current else current + " " + word
            if current and font.measure(candidate) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate'''
new = '''        for word in words:
            candidate = word if not current else current + " " + word
            if font.measure(candidate) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            fragment = ""
            for character in word:
                candidate_fragment = fragment + character
                if fragment and font.measure(candidate_fragment) > max_width:
                    lines.append(fragment)
                    fragment = character
                else:
                    fragment = candidate_fragment
            current = fragment'''
if old not in source:
    raise SystemExit("Anchor wrapping teks tidak ditemukan.")
source = source.replace(old, new, 1)

path.write_text(source, encoding="utf-8")
'@

$PatchPath = Join-Path $env:TEMP "patch_document_viewer_zoom_layout.py"
Set-Content -Path $PatchPath -Value $Patch -Encoding UTF8
& $Python $PatchPath
if ($LASTEXITCODE -ne 0) { throw "Patch Python gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== VERIFIKASI SINTAKS ==========" -ForegroundColor Cyan
& $Python -m py_compile ".\core\document_viewer.py"
if ($LASTEXITCODE -ne 0) { throw "Kompilasi gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
& $Python -m unittest tests.test_document_content_model tests.test_documentation_generator -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup tersedia di: $Backup" }

Write-Host "`nBATCH SELESAI: skala font, wrapping, cover, dan Daftar Isi diperbarui." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Catatan: Draft tersimpan tidak diubah; periksa visual pada zoom 60%, 70%, 100%, dan 150%."
