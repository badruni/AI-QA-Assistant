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
    title.alignment = 1
    title.paragraph_format.space_before = Pt(100)
    title.paragraph_format.space_after = Pt(18)
    for run in title.runs:
        run.font.name = "Arial"
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = RGBColor(31, 78, 121)
    p = doc.add_paragraph(project.get("project_name", project_id))
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
    field.set(qn("w:instr"), 'TOC \\o "1-3" \\h \\z \\u')
    toc._p.append(field)
    _style_paragraph(toc, after=8, line=1.0)
    doc.add_page_break()

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
