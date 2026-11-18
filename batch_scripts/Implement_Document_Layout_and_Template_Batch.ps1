$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
$Python = Join-Path $Root '.venv-scanner\Scripts\python.exe'
$Targets = @('core\document_viewer.py','modules\documentation_generator.py','core\docx_renderer.py','docs\PROJECT_SETUP_GUIDE.md')
foreach ($File in $Targets) { if (-not (Test-Path (Join-Path $Root $File) -PathType Leaf)) { throw "File wajib tidak ditemukan: $File" } }
if (-not (Test-Path $Python -PathType Leaf)) { throw "Python scanner tidak ditemukan: $Python" }
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupDir = Join-Path $Root "backups\before_document_layout_template_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
foreach ($File in $Targets) { $Destination = Join-Path $BackupDir $File; New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null; Copy-Item (Join-Path $Root $File) $Destination -Force }
Write-Host "Backup dibuat: $BackupDir"
$PatchPath = Join-Path $env:TEMP 'apply_document_layout_template_patch.py'
@'
from pathlib import Path
import math
root = Path.cwd()

# Viewer: scale evidence down to the available printable A4 content rectangle.
vp = root / 'core' / 'document_viewer.py'
v = vp.read_text(encoding='utf-8')
if 'import math\n' not in v:
    v = v.replace('import re\n', 'import re\nimport math\n')
old = '''                            photo = tk.PhotoImage(file=str(image_path))
                            factor = max(1, int(max(photo.width(), photo.height()) / (460 * self.zoom_percent / 100)))
                            if factor > 1:
                                photo = photo.subsample(factor, factor)
                            self._image_refs.append(photo)
                            self.canvas.create_image(x, y, anchor="nw", image=photo)
                            y += photo.height() + int(10 * self.zoom_percent / 100)
'''
new = '''                            photo = tk.PhotoImage(file=str(image_path))
                            page_right = 30 + width - margin
                            page_bottom = 25 + height - margin - int(28 * self.zoom_percent / 100)
                            max_width = max(1, page_right - x)
                            max_height = max(1, page_bottom - y)
                            factor = max(1, math.ceil(photo.width() / max_width), math.ceil(photo.height() / max_height))
                            if factor > 1:
                                photo = photo.subsample(factor, factor)
                            if photo.width() <= max_width and photo.height() <= max_height:
                                self._image_refs.append(photo)
                                self.canvas.create_image(x, y, anchor="nw", image=photo)
                                y += photo.height() + max(6, int(10 * self.zoom_percent / 100))
                            else:
                                self.canvas.create_text(x, y, anchor="nw", text="[Evidence terlalu besar untuk area halaman]", font=("Arial", max(8, int(9 * self.zoom_percent / 100))), fill="#555555")
                                y += max(24, int(28 * self.zoom_percent / 100))
'''
if old not in v:
    raise SystemExit('Pola render gambar tidak cocok. Patch dihentikan tanpa menulis viewer.')
v = v.replace(old, new)
vp.write_text(v, encoding='utf-8')

# DOCX: repeat header row when tables span multiple pages and emphasize header labels.
rp = root / 'core' / 'docx_renderer.py'
r = rp.read_text(encoding='utf-8')
old = '''                table = doc.add_table(rows=1, cols=len(block["headers"]))
                table.style = "Table Grid"
                for cell, value in zip(table.rows[0].cells, block["headers"]):
                    cell.text = value
'''
new = '''                table = doc.add_table(rows=1, cols=len(block["headers"]))
                table.style = "Table Grid"
                table.autofit = True
                header_row = table.rows[0]
                header_properties = header_row._tr.get_or_add_trPr()
                from docx.oxml import OxmlElement
                from docx.oxml.ns import qn
                repeat_header = OxmlElement("w:tblHeader")
                repeat_header.set(qn("w:val"), "true")
                header_properties.append(repeat_header)
                for cell, value in zip(header_row.cells, block["headers"]):
                    cell.text = value
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
'''
if old not in r:
    raise SystemExit('Pola tabel DOCX tidak cocok. Patch dihentikan.')
r = r.replace(old, new)
rp.write_text(r, encoding='utf-8')

