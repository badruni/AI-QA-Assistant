"""Generate conservative QA document drafts from observed project reports."""
from datetime import datetime, timezone
import json

from core.project_manager import PROJECTS_DIR, get_project, validate_project_id
from core.document_manager import create_document, list_documents
from core.document_content_model import create_document_content, make_section
from core.evidence_manager import list_evidence, verify_evidence


def _reports(project_id):
    validate_project_id(project_id)
    get_project(project_id)
    root = (PROJECTS_DIR / project_id / "reports").resolve()
    project_root = (PROJECTS_DIR / project_id).resolve()
    try:
        root.relative_to(project_root)
    except ValueError:
        raise ValueError("Folder laporan berada di luar proyek.") from None
    if not root.exists():
        return []
    if root.is_symlink():
        raise ValueError("Folder laporan tidak boleh berupa symbolic link.")
    records = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("project_id") == project_id:
            records.append((path.name, payload))
    return records


def _evidence_for_page(project_id, page_url, evidence_records):
    for item in evidence_records:
        if item.get("evidence_type") != "screenshot":
            continue
        evidence_id = item.get("evidence_id")
        if item.get("page_url") == page_url and evidence_id and verify_evidence(project_id, evidence_id):
            return evidence_id
    return None


def _report_result(records, inspection_type):
    for name, payload in records:
        if payload.get("inspection_type") == inspection_type:
            return name, payload.get("result") or {}
    return None, None


def _text(value, fallback="Belum tersedia"):
    if value is None or value == "":
        return fallback
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _page_rows(pages):
    rows = []
    for page in pages:
        rows.append([
            _text(page.get("page_url"), "-"),
            _text(page.get("http_status")),
            f"Needs Review (status inspeksi sumber: {_text(page.get('status'), 'Tidak tersedia')})",
            _text(page.get("component_summary"), "{}"),
        ])
    return rows or [["Belum ada halaman pada laporan", "-", "Needs Review", "{}"]]


