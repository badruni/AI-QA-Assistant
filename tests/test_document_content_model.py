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

    def test_test_case_status_is_not_inferred_and_pass_fail_require_evidence(self):
        case = model.make_test_case_block(
            "TC-001", "Login", "User masuk", "Belum dicoba",
            "Needs Review",
        )
        self.assertEqual(case["status"], "Needs Review")
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-002", "Login", "User masuk", "Tombol ditemukan",
                "Passed",
            )
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-003", "Login", "User masuk", "Login gagal",
                "Failed",
            )

    def test_passed_and_failed_status_accept_evidence_reference(self):
        passed = model.make_test_case_block(
            "TC-004", "Login", "User masuk", "Login berhasil diamati",
            "Passed", ["EV-001"],
        )
        failed = model.make_test_case_block(
            "TC-005", "Login", "User masuk", "Pesan error diamati",
            "Failed", ["EV-002"],
        )
        self.assertEqual(passed["status"], "Passed")
        self.assertEqual(failed["status"], "Failed")

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