# Generator: append a new template-aware builder and redirect the public API to it.
gp = root / 'modules' / 'documentation_generator.py'
g = gp.read_text(encoding='utf-8')
if 'def _generate_template_shaped_draft(' not in g:
    g += '''\n\ndef _generate_template_shaped_draft(project_id, document_type):\n    """Build a conservative template-shaped draft from observed reports only."""\n    if document_type not in ("UAT", "User_Guide_Web", "User_Guide_CMS"):\n        raise ValueError("Jenis dokumen tidak didukung.")\n    project = get_project(project_id)\n    records = _reports(project_id)\n    evidence_records = list_evidence(project_id)\n    title = {"UAT": "User Acceptance Testing", "User_Guide_Web": "Panduan Penggunaan Website", "User_Guide_CMS": "Panduan Penggunaan Web CMS"}[document_type]\n    metadata = {"project_id": project_id, "project_name": project.get("project_name", project_id), "generated_at": datetime.now(timezone.utc).isoformat(), "generation_note": "Draft template-shaped; isi hanya dari sumber teramati."}\n    sections, unverified, sources = [], [], []\n    def table(headers, rows):\n        return {"type": "table", "headers": headers, "rows": rows}\n    if document_type == "UAT":\n        report_name, result = _report_result(records, "generic_uat")\n        if result is None:\n            raise ValueError("BLOCKED: laporan Generic UAT belum tersedia.")\n        sources.append(report_name)\n        pages, findings = result.get("pages") or [], result.get("findings") or []\n        page_rows = [[str(p.get("page_url", "-")), str(p.get("http_status") or "-"), str(p.get("status", "Needs Review")), json.dumps(p.get("component_summary") or {}, ensure_ascii=False)] for p in pages] or [["Belum tersedia", "-", "Needs Review", "-"]]\n        sections.append(make_section("Informasi Dokumen", [table(["Informasi", "Detail"], [["Proyek", str(project.get("project_name", project_id))], ["Aplikasi yang diuji", "Website — perlu dikonfirmasi"], ["Alamat website", str(pages[0].get("page_url", "Belum tersedia")) if pages else "Belum tersedia"], ["Versi dokumen", "Draft 1"], ["Tanggal pembaruan", datetime.now(timezone.utc).strftime("%d-%m-%Y")], ["Aktor pengujian", "Belum ditentukan"], ["Lingkungan dan versi aplikasi", "Diisi sebelum UAT"], ["Nama penguji dan periode UAT", "Diisi oleh QA"]])], "document-information"))\n        sections.append(make_section("Pendahuluan", [{"type":"heading","level":2,"text":"2.1 Tujuan Pengujian"},{"type":"paragraph","text":"Dokumen menjadi acuan pencatatan UAT. Fungsi harus diuji QA/pengguna terhadap hasil yang disepakati."},{"type":"heading","level":2,"text":"2.2 Kriteria Penerimaan"},{"type":"paragraph","text":"Kriteria penerimaan harus disepakati sebelum eksekusi. Kasus Tidak sesuai, Belum bisa dicoba, atau Tidak berlaku perlu dibahas."},{"type":"heading","level":2,"text":"2.3 Lingkup Pengujian"},{"type":"paragraph","text":"Sumber yang tersedia hanya observasi DOM read-only, bukan pengujian alur bisnis."},table(["Kode","Modul","Jumlah","Cakupan"],[["OBS","Halaman teramati",str(len(pages)),"Observasi teknis saja"]]),table(["Halaman","HTTP","Status inspeksi","Komponen terdeteksi"],page_rows),{"type":"heading","level":2,"text":"2.4 Ketentuan Pelaksanaan"},{"type":"paragraph","text":"Isi identitas dan lingkungan sebelum UAT. Jangan melakukan submit atau perubahan data tanpa izin. Catat hasil aktual dan evidence setelah diamati."}], "introduction"))\n        test_rows = [[f"OBS-{i:03d}","Halaman teramati","Validasi fungsional belum ditentukan","Belum dieksekusi","Belum ditentukan","Ditetapkan QA/reviewer","Not Tested"] for i,_ in enumerate(pages,1)] or [["TBD-001","Belum ditentukan","Belum disusun","Belum dieksekusi","Belum ditentukan","Ditetapkan QA","Not Tested"]]\n        finding_rows = [[str(f.get("page_url","-")),str(f.get("category","-")),str(f.get("element","-")),str(f.get("issue","-")),"Needs Review"] for f in findings] or [["-","-","-","Tidak ada indikasi struktural; bukan bukti semua fungsi berhasil.","Needs Review"]]\n        sections.append(make_section("Skenario Pengujian", [{"type":"paragraph","text":"Kerangka test case berikut belum dieksekusi. Skenario, langkah, data uji, dan expected result harus ditetapkan QA."},table(["ID Test Case","Modul / Fitur","Skenario Pengujian","Langkah Pengujian","Data Uji","Hasil yang Diharapkan","Status"],test_rows),table(["Halaman","Kategori","Elemen","Observasi","Status"],finding_rows)], "test-scenarios"))\n        sections.append(make_section("Catatan Pengujian", [{"type":"paragraph","text":"Catat kendala setelah pengujian dengan ID Test Case."},table(["ID Test Case","Yang Terjadi","Catatan atau Kendala","Foto atau Tautan"],[["Belum tersedia","Belum ada catatan manual","Diisi QA","Evidence terverifikasi"]])], "test-notes"))\n        sections.append(make_section("Persetujuan Hasil Pengujian", [{"type":"paragraph","text":"Diisi setelah pengujian selesai dan dibahas bersama."},table(["Rekap status","Jumlah"],[["Sesuai","Belum dihitung"],["Tidak sesuai","Belum dihitung"],["Belum bisa dicoba","Belum dihitung"],["Belum dicoba","Belum dihitung"],["Tidak berlaku","Belum dihitung"]]),{"type":"paragraph","text":"Hasil akhir: Belum diputuskan."},table(["Peran","Nama","Tanggal","Paraf atau Tanda Tangan"],[["Penguji","________","________","________"],["Pendamping dari tim","________","________","________"],["Wakil pengguna","________","________","________"]])], "approval"))\n        for i,p in enumerate(pages,1):\n            url=p.get("page_url"); eid=_evidence_for_page(project_id,url,evidence_records) if url else None\n            if eid: sections.append(make_section(f"Lampiran Evidence {i}",[{"type":"image","evidence_id":eid,"caption":f"Screenshot observasi: {url}","alt":"Screenshot halaman hasil inspeksi"}],f"evidence-{i}"))\n        unverified.extend(["Identitas penguji, lingkungan, versi aplikasi, dan periode UAT belum diisi.","Test case, langkah, data uji, expected result, dan acceptance criteria harus ditetapkan sebelum eksekusi.","Actual result dan status belum diuji; kerangka test case berstatus Not Tested.","Status Passed pada Generic UAT adalah status inspeksi DOM, bukan bukti keberhasilan fungsi bisnis.","Persetujuan dan keputusan penerimaan belum dilakukan."])\n    elif document_type == "User_Guide_Web":\n        report_name,result=_report_result(records,"generic_uat")\n        if result is None: raise ValueError("BLOCKED: laporan Generic UAT/observasi website belum tersedia.")\n        sources.append(report_name); pages=result.get("pages") or []\n        sections.append(make_section("Version History",[table(["Version","Date","Author","Change Log"],[["1",datetime.now(timezone.utc).strftime("%d/%m/%Y"),"Belum ditentukan","Inisiasi dari observasi website"]])],"version-history"))\n        sections.append(make_section("Ruang Lingkup",[{"type":"paragraph","text":"Panduan mencatat halaman yang teramati. Tujuan, alur, dan instruksi operasional harus dikonfirmasi sebelum diterbitkan."}],"scope"))\n        sections.append(make_section("Daftar Isi",[{"type":"numbered_list","items":["Informasi Website","Halaman yang Diamati","Panduan Penggunaan Terverifikasi","Catatan dan Evidence"]}],"table-of-contents"))\n        rows=[[str(p.get("page_url","-")),str(p.get("http_status") or "-"),str(p.get("status","Needs Review")),json.dumps(p.get("component_summary") or {},ensure_ascii=False)] for p in pages]\n        sections.append(make_section("Halaman yang Diamati",[table(["URL Halaman","HTTP","Status Observasi","Komponen Terdeteksi"],rows or [["Belum tersedia","-","Needs Review","-"]])],"observed-pages"))\n        sections.append(make_section("Panduan Penggunaan Terverifikasi",[{"type":"paragraph","text":"Belum tersedia langkah penggunaan yang diverifikasi manual. Ringkasan DOM bukan instruksi operasional."}],"verified-usage"))\n        unverified.extend(["Tujuan halaman dan alur navigasi perlu dikonfirmasi.","Deskripsi field, tombol, dan langkah penggunaan belum diverifikasi.","Evidence hanya ditampilkan bila terdaftar dan hash valid."])\n        for i,p in enumerate(pages,1):\n            url=p.get("page_url"); eid=_evidence_for_page(project_id,url,evidence_records) if url else None\n            if eid: sections.append(make_section(f"Evidence Halaman {i}",[{"type":"image","evidence_id":eid,"caption":str(url),"alt":"Screenshot website"}],f"web-evidence-{i}"))\n    else:\n        cms_reports=[(n,p.get("result") or {}) for n,p in records if p.get("inspection_type")=="cms_exploration"]\n        sources.extend(n for n,_ in cms_reports)\n        sections.append(make_section("Version History",[table(["Version","Date","Author","Change Log"],[["1",datetime.now(timezone.utc).strftime("%d/%m/%Y"),"Belum ditentukan","Inisiasi panduan CMS"]])],"version-history"))\n        sections.append(make_section("Ruang Lingkup",[{"type":"paragraph","text":"Panduan CMS hanya akan menjelaskan elemen dan prosedur yang telah diamati dan diverifikasi. Tidak ada perubahan data selama penyusunan draft."},table(["Item sumber","Kondisi"],[["CMS URL",str(project.get("cms_url") or "Belum dikonfigurasi")],["Laporan eksplorasi CMS","Tersedia" if cms_reports else "Belum tersedia"],["Dashboard/menu/field/tombol","Belum diverifikasi"],["Langkah operasional","Belum diverifikasi"]])],"scope"))\n        sections.append(make_section("Daftar Isi",[{"type":"numbered_list","items":["Login","Dashboard","Menu dan Submenu CMS","Panduan Penggunaan Fitur"]}],"table-of-contents"))\n        for h,t,sid in [("1. Login","URL, field login, tombol, dan alur setelah login belum boleh dijelaskan sebelum diamati.","cms-login"),("2. Dashboard","Ringkasan dashboard, navigasi, pencarian, dan kontrol akun belum diverifikasi.","cms-dashboard"),("3. Menu dan Submenu CMS","Nama menu dan submenu ditambahkan berdasarkan eksplorasi CMS.","cms-navigation"),("4. Panduan Penggunaan Fitur","Langkah tambah/edit/hapus hanya ditulis setelah prosedur dan otorisasi diverifikasi.","cms-procedures")]: sections.append(make_section(h,[{"type":"paragraph","text":t}],sid))\n        unverified.extend(["Login CMS, dashboard, navigasi, menu, dan submenu perlu dieksplorasi.","Nama field, tombol, hak akses, dan hasil tindakan belum diverifikasi.","Instruksi tambah/edit/hapus belum disusun; tidak ada operasi data yang dijalankan."])\n    content=create_document_content(document_type=document_type,title=title,sections=sections,metadata=metadata,page_settings={"size":"A4","orientation":"portrait","margin_top_mm":20,"margin_bottom_mm":20,"margin_left_mm":20,"margin_right_mm":20})\n    has_cms=any(p.get("inspection_type")=="cms_exploration" for _,p in records)\n    status="BLOCKED" if document_type=="User_Guide_CMS" and not has_cms else "NEEDS_REVIEW"\n    return create_document(project_id=project_id,document_type=document_type,title=f"{title} - {project.get('project_name',project_id)}",content=content,status=status,source_summary={"report_files":sources,"evidence_count":len(evidence_records)},unverified_sections=unverified)\n\n\ndef generate_document_draft(project_id, document_type):\n    return _generate_template_shaped_draft(project_id, document_type)\n'''
    g += replacement
    gp.write_text(g, encoding='utf-8')

