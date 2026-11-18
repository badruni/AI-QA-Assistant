#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Python = Join-Path $Root ".venv-scanner\Scripts\python.exe"
$ViewerPath = Join-Path $Root "core\document_viewer.py"
$DocxPath = Join-Path $Root "core\docx_renderer.py"
foreach ($p in @($Python, $ViewerPath, $DocxPath)) {
    if (-not (Test-Path $p -PathType Leaf)) { throw "File wajib tidak ditemukan: $p" }
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Root "backups\before_a4_renderer_visual_fix_$Stamp"
New-Item -ItemType Directory -Path (Join-Path $Backup "core") -Force | Out-Null
Copy-Item $ViewerPath (Join-Path $Backup "core\document_viewer.py")
Copy-Item $DocxPath (Join-Path $Backup "core\docx_renderer.py")
Write-Host "Backup dibuat: $Backup" -ForegroundColor Green

$ViewerSource = @'
"""Read-only A4 print preview for validated semantic QA document content."""
import math
import re
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from pathlib import Path

from core.evidence_manager import list_evidence, verify_evidence
from core.project_manager import PROJECTS_DIR
from core.document_manager import get_document
from core.document_content_model import validate_document_content


PAGE_W = 794
PAGE_H = 1123
MARGIN_X = 76
MARGIN_TOP = 76
MARGIN_BOTTOM = 68
CONTENT_W = PAGE_W - (2 * MARGIN_X)
CONTENT_BOTTOM = PAGE_H - MARGIN_BOTTOM
BLUE = "#1F4E78"
LIGHT_BLUE = "#D9EAF7"
GRID = "#8A9AA8"
TEXT = "#202124"


class DocumentViewer:
    """A semantic-block A4 renderer. Zoom scales a fixed logical page layout."""

    def __init__(self, project_id, document_id):
        self.project_id = project_id
        self.document_id = document_id
        record = get_document(project_id, document_id)
        self.manifest, self.version = record["manifest"], record["version"]
        self.content = validate_document_content(self.version["content"])
        self.zoom_percent = 100
        self.page_index = 0
        self._image_refs = []
        self.evidence_records = list_evidence(project_id)

        self.root = tk.Tk()
        self.root.title(f"Print Preview - {self.content['title']}")
        self.root.geometry("1100x850")
        self._fonts = self._make_fonts()
        self.pages = self._paginate()
        self._build()
        self._draw_page()

    def _make_fonts(self):
        return {
            "title": tkfont.Font(self.root, family="Arial", size=20, weight="bold"),
            "h1": tkfont.Font(self.root, family="Arial", size=16, weight="bold"),
            "h2": tkfont.Font(self.root, family="Arial", size=13, weight="bold"),
            "h3": tkfont.Font(self.root, family="Arial", size=11, weight="bold"),
            "body": tkfont.Font(self.root, family="Arial", size=10),
            "body_bold": tkfont.Font(self.root, family="Arial", size=10, weight="bold"),
            "small": tkfont.Font(self.root, family="Arial", size=9),
            "table_header": tkfont.Font(self.root, family="Arial", size=9, weight="bold"),
            "table_body": tkfont.Font(self.root, family="Arial", size=9),
            "caption": tkfont.Font(self.root, family="Arial", size=9, slant="italic"),
        }

    def _wrap(self, text, font, max_width):
        words = str(text).split()
        if not words:
            return [""]
        lines, current = [], ""
        for word in words:
            candidate = word if not current else current + " " + word
            if current and font.measure(candidate) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def _new_page(self, pages):
        pages.append([])
        return MARGIN_TOP

    def _paginate(self):
        pages = [[]]
        y = MARGIN_TOP
        operations = pages[-1]

        def ensure(height):
            nonlocal y, operations
            if y + height > CONTENT_BOTTOM and operations:
                y = self._new_page(pages)
                operations = pages[-1]

        def add_text(text, font_key, before=0, after=6, indent=0, marker=None):
            nonlocal y, operations
            font = self._fonts[font_key]
            y += before
            lines = self._wrap(text, font, CONTENT_W - indent)
            line_h = max(font.metrics("linespace") + 3, 14)
            for index, line in enumerate(lines):
                ensure(line_h)
                operations.append({
                    "kind": "text", "x": MARGIN_X + indent,
                    "y": y, "text": line, "font": font_key,
                    "marker": marker if index == 0 else None,
                })
                y += line_h
            y += after

        add_text(self.content["title"], "title", after=14)
        add_text(f"Project: {self.project_id}    Document: {self.document_id}", "small", after=18)

        for section in self.content["sections"]:
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
                    # First column receives a little extra room for labels; all columns remain within A4.
                    widths = [CONTENT_W / col_count] * col_count
                    if col_count == 2:
                        widths = [CONTENT_W * 0.32, CONTENT_W * 0.68]
                    elif col_count >= 6:
                        widths = [CONTENT_W * 0.11] + [CONTENT_W * 0.89 / (col_count - 1)] * (col_count - 1)

                    def row_lines(values, font_key):
                        font = self._fonts[font_key]
                        result = []
                        for value, width in zip(values, widths):
                            result.append(self._wrap(value, font, max(24, width - 12)))
                        return result

                    all_rows = [(headers, True)] + [(row, False) for row in block["rows"]]
                    for values, is_header in all_rows:
                        key = "table_header" if is_header else "table_body"
                        wrapped = row_lines(values, key)
                        line_count = max((len(cell) for cell in wrapped), default=1)
                        row_height = max(26, line_count * (self._fonts[key].metrics("linespace") + 2) + 12)
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
                    y = self._new_page(pages)
                    operations = pages[-1]

        if len(pages) > 1 and not pages[-1]:
            pages.pop()
        return pages or [[]]

    def _build(self):
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="◀ Sebelumnya", command=self._previous).pack(side="left")
        self.page_label = ttk.Label(toolbar, text="")
        self.page_label.pack(side="left", padx=12)
        ttk.Button(toolbar, text="Berikutnya ▶", command=self._next).pack(side="left")
        ttk.Button(toolbar, text="−", width=3, command=lambda: self._set_zoom(-10)).pack(side="left", padx=(20, 2))
        ttk.Button(toolbar, text="+", width=3, command=lambda: self._set_zoom(10)).pack(side="left")
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=8)
        ttk.Label(toolbar, text=f"Status: {self.version.get('status', '-')}").pack(side="right")
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, background="#777777", highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.root.bind("<Prior>", lambda _event: self._previous())
        self.root.bind("<Next>", lambda _event: self._next())

    def _draw_page(self):
        self.canvas.delete("all")
        scale = self.zoom_percent / 100
        page_w, page_h = int(PAGE_W * scale), int(PAGE_H * scale)
        origin_x, origin_y = 30, 25
        self.canvas.configure(scrollregion=(0, 0, page_w + 80, page_h + 60))
        self.canvas.create_rectangle(
            origin_x, origin_y, origin_x + page_w, origin_y + page_h,
            fill="white", outline="#333333"
        )
        self._image_refs = []

        def sx(value):
            return origin_x + int(value * scale)

        def sy(value):
            return origin_y + int(value * scale)

        for op in self.pages[self.page_index]:
            if op["kind"] == "text":
                base_font = self._fonts[op["font"]]
                font_size = max(7, int(base_font.cget("size") * scale))
                weight = "bold" if base_font.cget("weight") == "bold" else "normal"
                slant = base_font.cget("slant")
                font = ("Arial", font_size, weight, slant)
                if op.get("marker"):
                    self.canvas.create_text(
                        sx(op["x"] - 18), sy(op["y"]), anchor="nw",
                        text=op["marker"], font=font, fill=TEXT
                    )
                self.canvas.create_text(
                    sx(op["x"]), sy(op["y"]), anchor="nw",
                    text=op["text"], font=font, fill=TEXT
                )
            elif op["kind"] == "table_row":
                x, y = sx(op["x"]), sy(op["y"])
                row_h = max(1, int(op["height"] * scale))
                cursor = x
                fill = BLUE if op["header"] else "white"
                text_fill = "white" if op["header"] else TEXT
                font = ("Arial", max(7, int((9 if op["header"] else 9) * scale)),
                        "bold" if op["header"] else "normal")
                for width, lines in zip(op["widths"], op["cells"]):
                    cell_w = max(1, int(width * scale))
                    self.canvas.create_rectangle(
                        cursor, y, cursor + cell_w, y + row_h,
                        fill=fill, outline=GRID, width=1
                    )
                    line_y = y + max(5, int(6 * scale))
                    for line in lines:
                        self.canvas.create_text(
                            cursor + max(4, int(6 * scale)), line_y,
                            anchor="nw", text=line, font=font, fill=text_fill,
                            width=max(10, cell_w - int(12 * scale))
                        )
                        line_y += max(10, int(12 * scale))
                    cursor += cell_w
            elif op["kind"] == "image":
                evidence_id = op["evidence_id"]
                record = next((item for item in self.evidence_records
                               if item.get("evidence_id") == evidence_id), None)
                if record and verify_evidence(self.project_id, evidence_id):
                    try:
                        evidence_root = (PROJECTS_DIR / self.project_id / "evidence").resolve()
                        image_path = (evidence_root / record["file_path"]).resolve()
                        image_path.relative_to(evidence_root)
                        if image_path.is_symlink() or image_path.suffix.lower() != ".png":
                            raise ValueError("Format evidence tidak didukung.")
                        photo = tk.PhotoImage(file=str(image_path))
                        max_w = max(1, int(op["width"] * scale))
                        max_h = max(1, int(op["height"] * scale))
                        factor = max(1, math.ceil(photo.width() / max_w),
                                     math.ceil(photo.height() / max_h))
                        if factor > 1:
                            photo = photo.subsample(factor, factor)
                        self._image_refs.append(photo)
                        self.canvas.create_image(sx(op["x"]), sy(op["y"]),
                                                 anchor="nw", image=photo)
                    except (OSError, ValueError, KeyError, tk.TclError):
                        self.canvas.create_text(
                            sx(op["x"]), sy(op["y"]), anchor="nw",
                            text="[Evidence tidak dapat ditampilkan]",
                            font=("Arial", max(7, int(9 * scale))), fill="#aa0000"
                        )
                else:
                    self.canvas.create_text(
                        sx(op["x"]), sy(op["y"]), anchor="nw",
                        text="[Evidence tidak valid atau tidak ditemukan]",
                        font=("Arial", max(7, int(9 * scale))), fill="#aa0000"
                    )

        footer_y = sy(PAGE_H - 42)
        self.canvas.create_text(
            origin_x + page_w // 2, footer_y, text=str(self.page_index + 1),
            font=("Arial", max(7, int(9 * scale))), fill="#555555"
        )
        self.page_label.configure(text=f"Halaman {self.page_index + 1} dari {len(self.pages)}")
        self.zoom_label.configure(text=f"{self.zoom_percent}%")
        self.canvas.yview_moveto(0)

    def _previous(self):
        if self.page_index > 0:
            self.page_index -= 1
            self._draw_page()

    def _next(self):
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            self._draw_page()

    def _set_zoom(self, delta):
        self.zoom_percent = min(150, max(60, self.zoom_percent + delta))
        self._draw_page()

    def show(self):
        self.root.mainloop()