def _make_uat_sections(project, result, evidence_records):
    pages = result.get("pages") or []
    findings = result.get("findings") or []
    project_name = project.get("project_name", "Belum tersedia")
    base_url = project.get("website_url") or project.get("web_url") or (
        pages[0].get("page_url") if pages else "Belum tersedia"
    )
    sections = [
        make_section("1. Informasi Dokumen", [
            {"type": "table", "headers": ["Informasi", "Detail"], "rows": [
                ["Proyek", _text(project_name)],
                ["Aplikasi yang Diuji", "Website dan fitur yang termasuk dalam lingkup UAT (perlu konfirmasi)"],
                ["Alamat Website", _text(base_url)],
                ["Versi Dokumen", "Draft 1"],
                ["Tanggal Pembaruan", datetime.now(timezone.utc).date().isoformat()],
                ["Aktor Pengujian", "Pengunjung tanpa login; status member belum diverifikasi"],
                ["Lingkungan dan Versi Aplikasi", "Diisi sebelum pengujian"],
                ["Nama Penguji dan Periode UAT", "Diisi sebelum pengujian"],
            ]},
        ], "uat-document-info"),
        make_section("2. Pendahuluan", [
            {"type": "paragraph", "text": "Dokumen ini merupakan draft acuan User Acceptance Testing. Sumber awal berupa laporan observasi Generic UAT; laporan tersebut tidak dengan sendirinya membuktikan fungsi bisnis berjalan sesuai harapan."},
            {"type": "heading", "text": "2.1 Tujuan Pengujian"},
            {"type": "paragraph", "text": "Menyiapkan pencatatan pengujian penerimaan terhadap fungsi website yang telah disepakati. Tujuan dan skenario final perlu dikonfirmasi oleh pemilik produk dan penguji."},
            {"type": "heading", "text": "2.2 Kriteria Penerimaan"},
            {"type": "paragraph", "text": "Kriteria penerimaan belum tersedia pada sumber inspeksi. Kriteria harus disepakati sebelum UAT; status Tidak sesuai, Belum bisa dicoba, Belum diuji, atau Tidak berlaku perlu ditinjau bersama pihak terkait."},
            {"type": "heading", "text": "2.3 Lingkup Pengujian"},
            {"type": "paragraph", "text": "Lingkup sementara dibatasi pada halaman yang tercatat dalam laporan Generic UAT. Modul, cakupan fungsional, dan pemisahan skenario Guest/Member belum ditetapkan oleh laporan tersebut."},
            {"type": "table", "headers": ["Halaman terobservasi", "HTTP", "Status inspeksi", "Komponen terdeteksi"], "rows": _page_rows(pages)},
            {"type": "heading", "text": "2.4 Ketentuan Pelaksanaan"},
            {"type": "bullet_list", "items": [
                "Lengkapi identitas penguji, lingkungan, versi aplikasi, akun uji, dan periode pelaksanaan sebelum UAT.",
                "Isi langkah pengujian, data uji, dan hasil yang diharapkan berdasarkan kebutuhan yang disetujui.",
                "Kolom status diisi setelah tindakan benar-benar diuji dan hasilnya diamati.",
                "Jangan melakukan submit form, transaksi, atau perubahan data tanpa otorisasi eksplisit.",
                "Catat kendala dan evidence menggunakan ID test case yang dapat ditelusuri.",
            ]},
        ], "uat-introduction"),
        make_section("3. Skenario Pengujian", [
            {"type": "paragraph", "text": "Daftar di bawah merupakan kerangka pengisian. Laporan inspeksi DOM tidak menyediakan skenario fungsional, langkah uji, data uji, atau expected result."},
            {"type": "table", "headers": ["Kode", "Modul", "Jumlah", "Cakupan Fungsional"], "rows": [
                ["TBD", "Modul dari hasil analisis kebutuhan", "Belum ditentukan", "Perlu disepakati"],
                ["GST", "Pengunjung (Guest)", "Belum ditentukan", "Belum disusun"],
                ["MBR", "Member", "Belum ditentukan", "Keberadaan/alur member perlu diverifikasi"],
            ]},
            {"type": "table", "caption": "Template test case — belum merupakan hasil pengujian", "headers": [
                "ID Test Case", "Modul / Fitur", "Skenario Pengujian", "Langkah Pengujian",
                "Data Uji", "Hasil yang Diharapkan", "Status"
            ], "rows": [
                ["TBD-001", "Belum ditentukan", "Belum disusun", "Belum disusun", "Belum ditentukan", "Harus ditetapkan sebelum pengujian", "Belum diuji"]
            ]},
        ], "uat-test-scenarios"),
        make_section("4. Catatan Pengujian", [
            {"type": "paragraph", "text": "Isi bagian ini setelah pelaksanaan UAT. Gunakan ID Test Case dari tabel skenario agar kendala dan evidence dapat ditelusuri."},
            {"type": "table", "headers": ["ID Test Case", "Yang Terjadi", "Catatan atau Kendala", "Foto atau Tautan"], "rows": [
                ["Belum ada catatan", "Belum diuji", "Diisi saat UAT", "Evidence ditambahkan setelah diverifikasi"]
            ]},
        ], "uat-test-notes"),
        make_section("5. Persetujuan Hasil Pengujian", [
            {"type": "paragraph", "text": "Bagian persetujuan diisi setelah seluruh skenario yang disepakati ditinjau. Draft ini belum menyatakan aplikasi diterima."},
            {"type": "table", "headers": ["Rekap Status", "Jumlah"], "rows": [
                ["Sesuai", "Belum dihitung"],
                ["Tidak sesuai", "Belum dihitung"],
                ["Belum bisa dicoba", "Belum dihitung"],
                ["Belum diuji", "1 template; jumlah final mengikuti test case"],
                ["Tidak berlaku", "Belum ditentukan"],
            ]},
            {"type": "paragraph", "text": "Hasil akhir: Belum diputuskan (Diterima / Diterima bersyarat / Belum diterima)."},
            {"type": "paragraph", "text": "Catatan atau syarat yang perlu diselesaikan: diisi saat review."},
            {"type": "table", "headers": ["Peran", "Nama", "Tanggal", "Paraf atau Tanda Tangan"], "rows": [
                ["Penguji", "Diisi", "Diisi", "Diisi"],
                ["Pendamping dari tim", "Diisi", "Diisi", "Diisi"],
                ["Wakil pengguna", "Diisi", "Diisi", "Diisi"],
            ]},
        ], "uat-approval"),
    ]
    for page in pages:
        url = page.get("page_url")
        evidence_id = _evidence_for_page(project.get("project_id"), url, evidence_records) if url else None
        if evidence_id:
            sections.append(make_section("Evidence observasi", [
                {"type": "image", "evidence_id": evidence_id, "caption": f"Screenshot observasi: {url}", "alt": "Screenshot halaman yang diamati"}
            ]))
    return sections, [
        "Tujuan, kriteria penerimaan, dan ruang lingkup final perlu disetujui.",
        "Skenario Guest/Member, langkah, data uji, dan expected result belum tersedia dari laporan Generic UAT.",
        "Actual result dan status setiap test case harus diisi setelah pengujian nyata.",
        "Status halaman pada laporan Generic UAT adalah status inspeksi, bukan bukti keberhasilan fungsi bisnis.",
    ]


