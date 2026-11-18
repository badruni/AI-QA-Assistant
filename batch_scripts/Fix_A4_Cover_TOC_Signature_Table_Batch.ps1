#requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Python = Join-Path $Root ".venv-scanner\Scripts\python.exe"
$Viewer = Join-Path $Root "core\document_viewer.py"
$Docx = Join-Path $Root "core\docx_renderer.py"
foreach ($p in @($Python, $Viewer, $Docx)) {
    if (-not (Test-Path $p -PathType Leaf)) { throw "File wajib tidak ditemukan: $p" }
}
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Root "backups\before_a4_cover_toc_table_fix_$Stamp"
New-Item -ItemType Directory -Path (Join-Path $Backup "core") -Force | Out-Null
Copy-Item $Viewer (Join-Path $Backup "core\document_viewer.py")
Copy-Item $Docx (Join-Path $Backup "core\docx_renderer.py")
Write-Host "Backup dibuat: $Backup" -ForegroundColor Green

$Patch = @'
from pathlib import Path

viewer_path = Path("core/document_viewer.py")
source = viewer_path.read_text(encoding="utf-8-sig")
start = source.index("    def _paginate(self):")
end = source.index("    def _build(self):", start)

new_paginate = """    def _paginate(self):
        pages = [[]]
        y = MARGIN_TOP
        operations = pages[-1]
        section_start_pages = []

        def new_page():
            nonlocal y, operations
            pages.append([])
            operations = pages[-1]
            y = MARGIN_TOP

        def ensure(height):
            nonlocal y
            if y + height > CONTENT_BOTTOM and operations:
                new_page()

        def add_text(text, font_key, before=0, after=6, indent=0, marker=None, align="left"):
            nonlocal y
            font = self._fonts[font_key]
            y += before
            lines = self._wrap(text, font, CONTENT_W - indent)
            line_h = max(font.metrics("linespace") + 3, 14)
            for index, line in enumerate(lines):
                ensure(line_h)
                operations.append({
                    "kind": "text", "x": MARGIN_X + indent, "y": y,
                    "text": line, "font": font_key,
                    "marker": marker if index == 0 else None,
                    "align": align,
                })
                y += line_h
            y += after

        # Cover page: centered title and project identity.
        y = 285
        add_text(self.content["title"], "title", after=18, align="center")
        add_text(self.project_id, "h2", after=8, align="center")
        add_text("User Acceptance Testing", "h2", after=10, align="center")
        add_text(f"{self.version.get('version', 'Draft 1')} | {self.version.get('status', 'NEEDS_REVIEW')}",
                 "body", after=0, align="center")
        new_page()

        # Contents page generated from semantic section headings.
        add_text("Daftar Isi", "h1", after=18)
        toc_ops = operations
        for section in self.content["sections"]:
            add_text(section["title"], "body", after=8)
        new_page()

        for section in self.content["sections"]:
            section_start_pages.append((section["title"], len(pages)))
            add_text(section["title"], "h1", before=8, after=8)
            for block in section["blocks"]:
                kind = block["type"]
                if kind == "heading":
                    key = {1: "h1", 2: "h2", 3: "h3"}[block["level"]]
                    add_text(block["text"], key, before=8, after=6)
                elif kind == "paragraph":
                    add_text(block["text"], "body", before=2, after=9)
                elif kind in ("bullet_list", "numbered_list"):
                    for index, item in enumerate(block["items"], 1):
                        marker = "•" if kind == "bullet_list" else f"{index}."
                        add_text(item, "body", before=1, after=4, indent=20, marker=marker)
                elif kind == "table":
                    if block.get("caption"):
                        add_text(block["caption"], "caption", before=4, after=5)
                    headers = block["headers"]
                    col_count = len(headers)
                    widths = [CONTENT_W / col_count] * col_count
                    normalized_headers = [str(value).strip().lower() for value in headers]
                    if col_count == 2:
                        widths = [CONTENT_W * 0.32, CONTENT_W * 0.68]
                    elif col_count == 4 and any("paraf" in h or "tanda tangan" in h for h in normalized_headers):
                        widths = [CONTENT_W * 0.16, CONTENT_W * 0.22, CONTENT_W * 0.20, CONTENT_W * 0.42]
                    elif col_count >= 6:
                        widths = [CONTENT_W * 0.11] + [CONTENT_W * 0.89 / (col_count - 1)] * (col_count - 1)

                    def row_lines(values, font_key):
                        font = self._fonts[font_key]
                        return [self._wrap(value, font, max(24, width - 14))
                                for value, width in zip(values, widths)]

                    all_rows = [(headers, True)] + [(row, False) for row in block["rows"]]
                    for values, is_header in all_rows:
                        key = "table_header" if is_header else "table_body"
                        wrapped = row_lines(values, key)
                        line_count = max((len(cell) for cell in wrapped), default=1)
                        line_height = self._fonts[key].metrics("linespace") + 4
                        row_height = max(30, line_count * line_height + 14)
                        ensure(row_height)
                        operations.append({
                            "kind": "table_row", "x": MARGIN_X, "y": y,
                            "widths": widths, "height": row_height,
                            "cells": wrapped, "header": is_header,
                        })
                        y += row_height
                    y += 10
                elif kind == "image":
                    image_height = 230
                    ensure(image_height + 28)
                    operations.append({
                        "kind": "image", "x": MARGIN_X, "y": y,
                        "width": CONTENT_W, "height": image_height,
                        "evidence_id": block["evidence_id"],
                        "caption": block.get("caption", ""),
                    })
                    y += image_height + 8
                    if block.get("caption"):
                        add_text(block["caption"], "caption", after=8)
                elif kind == "page_break":
                    new_page()

        # Append logical page references to the contents entries.
        toc_lines = [op for op in toc_ops if op.get("kind") == "text"]
        for index, (title, page_number) in enumerate(section_start_pages):
            if index + 1 < len(toc_lines):
                toc_lines[index + 1]["text"] = f"{title}  ................................  {page_number + 1}"
        return pages or [[]]

"""
source = source[:start] + new_paginate + source[end:]

