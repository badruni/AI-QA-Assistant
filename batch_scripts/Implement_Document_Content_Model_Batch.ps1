#requires -Version 5.1
<#
AI QA Assistant - Document Content Model implementation batch
Run from repository root:
  .\batch_scripts\Implement_Document_Content_Model_Batch.ps1

Creates a render-agnostic document structure for UAT and user guides.
No new third-party dependencies are introduced.
#>

$ErrorActionPreference = "Stop"

$RequiredPaths = @(
    ".\core",
    ".\tests",
    ".\docs\PROJECT_SETUP_GUIDE.md",
    ".\core\document_manager.py",
    ".\core\evidence_manager.py"
)
foreach ($Path in $RequiredPaths) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Path wajib tidak ditemukan: $Path. Jalankan dari root repository."
    }
}

$Python = ".\.venv-scanner\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = ".\backups\before_document_content_model_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$Targets = @(
    ".\core\document_content_model.py",
    ".\tests\test_document_content_model.py",
    ".\docs\PROJECT_SETUP_GUIDE.md"
)
foreach ($Target in $Targets) {
    if (Test-Path -LiteralPath $Target) {
        $Relative = $Target.TrimStart(".\")
        $BackupTarget = Join-Path $BackupDir $Relative
        New-Item -ItemType Directory -Path (Split-Path $BackupTarget -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $Target -Destination $BackupTarget -Force
    }
}

$Module = @'
"""Validated, renderer-independent content model for QA documents.

The model stores semantic blocks only. It does not render HTML or DOCX and
never treats unverified test observations as passing results.
"""

from copy import deepcopy
import re
from uuid import uuid4


SCHEMA_VERSION = 1
DOCUMENT_TYPES = ("UAT", "User_Guide_Web", "User_Guide_CMS")
PAGE_SIZES = ("A4",)
PAGE_ORIENTATIONS = ("portrait", "landscape")
BLOCK_TYPES = (
    "heading",
    "paragraph",
    "bullet_list",
    "numbered_list",
    "table",
    "image",
    "page_break",
)

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_ALLOWED_STATUSES = (
    "Passed",
    "Failed",
    "Blocked",
    "Access Restricted",
    "Inconclusive",
    "Timeout",
    "Needs Review",
    "Not Tested",
    "Not Applicable",
)


def _require_text(value, field, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(f"{field} harus berupa teks.")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} tidak boleh kosong.")
    return value


def _validate_plain_mapping(value, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field} harus berupa object/dictionary.")
    return deepcopy(value)


def _validate_page_settings(settings):
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError("page_settings harus berupa object/dictionary.")
    allowed = {"size", "orientation", "margin_top_mm", "margin_bottom_mm",
               "margin_left_mm", "margin_right_mm"}
    unknown = set(settings) - allowed
    if unknown:
        raise ValueError(
            "Pengaturan halaman tidak dikenal: " + ", ".join(sorted(unknown))
        )
    result = {
        "size": settings.get("size", "A4"),
        "orientation": settings.get("orientation", "portrait"),
        "margin_top_mm": settings.get("margin_top_mm", 20),
        "margin_bottom_mm": settings.get("margin_bottom_mm", 20),
        "margin_left_mm": settings.get("margin_left_mm", 20),
        "margin_right_mm": settings.get("margin_right_mm", 20),
    }
    if result["size"] not in PAGE_SIZES:
        raise ValueError("Ukuran halaman yang didukung saat ini hanya A4.")
    if result["orientation"] not in PAGE_ORIENTATIONS:
        raise ValueError("Orientasi halaman harus portrait atau landscape.")
    for key in ("margin_top_mm", "margin_bottom_mm",
                "margin_left_mm", "margin_right_mm"):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} harus berupa angka.")
        if not 5 <= value <= 50:
            raise ValueError(f"{key} harus berada pada rentang 5 sampai 50 mm.")
    return result


def _validate_block(block, location):
    if not isinstance(block, dict):
        raise ValueError(f"{location} harus berupa object/dictionary.")
    block_type = block.get("type")
    if block_type not in BLOCK_TYPES:
        raise ValueError(f"Tipe block tidak didukung pada {location}.")

    if block_type == "heading":
        unknown = set(block) - {"type", "level", "text"}
        if unknown:
            raise ValueError(f"Properti heading tidak dikenal pada {location}.")
        level = block.get("level", 2)
        if isinstance(level, bool) or level not in (1, 2, 3):
            raise ValueError("Level heading harus 1, 2, atau 3.")
        return {"type": "heading", "level": level,
                "text": _require_text(block.get("text"), f"{location}.text")}

    if block_type == "paragraph":
        unknown = set(block) - {"type", "text"}
        if unknown:
            raise ValueError(f"Properti paragraph tidak dikenal pada {location}.")
        return {"type": "paragraph",
                "text": _require_text(block.get("text"), f"{location}.text", True)}

    if block_type in ("bullet_list", "numbered_list"):
        unknown = set(block) - {"type", "items"}
        if unknown:
            raise ValueError(f"Properti list tidak dikenal pada {location}.")
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{location}.items harus berupa list yang tidak kosong.")
        return {
            "type": block_type,
            "items": [
                _require_text(item, f"{location}.items[{index}]")
                for index, item in enumerate(items)
            ],
        }

    if block_type == "table":
        unknown = set(block) - {"type", "headers", "rows", "caption"}
        if unknown:
            raise ValueError(f"Properti table tidak dikenal pada {location}.")
        headers = block.get("headers")
        rows = block.get("rows")
        if not isinstance(headers, list) or not headers:
            raise ValueError("Table harus memiliki headers.")
        headers = [
            _require_text(item, f"{location}.headers[{index}]")
            for index, item in enumerate(headers)
        ]
        if not isinstance(rows, list):
            raise ValueError("Table rows harus berupa list.")
        normalized_rows = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != len(headers):
                raise ValueError(
                    f"Jumlah kolom pada baris {row_index + 1} tidak sesuai headers."
                )
            normalized_rows.append([
                _require_text(cell, f"{location}.rows[{row_index}]", True)
                for cell in row
            ])
        caption = block.get("caption", "")
        _require_text(caption, f"{location}.caption", True)
        return {
            "type": "table",
            "headers": headers,
            "rows": normalized_rows,
            "caption": caption,
        }

    if block_type == "image":
        unknown = set(block) - {"type", "evidence_id", "caption", "alt"}
        if unknown:
            raise ValueError(f"Properti image tidak dikenal pada {location}.")
        evidence_id = _require_text(
            block.get("evidence_id"), f"{location}.evidence_id"
        )
        if not _ID_PATTERN.fullmatch(evidence_id):
            raise ValueError("evidence_id hanya boleh berisi huruf, angka, _ dan -.")
        caption = block.get("caption", "")
        alt = block.get("alt", "")
        _require_text(caption, f"{location}.caption", True)
        _require_text(alt, f"{location}.alt", True)
        return {
            "type": "image",
            "evidence_id": evidence_id,
            "caption": caption,
            "alt": alt,
        }

    unknown = set(block) - {"type"}
    if unknown:
        raise ValueError(f"Properti page_break tidak dikenal pada {location}.")
    return {"type": "page_break"}


def validate_document_content(content):
    """Validate and return a normalized deep copy of a content model."""
    if not isinstance(content, dict):
        raise ValueError("Content model harus berupa object/dictionary.")
    allowed = {
        "schema_version", "document_type", "title", "metadata",
        "page_settings", "sections",
    }
    unknown = set(content) - allowed
    if unknown:
        raise ValueError("Properti content model tidak dikenal: " +
                         ", ".join(sorted(unknown)))
    if content.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version content model tidak didukung.")
    document_type = content.get("document_type")
    if document_type not in DOCUMENT_TYPES:
        raise ValueError("Jenis dokumen tidak didukung.")
    title = _require_text(content.get("title"), "title")
    metadata = _validate_plain_mapping(content.get("metadata", {}), "metadata")
    page_settings = _validate_page_settings(content.get("page_settings"))
    sections = content.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("Content model harus memiliki minimal satu section.")

    normalized_sections = []
    seen_ids = set()
    for index, section in enumerate(sections):
        location = f"sections[{index}]"
        if not isinstance(section, dict):
            raise ValueError(f"{location} harus berupa object/dictionary.")
        unknown_section = set(section) - {"id", "title", "blocks"}
        if unknown_section:
            raise ValueError(f"Properti section tidak dikenal pada {location}.")
        section_id = section.get("id") or f"section-{index + 1}"
        if not isinstance(section_id, str) or not _ID_PATTERN.fullmatch(section_id):
            raise ValueError(f"ID section tidak valid pada {location}.")
        if section_id in seen_ids:
            raise ValueError(f"ID section duplikat: {section_id}")
        seen_ids.add(section_id)
        section_title = _require_text(section.get("title"), f"{location}.title")
        blocks = section.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            raise ValueError(f"{location}.blocks harus berupa list yang tidak kosong.")
        normalized_sections.append({
            "id": section_id,
            "title": section_title,
            "blocks": [
                _validate_block(block, f"{location}.blocks[{block_index}]")
                for block_index, block in enumerate(blocks)
            ],
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "document_type": document_type,
        "title": title,
        "metadata": metadata,
        "page_settings": page_settings,
        "sections": normalized_sections,
    }


def create_document_content(
    document_type,
    title,
    sections,
    metadata=None,
    page_settings=None,
):
    """Create and validate a standard document content model."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "document_type": document_type,
        "title": title,
        "metadata": metadata or {},
        "page_settings": page_settings or {},
        "sections": sections,
    }
    return validate_document_content(payload)


def make_section(title, blocks, section_id=None):
    """Convenience constructor for a semantic document section."""
    return {
        "id": section_id or f"section-{uuid4().hex[:12]}",
        "title": title,
        "blocks": blocks,
    }


def make_test_case_block(
    case_id,
    scenario,
    expected_result,
    actual_result,
    status,
    evidence_ids=None,
):
    """Build a UAT test-case table row without inferring its status."""
    _require_text(case_id, "case_id")
    _require_text(scenario, "scenario")
    _require_text(expected_result, "expected_result")
    _require_text(actual_result, "actual_result", True)
    if status not in _ALLOWED_STATUSES:
        raise ValueError("Status test case tidak dikenal.")
    if evidence_ids is None:
        evidence_ids = []
    if not isinstance(evidence_ids, list):
        raise ValueError("evidence_ids harus berupa list.")
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not _ID_PATTERN.fullmatch(evidence_id):
            raise ValueError("Evidence ID tidak valid.")
    return {
        "case_id": case_id,
        "scenario": scenario,
        "expected_result": expected_result,
        "actual_result": actual_result,
        "status": status,
        "evidence_ids": list(evidence_ids),
    }
'@

$Tests = @'
import copy
import unittest

from core import document_content_model as model


class DocumentContentModelTests(unittest.TestCase):
    def valid_sections(self):
        return [{
            "id": "overview",
            "title": "Ringkasan",
            "blocks": [
                {"type": "heading", "level": 2, "text": "Tujuan"},
                {"type": "paragraph", "text": "Pemeriksaan berdasarkan evidence."},
                {"type": "bullet_list", "items": ["Langkah satu", "Langkah dua"]},
                {"type": "table", "headers": ["Kolom A", "Kolom B"],
                 "rows": [["A1", "B1"]], "caption": "Ringkasan"},
                {"type": "image", "evidence_id": "EV-001",
                 "caption": "Homepage", "alt": "Screenshot homepage"},
                {"type": "page_break"},
            ],
        }]

    def create(self, **kwargs):
        args = {
            "document_type": "UAT",
            "title": "UAT Demo",
            "sections": self.valid_sections(),
        }
        args.update(kwargs)
        return model.create_document_content(**args)

    def test_creates_normalized_a4_content_model(self):
        result = self.create()
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["page_settings"]["size"], "A4")
        self.assertEqual(result["page_settings"]["orientation"], "portrait")
        self.assertEqual(len(result["sections"]), 1)

    def test_does_not_mutate_input(self):
        sections = self.valid_sections()
        original = copy.deepcopy(sections)
        model.create_document_content("UAT", "Demo", sections)
        self.assertEqual(sections, original)

    def test_supports_all_document_types(self):
        for document_type in model.DOCUMENT_TYPES:
            with self.subTest(document_type=document_type):
                self.create(document_type=document_type)

    def test_rejects_unknown_document_type(self):
        with self.assertRaises(ValueError):
            self.create(document_type="Other")

    def test_rejects_empty_sections(self):
        with self.assertRaises(ValueError):
            self.create(sections=[])

    def test_rejects_duplicate_section_ids(self):
        sections = self.valid_sections()
        sections.append(copy.deepcopy(sections[0]))
        with self.assertRaises(ValueError):
            self.create(sections=sections)

    def test_rejects_unknown_block_type(self):
        with self.assertRaises(ValueError):
            self.create(sections=[{"title": "X", "blocks": [{"type": "html"}]}])

    def test_rejects_malformed_table_rows(self):
        with self.assertRaises(ValueError):
            self.create(sections=[{
                "title": "X",
                "blocks": [{"type": "table", "headers": ["A", "B"],
                            "rows": [["only one"]]}],
            }])

    def test_rejects_invalid_page_margins(self):
        with self.assertRaises(ValueError):
            self.create(page_settings={"margin_left_mm": 2})

    def test_rejects_unknown_page_settings(self):
        with self.assertRaises(ValueError):
            self.create(page_settings={"paper": "Letter"})

    def test_image_uses_evidence_reference_not_path(self):
        result = self.create()
        image = result["sections"][0]["blocks"][4]
        self.assertEqual(image["evidence_id"], "EV-001")
        with self.assertRaises(ValueError):
            self.create(sections=[{
                "title": "Images",
                "blocks": [{"type": "image", "evidence_id": "../outside.png"}],
            }])

    def test_rejects_arbitrary_local_path_property(self):
        with self.assertRaises(ValueError):
            self.create(sections=[{
                "title": "Images",
                "blocks": [{"type": "image", "evidence_id": "EV-1",
                            "path": "C:/private/file.png"}],
            }])

    def test_test_case_status_is_not_inferred(self):
        case = model.make_test_case_block(
            "TC-001", "Login", "User masuk", "Belum dicoba",
            "Needs Review", ["EV-001"],
        )
        self.assertEqual(case["status"], "Needs Review")
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-002", "Login", "User masuk", "Tombol ditemukan",
                "Passed",
            )

    def test_section_helper_creates_id(self):
        section = model.make_section(
            "Pendahuluan", [{"type": "paragraph", "text": "Isi"}]
        )
        self.assertTrue(section["id"].startswith("section-"))

    def test_rejects_unknown_content_properties(self):
        payload = {
            "schema_version": 1,
            "document_type": "UAT",
            "title": "Demo",
            "sections": self.valid_sections(),
            "raw_html": "<script>",
        }
        with self.assertRaises(ValueError):
            model.validate_document_content(payload)


if __name__ == "__main__":
    unittest.main()
'@

$DocPath = ".\docs\PROJECT_SETUP_GUIDE.md"
$DocText = [System.IO.File]::ReadAllText((Resolve-Path $DocPath), [System.Text.Encoding]::UTF8)
$DocSection = @'

## Document Content Model

`core/document_content_model.py` menyediakan struktur konten dokumen yang
independen dari renderer. Model ini digunakan sebagai sumber data semantik
untuk Print Preview Viewer dan DOCX Renderer pada tahap berikutnya.

Jenis dokumen yang didukung: `UAT`, `User_Guide_Web`, dan `User_Guide_CMS`.
Setiap dokumen menggunakan section dan block terstruktur: heading, paragraph,
bullet/numbered list, table, image reference, dan page break. Pengaturan halaman
awal menggunakan A4 dengan orientasi portrait atau landscape dan margin dalam
milimeter.

Block gambar hanya menyimpan `evidence_id`, bukan path file bebas. Renderer
berikutnya harus menyelesaikan referensi tersebut melalui Evidence Manager dan
memverifikasi integritas evidence sebelum menampilkan atau menyisipkannya.
Model tidak membuat kesimpulan PASS/FAIL; status test case harus diberikan
berdasarkan hasil inspeksi dan evidence yang tersedia.
'@

if ($DocText -notmatch '(?m)^## Document Content Model\s*$') {
    $DocText = $DocText.TrimEnd("`r", "`n") + "`r`n`r`n" + $DocSection.Trim() + "`r`n"
}

Set-Content -LiteralPath ".\core\document_content_model.py" -Value $Module -Encoding UTF8
Set-Content -LiteralPath ".\tests\test_document_content_model.py" -Value $Tests -Encoding UTF8
[System.IO.File]::WriteAllText(
    (Resolve-Path $DocPath),
    $DocText,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "`n========== IMPLEMENTATION WRITTEN ==========" -ForegroundColor Cyan
Write-Host "Backup: $BackupDir"
Write-Host "core\document_content_model.py"
Write-Host "tests\test_document_content_model.py"
Write-Host "docs\PROJECT_SETUP_GUIDE.md"

Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
& $Python -m unittest tests.test_document_content_model -v
if ($LASTEXITCODE -ne 0) {
    throw "Focused tests gagal. Backup: $BackupDir"
}

Write-Host "`n========== SYNTAX CHECK ==========" -ForegroundColor Cyan
& $Python -m py_compile .\core\document_content_model.py .\tests\test_document_content_model.py
if ($LASTEXITCODE -ne 0) {
    throw "Syntax check gagal. Backup: $BackupDir"
}

Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check menemukan masalah. Backup: $BackupDir"
}

Write-Host "`n========== BATCH COMPLETED ==========" -ForegroundColor Green
Write-Host "Focused tests, syntax check, dan diff check berhasil."
Write-Host "Backup: $BackupDir"
