# AI QA Assistant — Checkpoint M5.2
Tanggal: 24 November 2026

## 1. Status milestone

M5.2 — Evidence Status Separation: SELESAI
Regression test: LULUS

- Total test: 280
- Skipped: 3
- Failed: 0
- Unified QA Workflow tests: 9/9 lulus

## 2. Perubahan implementasi

File utama:
- modules/qa_workflow.py
- tests/test_qa_workflow.py

UnifiedQAWorkflowResult sekarang memiliki field:
- evidence_status
- expected_evidence
- verified_evidence

Aturan evidence_status:
- not_required: tidak ada screenshot yang diharapkan.
- verified: seluruh evidence yang diharapkan berhasil diverifikasi.
- failed: terdapat evidence yang tidak berhasil diverifikasi.

result.status tetap menunjukkan hasil inspeksi QA dan tidak digantikan oleh evidence_status.

Kegagalan evidence verification tetap menyebabkan terminal workflow gagal apabila inspeksi sebelumnya selesai tanpa kegagalan lain.

Progress event juga menyampaikan status evidence dan jumlah verified/expected.

## 3. Pengujian

Test khusus:
python -m unittest tests.test_qa_workflow -v

Hasil:
- 9 tests
- OK

Regression penuh:
python -m unittest discover -s tests -v

Hasil terakhir:
- 280 tests
- 3 skipped
- 0 failed
- OK

## 4. Dokumentasi diperbarui

- docs/PROJECT_SETUP_GUIDE.md
- docs/PORTABLE_SETUP_GUIDE.md

Keduanya menjelaskan:
- evidence_status
- expected_evidence
- verified_evidence
- Perbedaan status inspeksi QA dan status evidence.

Pemeriksaan dokumentasi:
- PROJECT_SETUP_GUIDE.md: seluruh 4 pemeriksaan True.
- PORTABLE_SETUP_GUIDE.md: seluruh 4 pemeriksaan True.

## 5. Backup sebelum perubahan

Backup implementasi:
backups/before_m5_2_evidence_status_20261124_142849

Backup dokumentasi:
backups/before_m5_2_docs_20261124_143954

Backup dokumentasi sudah diverifikasi dengan SHA-256.

## 6. Kondisi proyek

- Aplikasi aktif berada di folder AI_QA_Assistant_RESTORE_20261123.
- Environment: .venv-scanner.
- Python: 3.14.10.
- Playwright: 1.65.1.
- Chromium sudah terpasang dan sebelumnya berhasil diuji headless.
- Data eksternal: <LOCAL_PATH>
- Launcher run_ai_qa_assistant.ps1 tersedia.
- M4 Backup & Restore Verification telah selesai.
- Full regression baseline: 280 tests, 3 skipped.

## 7. Batasan dan catatan

- Belum dilakukan scan website nyata sebagai uji coba M5.
- Generic UAT masih berupa inspeksi DOM berbasis heuristik.
- Temuan Needs Review harus divalidasi manusia sebelum dinyatakan sebagai bug.
- Workflow Unified QA bersifat read-only.
- Tidak melakukan login, submit form, aksi yang mengubah data, CAPTCHA bypass, Cloudflare bypass, atau WAF bypass.
- Gunakan hanya website yang memiliki izin pengujian.
- Jangan mengklaim evidence jika belum berhasil diverifikasi.

## 8. Langkah berikutnya — QA Playground

Rencana checkpoint berikutnya:

1. Audit konfigurasi dan kesiapan QA Playground.
2. Pastikan target dan cakupan pengujian memang diizinkan.
3. Siapkan atau verifikasi project khusus QA Playground.
4. Jalankan satu uji coba Unified QA secara terkontrol.
5. Periksa hasil Frontend Inspection, Website Discovery, Generic UAT, dan Authentication Discovery.
6. Periksa screenshot, evidence registry, dan SHA-256.
7. Periksa laporan JSON dan bandingkan dengan kondisi website yang benar-benar diamati.
8. Catat bug terkonfirmasi, temuan Needs Review, keterbatasan, dan perbaikan berikutnya.

Jangan memulai scan sebelum konfigurasi dan otorisasi diverifikasi.

## 9. Instruksi melanjutkan sesi

Mulai dari:
"Melanjutkan AI QA Assistant dari checkpoint M5.2. Seluruh 280 regression tests lulus dengan 3 skipped. Mari mulai audit kesiapan dan uji coba QA Playground secara bertahap."

Kerjakan satu checkpoint pada satu waktu. Jangan menganggap suatu langkah berhasil sebelum output diverifikasi.