def open_document_viewer(project_id, document_id):
    try:
        DocumentViewer(project_id, document_id).show()
    except tk.TclError as exc:
        raise RuntimeError("A4 Print Preview membutuhkan sesi desktop Windows aktif.") from exc
'@

$DocxSource = @'
"""Render approved QA content-model versions to styled, versioned DOCX files."""
from pathlib import Path

from core.document_manager import get_document
from core.document_content_model import validate_document_content
from core.evidence_manager import list_evidence, verify_evidence
from core.project_manager import PROJECTS_DIR, get_project


def _verified_image(project_id, evidence_id, records):
    record = next((item for item in records if item.get("evidence_id") == evidence_id), None)
    if record is None or not verify_evidence(project_id, evidence_id):
        raise ValueError(f"Evidence {evidence_id} tidak tersedia atau hash tidak valid.")
    project_root = (PROJECTS_DIR / project_id).resolve()
    evidence_root = (project_root / "evidence").resolve()
    path = (evidence_root / record["file_path"]).resolve()
    try:
        path.relative_to(evidence_root)
    except ValueError:
        raise ValueError("Path evidence berada di luar folder evidence proyek.") from None
    if path.is_symlink() or not path.is_file():
        raise ValueError("File evidence tidak aman atau tidak tersedia.")
    return path


