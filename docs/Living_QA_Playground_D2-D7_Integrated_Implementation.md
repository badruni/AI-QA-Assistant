# Living QA Playground — Integrated D2–D7 Implementation

Tanggal: 26 November 2026

## Sasaran
Satu implementasi terpadu untuk Component Catalog, Scenario Registry, lima lab QA, evidence export, dan regression smoke checks.

## Implementasi frontend yang disertakan
- D2: component catalog dan scenario registry terstruktur di runtime.
- D3: normal scenario checks untuk route, tabs, theme control, dan gallery dialog.
- D4: negative simulations terisolasi; tidak merusak homepage dan tidak mengirim request.
- D5: accessibility checks dasar dan responsive viewport/overflow checks.
- D6: security behavior simulator lokal, termasuk stop threshold 403 simulasi.
- D7: safe regression runner, per-session execution records, JSON evidence export.

## Data model
Component:
`id, name, selector, category, confidence, detection_status, evidence_refs`

Scenario:
`id, name, lab, component_id, purpose, preconditions, steps, expected_result, actual_result, status, evidence_ref, severity, last_verified`

Execution result:
`scenario_id, name, lab, status, actual_result, evidence, executed_at, page_url, viewport`

## Batasan penting / integrasi scanner
D7 pada paket ini menyediakan runner regresi frontend dan format evidence JSON. Paket ini tidak mengklaim telah menghubungkan atau menjalankan Python `modules/frontend_scanner.py`, karena kontrak API antara browser dan scanner lokal belum diverifikasi dari kode scanner dan server lokal. Tidak ada endpoint server baru yang ditebak atau dibuat. Integrasi backend scanner harus dilakukan setelah kontrak aktualnya diperiksa, tanpa mengubah perilaku scanner yang sudah berfungsi.

## Evidence
JSON export berisi data komponen, skenario, dan hanya hasil yang benar-benar dieksekusi dalam sesi browser. Security test merupakan simulasi UI lokal, bukan penetration test dan bukan hasil HTTP 403 sungguhan. Hasil responsive/accessibility bersifat pemeriksaan otomatis dasar dan membutuhkan pemeriksaan manual tambahan.

## Verifikasi penerimaan
1. QA Workbench tampil pada QA Lab.
2. Component Catalog menampilkan inventaris dan pencarian berfungsi.
3. Lima lab menampilkan skenario sesuai kategorinya.
4. Run safe checks mengeksekusi skenario non-security dan mengisi hasil aktual.
5. Negative simulations tidak mengirim request dan tidak mengubah homepage.
6. Security simulator berhenti tepat pada batas angka yang diatur; simulasi bukan request nyata.
7. Evidence JSON dapat diekspor dan memuat hasil sesi yang dieksekusi.
8. Homepage, theme, drawer, hero carousel, gallery modal tetap berfungsi.
9. Browser Console tidak menunjukkan error baru.
10. Desktop dan mobile tidak mengalami layout overflow baru.

## Tidak termasuk klaim pada paket ini
- Full browser automation terhadap semua 56/57 komponen.
- Screenshot capture otomatis atau pixel-diff.
- Python scanner integration / crawler orchestration.
- Server-side persistence, multi-client database, CMS workflow.
- Penetration testing atau pemeriksaan keamanan eksternal.

## Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
- Satu implementasi terpadu; lakukan satu rangkaian verifikasi menyeluruh setelah pemasangan.
- Jangan menganggap implementasi berhasil sebelum diuji.
- Pertahankan kode dan fitur yang sudah berfungsi; backup sebelum perubahan besar.
- Jangan menghapus data proyek, laporan, evidence, atau log.
- Pisahkan kode aplikasi dari data pengguna/klien.
- Jangan menyimpan password, token, cookie, atau kredensial dalam log.
- Jangan melakukan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.
- Hentikan pemindaian setelah batas 403 terkonfigurasi tercapai.
- Setiap laptop membuat virtual environment sendiri; jangan memindahkan venv.
- Perbarui dokumentasi untuk perubahan arsitektur, dependensi, dan cara menjalankan.
- Visi: satu website MyDreamZone dengan lima lab QA terpisah; negative test terisolasi dari homepage normal.


## Patch — Scenario status refresh & UI polish
- Setelah setiap eksekusi, daftar lab terkait dirender ulang sehingga `not_run` langsung berubah menjadi `passed` atau `failed`.
- Baris skenario menampilkan hasil aktual terakhir dan tombol `Run again`.
- Component Catalog tetap menggunakan `declared` untuk komponen yang didaftarkan; status tersebut bukan status hasil tes.
- Workbench header, tombol aksi, summary cards, tabs, dan result cards dirapikan untuk desktop/mobile.
- `Executed` dan `Passed` tetap menghitung execution records pada sesi aktif; pengulangan skenario menambah record baru.