def _make_web_guide_sections(project, result, evidence_records):
    pages = result.get("pages") or []
    sections = [
        make_section("Ruang Lingkup", [
            {"type": "paragraph", "text": "Panduan ini merupakan kerangka User Guide Website berdasarkan halaman yang tercatat dalam laporan observasi. Deskripsi fungsi dan langkah operasional hanya dapat ditambahkan setelah diamati dan diverifikasi."},
            {"type": "paragraph", "text": "Bagian pengunjung dan member dipisahkan hanya apabila alur member telah dikonfirmasi. Keberadaan autentikasi pada website tidak otomatis membuktikan seluruh fitur member."},
        ], "web-guide-scope"),
        make_section("1. Informasi Website", [
            {"type": "table", "headers": ["Informasi", "Detail"], "rows": [
                ["Proyek", _text(project.get("project_name"))],
                ["Alamat Website", _text(project.get("website_url") or project.get("web_url") or (pages[0].get("page_url") if pages else None))],
                ["Sumber observasi", "Generic UAT Inspection"],
            ]},
        ], "web-guide-info"),
        make_section("2. Halaman Pengunjung", [
            {"type": "paragraph", "text": "Daftar berikut hanya menunjukkan halaman yang diamati. Tujuan halaman, navigasi, isi, dan instruksi penggunaan belum disimpulkan dari keberadaan elemen DOM."},
            {"type": "table", "headers": ["URL Halaman", "HTTP", "Status Inspeksi", "Komponen Teramati"], "rows": _page_rows(pages)},
            {"type": "paragraph", "text": "Cara penggunaan tiap halaman: menunggu eksplorasi manual dan verifikasi reviewer."},
        ], "web-guide-guest"),
        make_section("3. Area Member", [
            {"type": "paragraph", "text": "Bagian ini disediakan apabila website memiliki area member yang telah diverifikasi. Saat ini langkah login, registrasi, profil, dan fitur setelah login belum dapat disusun dari laporan Generic UAT saja."},
            {"type": "table", "headers": ["Area/Fitur", "Status Informasi"], "rows": [
                ["Login/registrasi", "Perlu verifikasi"],
                ["Fitur setelah login", "Belum diamati"],
                ["Langkah penggunaan", "Belum diverifikasi"],
            ]},
        ], "web-guide-member"),
        make_section("4. Catatan dan Evidence", [
            {"type": "paragraph", "text": "Screenshot hanya disertakan apabila terdaftar pada Evidence Manager dan lolos verifikasi integritas."},
        ], "web-guide-evidence"),
    ]
    for page in pages:
        url = page.get("page_url")
        evidence_id = _evidence_for_page(project.get("project_id"), url, evidence_records) if url else None
        if evidence_id:
            sections.append(make_section("Screenshot halaman website", [
                {"type": "image", "evidence_id": evidence_id, "caption": str(url), "alt": "Screenshot halaman website"}
            ]))
    return sections, [
        "Tujuan halaman dan navigasi perlu dikonfirmasi melalui eksplorasi manual.",
        "Instruksi fitur dan langkah penggunaan belum diverifikasi.",
        "Bagian member harus diperbarui hanya setelah alur member diamati.",
    ]