# Add setup guide note without disturbing existing sections.
dp = root / 'docs' / 'PROJECT_SETUP_GUIDE.md'
d = dp.read_text(encoding='utf-8')
heading = '## Documentation Generator — Template Drafts and A4 Evidence Layout'
if heading not in d:
    d = d.rstrip() + '\n\n' + heading + '\n- Draft UAT follows the Sample-UAT section structure. DOM observations are not converted into functional Passed/Failed test cases; unexecuted cases remain Not Tested.\n- Web and CMS guide drafts use template-shaped sections. Unobserved CMS procedures remain unverified and CMS stays BLOCKED without a CMS exploration report.\n- A4 Print Preview constrains verified PNG evidence to the printable content rectangle. DOCX tables repeat header rows across pages.\n'
dp.write_text(d, encoding='utf-8')
print('Patch source applied.')
'@ | Set-Content -Path $PatchPath -Encoding UTF8
Write-Host "`nMenerapkan pembaruan template dan layout..."
& $Python $PatchPath
if ($LASTEXITCODE -ne 0) { throw "Patch gagal diterapkan. Backup tersedia di $BackupDir" }
Write-Host "`nMenjalankan syntax check..."
& $Python -m py_compile .\core\document_viewer.py .\core\docx_renderer.py .\modules\documentation_generator.py
if ($LASTEXITCODE -ne 0) { throw "Syntax check gagal. Backup tersedia di $BackupDir" }
Write-Host "`nPerubahan diterapkan."
Write-Host "Backup: $BackupDir"
Write-Host 'Syntax check: PASSED'
Write-Host 'Tes terfokus dan full regression belum dijalankan.'