def _shade_cell(cell, fill):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def _set_cell_margins(cell, top=90, start=100, bottom=90, end=100):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _style_paragraph(paragraph, before=0, after=6, line=1.15):
    paragraph.paragraph_format.space_before = before
    paragraph.paragraph_format.space_after = after
    paragraph.paragraph_format.line_spacing = line


def _style_table(table, header_fill="1F4E78"):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    table.style = "Table Grid"
    table.autofit = True
    table.allow_autofit = True
    header = table.rows[0]
    tr_pr = header._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)
    for cell in header.cells:
        _shade_cell(cell, header_fill)
        _set_cell_margins(cell)
        for paragraph in cell.paragraphs:
            _style_paragraph(paragraph, after=0, line=1.0)
            for run in paragraph.runs:
                run.bold = True
                run.font.name = "Arial"
                run.font.size = __import__("docx").shared.Pt(9)
                run.font.color.rgb = __import__("docx").shared.RGBColor(255, 255, 255)
    for row in table.rows[1:]:
        for cell in row.cells:
            _set_cell_margins(cell)
            for paragraph in cell.paragraphs:
                _style_paragraph(paragraph, after=0, line=1.0)
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = __import__("docx").shared.Pt(9)


def render_approved_docx(project_id, document_id):
    """Only APPROVED versions may be rendered; never overwrites an export."""
    try:
        from docx import Document
        from docx.shared import Mm, Inches, Pt, RGBColor
        from docx.enum.section import WD_ORIENT
    except ImportError as exc:
        raise RuntimeError("python-docx belum terpasang pada environment ini.") from exc

    record = get_document(project_id, document_id)
    manifest, version = record["manifest"], record["version"]
    if version.get("status") != "APPROVED":
        raise ValueError("DOCX final hanya dapat dibuat dari versi APPROVED.")
    content = validate_document_content(version.get("content"))
    project = get_project(project_id)
    docs_dir = (PROJECTS_DIR / project_id / "documentation" / document_id).resolve()
    docs_dir.mkdir(parents=True, exist_ok=True)
    version_no = manifest["current_version"]
    output = docs_dir / f"{document_id}_v{version_no:04d}.docx"
    if output.exists():
        raise FileExistsError(f"DOCX versi ini sudah ada: {output.name}")

    doc = Document()
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.15
    for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11)):
        style = styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(31, 78, 121)
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True

    settings = content["page_settings"]
    for section in doc.sections:
        if settings["orientation"] == "landscape":
            section.orientation = WD_ORIENT.LANDSCAPE
        else:
            section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Mm(210 if settings["orientation"] == "portrait" else 297)
        section.page_height = Mm(297 if settings["orientation"] == "portrait" else 210)
        section.top_margin = Mm(settings["margin_top_mm"])
        section.bottom_margin = Mm(settings["margin_bottom_mm"])
        section.left_margin = Mm(settings["margin_left_mm"])
        section.right_margin = Mm(settings["margin_right_mm"])
        header = section.header.paragraphs[0]
        header.text = f"{project.get('project_name', project_id)} | {content['title']}"
        _style_paragraph(header, after=3, line=1.0)
        for run in header.runs:
            run.font.name = "Arial"
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(100, 100, 100)
        footer = section.footer.paragraphs[0]
        footer.text = f"{document_id} | Versi {version_no:04d} | Halaman "
        _style_paragraph(footer, after=0, line=1.0)
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instruction = OxmlElement("w:instrText")
        instruction.set(qn("xml:space"), "preserve")
        instruction.text = " PAGE "
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        run = footer.add_run()
        run._r.append(begin)
        run._r.append(instruction)
        run._r.append(end)
        run.font.name = "Arial"
        run.font.size = Pt(8)

    title = doc.add_heading(content["title"], level=0)
    title.paragraph_format.space_after = Pt(14)
    for run in title.runs:
        run.font.name = "Arial"
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = RGBColor(31, 78, 121)
    p = doc.add_paragraph(f"Project ID: {project_id}")
    _style_paragraph(p, after=3, line=1.0)
    p = doc.add_paragraph(f"Document ID: {document_id} | Versi: {version_no:04d}")
    _style_paragraph(p, after=12, line=1.0)

    evidence_records = list_evidence(project_id)
    for section_data in content["sections"]:
        heading = doc.add_heading(section_data["title"], level=1)
        heading.paragraph_format.keep_with_next = True
        for block in section_data["blocks"]:
            kind = block["type"]
            if kind == "heading":
                doc.add_heading(block["text"], level=block["level"])
            elif kind == "paragraph":
                paragraph = doc.add_paragraph(block["text"])
                _style_paragraph(paragraph)
            elif kind in ("bullet_list", "numbered_list"):
                style = "List Bullet" if kind == "bullet_list" else "List Number"
                for item in block["items"]:
                    paragraph = doc.add_paragraph(item, style=style)
                    _style_paragraph(paragraph, after=4, line=1.1)
            elif kind == "table":
                if block.get("caption"):
                    caption = doc.add_paragraph(block["caption"])
                    _style_paragraph(caption, before=4, after=5, line=1.0)
                    for run in caption.runs:
                        run.italic = True
                        run.font.size = Pt(9)
                table = doc.add_table(rows=1, cols=len(block["headers"]))
                for cell, value in zip(table.rows[0].cells, block["headers"]):
                    cell.text = value
                for row in block["rows"]:
                    cells = table.add_row().cells
                    for cell, value in zip(cells, row):
                        cell.text = value
                _style_table(table)
                spacer = doc.add_paragraph()
                _style_paragraph(spacer, after=4, line=1.0)
            elif kind == "image":
                path = _verified_image(project_id, block["evidence_id"], evidence_records)
                paragraph = doc.add_paragraph()
                paragraph.alignment = 1
                paragraph.add_run().add_picture(str(path), width=Inches(5.8))
                _style_paragraph(paragraph, after=3)
                if block.get("caption"):
                    caption = doc.add_paragraph(block["caption"])
                    caption.alignment = 1
                    _style_paragraph(caption, after=8, line=1.0)
                    for run in caption.runs:
                        run.italic = True
                        run.font.size = Pt(9)
            elif kind == "page_break":
                doc.add_page_break()

    temporary = output.with_suffix(".docx.tmp")
    try:
        doc.save(temporary)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output
'@

Set-Content -Path $ViewerPath -Value $ViewerSource -Encoding UTF8
Set-Content -Path $DocxPath -Value $DocxSource -Encoding UTF8

Write-Host "`n========== VERIFIKASI SINTAKS ==========" -ForegroundColor Cyan
& $Python -m py_compile ".\core\document_viewer.py" ".\core\docx_renderer.py"
if ($LASTEXITCODE -ne 0) { throw "Kompilasi gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
& $Python -m unittest tests.test_document_content_model tests.test_documentation_generator -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Backup tersedia di: $Backup" }

Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup tersedia di: $Backup" }

Write-Host "`nBATCH SELESAI: renderer diperbarui; sintaks, focused tests, dan diff check lulus." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host "Catatan: Draft dokumen dan Document Content Model tidak diubah."
