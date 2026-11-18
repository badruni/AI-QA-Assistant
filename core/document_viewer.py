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
            current = fragment
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
        add_text(self.project_id, "title", after=8, align="center")
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
                            "line_height": line_height,
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
        toc_font = self._fonts["body"]
        dot_width = max(1, toc_font.measure("."))
        for index, (title, page_number) in enumerate(section_start_pages):
            if index + 1 < len(toc_lines):
                page_label = str(page_number)
                occupied = toc_font.measure(title) + toc_font.measure(page_label) + toc_font.measure("  ")
                dot_count = max(3, int((CONTENT_W - occupied) / dot_width))
                toc_lines[index + 1]["text"] = f"{title}  {'.' * dot_count}  {page_label}"
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
                font_size = max(5, int(round(base_font.cget("size") * scale)))
                weight = "bold" if base_font.cget("weight") == "bold" else "normal"
                slant = base_font.cget("slant")
                font = ("Arial", font_size, weight, slant)
                if op.get("marker"):
                    self.canvas.create_text(
                        sx(op["x"] - 18), sy(op["y"]), anchor="nw",
                        text=op["marker"], font=font, fill=TEXT
                    )
                if op.get("align") == "center":
                    self.canvas.create_text(
                        sx(PAGE_W / 2), sy(op["y"]), anchor="n",
                        text=op["text"], font=font, fill=TEXT,
                        width=max(100, int(CONTENT_W * scale)), justify="center"
                    )
                else:
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
                font = ("Arial", max(5, int(round(9 * scale))),
                        "bold" if op["header"] else "normal")
                for width, lines in zip(op["widths"], op["cells"]):
                    cell_w = max(1, int(width * scale))
                    self.canvas.create_rectangle(
                        cursor, y, cursor + cell_w, y + row_h,
                        fill=fill, outline=GRID, width=1
                    )
                    horizontal_pad = max(2, int(round(6 * scale)))
                    vertical_pad = max(2, int(round(6 * scale)))
                    line_step = max(1, int(round(op.get("line_height", 15) * scale)))
                    for line_index, line in enumerate(lines):
                        line_y = y + vertical_pad + (line_index * line_step)
                        self.canvas.create_text(
                            cursor + horizontal_pad, line_y,
                            anchor="nw", text=line, font=font, fill=text_fill,
                            width=max(5, cell_w - (2 * horizontal_pad))
                        )
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