old = """                self.canvas.create_text(
                    sx(op["x"]), sy(op["y"]), anchor="nw",
                    text=op["text"], font=font, fill=TEXT
                )"""
new = """                if op.get("align") == "center":
                    self.canvas.create_text(
                        sx(PAGE_W / 2), sy(op["y"]), anchor="n",
                        text=op["text"], font=font, fill=TEXT,
                        width=max(100, int(CONTENT_W * scale)), justify="center"
                    )
                else:
                    self.canvas.create_text(
                        sx(op["x"]), sy(op["y"]), anchor="nw",
                        text=op["text"], font=font, fill=TEXT
                    )"""
if old not in source:
    raise SystemExit("Anchor render text tidak ditemukan.")
source = source.replace(old, new, 1)
viewer_path.write_text(source, encoding="utf-8")

docx_path = Path("core/docx_renderer.py")
docx_source = docx_path.read_text(encoding="utf-8-sig")
old_title = """    title = doc.add_heading(content["title"], level=0)
    title.paragraph_format.space_after = Pt(14)"""
new_title = """    title = doc.add_heading(content["title"], level=0)
    title.alignment = 1
    title.paragraph_format.space_before = Pt(100)
    title.paragraph_format.space_after = Pt(18)"""
if old_title not in docx_source:
    raise SystemExit("Anchor cover title DOCX tidak ditemukan.")
docx_source = docx_source.replace(old_title, new_title, 1)

old_meta = """    p = doc.add_paragraph(f"Project ID: {project_id}")
    _style_paragraph(p, after=3, line=1.0)
    p = doc.add_paragraph(f"Document ID: {document_id} | Versi: {version_no:04d}")
    _style_paragraph(p, after=12, line=1.0)

    evidence_records = list_evidence(project_id)"""
new_meta = """    p = doc.add_paragraph(project.get("project_name", project_id))
    p.alignment = 1
    _style_paragraph(p, after=8, line=1.0)
    for run in p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(14)
        run.bold = True
    p = doc.add_paragraph("User Acceptance Testing")
    p.alignment = 1
    _style_paragraph(p, after=8, line=1.0)
    for run in p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(12)
    p = doc.add_paragraph(f"Project ID: {project_id} | Document ID: {document_id} | Versi: {version_no:04d}")
    p.alignment = 1
    _style_paragraph(p, after=12, line=1.0)
    doc.add_page_break()

    toc_heading = doc.add_heading("Daftar Isi", level=1)
    toc_heading.paragraph_format.keep_with_next = True
    toc = doc.add_paragraph()
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), 'TOC \\\\o "1-3" \\\\h \\\\z \\\\u')
    toc._p.append(field)
    _style_paragraph(toc, after=8, line=1.0)
    doc.add_page_break()

    evidence_records = list_evidence(project_id)"""
if old_meta not in docx_source:
    raise SystemExit("Anchor metadata DOCX tidak ditemukan.")
docx_source = docx_source.replace(old_meta, new_meta, 1)
docx_path.write_text(docx_source, encoding="utf-8")
'@

$PatchPath = Join-Path $env:TEMP "patch_a4_cover_toc.py"
Set-Content -Path $PatchPath -Value $Patch -Encoding UTF8
& $Python $PatchPath
if ($LASTEXITCODE -ne 0) { throw "Patch Python gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== VERIFIKASI SINTAKS ==========" -ForegroundColor Cyan
& $Python -m py_compile ".\core\document_viewer.py" ".\core\docx_renderer.py"
if ($LASTEXITCODE -ne 0) { throw "Kompilasi gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
& $Python -m unittest tests.test_document_content_model tests.test_documentation_generator -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup tersedia di: $Backup" }

Write-Host "`nBATCH SELESAI: cover rata tengah, daftar isi, dan layout tabel tanda tangan diperbarui." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Catatan: Draft tersimpan tidak diubah. Daftar isi DOCX menggunakan field Word; perlu Update Field di Word untuk mengisi nomor halaman."