def _make_cms_guide_sections(project, records):
    cms_reports = [(name, payload.get("result") or {}) for name, payload in records
                   if payload.get("inspection_type") == "cms_exploration"]
    cms_url = project.get("cms_url")
    rows = [
        ["CMS URL", _text(cms_url)],
        ["Laporan eksplorasi CMS", ", ".join(name for name, _ in cms_reports) if cms_reports else "Belum tersedia"],
        ["Login dan dashboard", "Belum diverifikasi"],
        ["Menu dan submenu", "Belum diamati"],
        ["Field dan tombol", "Belum diamati"],
        ["Prosedur tambah/edit/hapus", "Belum diverifikasi; tidak ada operasi data yang dijalankan"],
    ]
    sections = [
        make_section("Ruang Lingkup", [
            {"type": "paragraph", "text": "Panduan ini mengikuti struktur User Guide CMS: akses login, dashboard, navigasi menu, penjelasan field/tombol, dan langkah penggunaan fitur. Nama menu dan instruksi harus mengikuti tampilan CMS yang benar-benar diamati."},
            {"type": "paragraph", "text": "Data, angka, dan status pada screenshot harus berasal dari evidence aktual. Jangan gunakan contoh sebagai fakta konfigurasi klien."},
        ], "cms-guide-scope"),
        make_section("VERSION HISTORY", [
            {"type": "table", "headers": ["Version", "Date", "Author", "Change Log"], "rows": [
                ["Draft 1", datetime.now(timezone.utc).date().isoformat(), "Belum ditentukan", "Inisiasi kerangka; menunggu eksplorasi CMS"]
            ]},
        ], "cms-guide-version"),
        make_section("1. Login", [
            {"type": "paragraph", "text": "Langkah login belum dapat ditulis karena halaman login CMS dan prosedurnya belum diverifikasi. Jangan memasukkan kredensial ke dokumen atau log."},
        ], "cms-guide-login"),
        make_section("2. Dashboard", [
            {"type": "paragraph", "text": "Deskripsi dashboard, ringkasan, navigasi, dan kontrol akun menunggu observasi CMS."},
        ], "cms-guide-dashboard"),
        make_section("3. Menu dan Pengelolaan Konten", [
            {"type": "paragraph", "text": "Nama menu/submenu, fungsi halaman, field, tombol, serta prosedur tambah/edit/hapus akan ditambahkan berdasarkan eksplorasi read-only dan verifikasi yang diizinkan."},
            {"type": "table", "headers": ["Item", "Kondisi Sumber"], "rows": rows},
        ], "cms-guide-management"),
    ]
    unverified = [
        "Login dan dashboard CMS belum diverifikasi.",
        "Menu, submenu, field, tombol, dan hak akses belum diamati.",
        "Prosedur tambah/edit/hapus belum diverifikasi; tidak ada operasi data yang dijalankan.",
    ]
    return sections, unverified, bool(cms_reports), [name for name, _ in cms_reports]


def generate_document_draft(project_id, document_type):
    """Create a conservative, template-shaped draft without inferring test outcomes."""
    if document_type not in ("UAT", "User_Guide_Web", "User_Guide_CMS"):
        raise ValueError("Jenis dokumen tidak didukung.")
    project = get_project(project_id)
    project["project_id"] = project_id
    records = _reports(project_id)
    evidence_records = list_evidence(project_id)
    titles = {
        "UAT": "Dokumen User Acceptance Testing",
        "User_Guide_Web": "Panduan Penggunaan Website",
        "User_Guide_CMS": "Panduan Penggunaan Web CMS",
    }
    title = titles[document_type]
    sources = []
    cms_source_available = False

    if document_type == "UAT":
        report_name, result = _report_result(records, "generic_uat")
        if result is None:
            raise ValueError("BLOCKED: laporan Generic UAT belum tersedia. Jalankan Generic UAT Inspection terlebih dahulu.")
        sources.append(report_name)
        sections, unverified = _make_uat_sections(project, result, evidence_records)
        status = "NEEDS_REVIEW"
    elif document_type == "User_Guide_Web":
        report_name, result = _report_result(records, "generic_uat")
        if result is None:
            raise ValueError("BLOCKED: laporan Generic UAT/observasi website belum tersedia.")
        sources.append(report_name)
        sections, unverified = _make_web_guide_sections(project, result, evidence_records)
        status = "NEEDS_REVIEW"
    else:
        sections, unverified, cms_source_available, cms_sources = _make_cms_guide_sections(project, records)
        sources.extend(cms_sources)
        status = "NEEDS_REVIEW" if cms_source_available else "BLOCKED"

    metadata = {
        "project_id": project_id,
        "project_name": project.get("project_name", project_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generation_note": "Draft berbasis sumber yang tersedia; bagian yang belum diverifikasi ditandai untuk review.",
        "template_reference": {
            "UAT": "Sample-UAT.docx",
            "User_Guide_Web": "Struktur panduan website; perlu eksplorasi website",
            "User_Guide_CMS": "Sample-User_Guide_CMS.docx",
        }[document_type],
    }
    content = create_document_content(
        document_type=document_type,
        title=title,
        sections=sections,
        metadata=metadata,
        page_settings={
            "size": "A4", "orientation": "portrait",
            "margin_top_mm": 20, "margin_bottom_mm": 20,
            "margin_left_mm": 20, "margin_right_mm": 20,
        },
    )
    return create_document(
        project_id=project_id,
        document_type=document_type,
        title=f"{title} - {project.get('project_name', project_id)}",
        content=content,
        status=status,
        source_summary={"report_files": sources, "evidence_count": len(evidence_records)},
        unverified_sections=unverified,
    )


def list_project_document_drafts(project_id, document_type=None):
    return list_documents(project_id, document_type)
