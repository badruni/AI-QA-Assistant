# Full Component Catalog + Scenario Engine — Implementation Batch

Tanggal: 26 November 2026

## Cakupan
- Catalog baseline 56 komponen ditambah Accordion #57.
- Setiap record memuat source status, source evidence, gap, category, selector candidates, relevant labs, confidence, runtime detection status, matched selectors, timestamp.
- Scenario registry menambahkan satu DOM candidate scan scenario per komponen (57 skenario) di samping 15 smoke/simulation scenarios yang sudah ada.
- Catalog scan berjalan pada DOM halaman aktif; tidak melakukan crawling, request eksternal, atau interaksi destruktif.
- Scenario run merekam component_id, hasil, evidence selector/matches, waktu, URL, dan viewport.
- `blocked` digunakan jika tidak tersedia selector kandidat yang aman; `needs_review` tidak dipaksakan menjadi pass/fail.
- Export evidence menggunakan schema 2.0 dan ringkasan execution records, unique scenarios, passed, failed, blocked.

## Makna hasil scanner
- `source_status`: klasifikasi source inventory awal (implemented/partial/not_implemented), bukan runtime result.
- `detected`: satu atau lebih selector kandidat ditemukan pada DOM.
- `not_detected`: tidak ada selector kandidat ditemukan.
- `needs_review`: selector tidak tersedia atau selector tidak valid.
- DOM candidate scan menguji kecocokan selector saja; tidak membuktikan interaksi/behavior komponen.
- Untuk komponen not_implemented, tidak ditemukannya selector hanya berarti kandidat tersebut tidak ditemukan; bukan bukti mutlak fitur tidak ada.
- `passed` untuk scan berarti hasil kandidat konsisten dengan source status awal. Itu bukan bukti komponen berfungsi penuh.
- Accordion #57 dipisahkan sebagai komponen tersendiri sesuai keputusan scope proyek.

## Scenario Engine
- 15 smoke/simulation scenarios dipertahankan.
- 57 DOM candidate scenarios ditambahkan.
- `Run safe checks` menjalankan semua skenario non-security, termasuk DOM candidate scans.
- Security scenarios tetap manual dan simulasi lokal; bukan HTTP test atau penetration test.
- Execution records dan unique scenario count dibedakan di evidence export.

## Batasan saat ini
- Belum ada Playwright-driven per-component interaction suite.
- Belum ada screenshot evidence capture otomatis untuk setiap scenario.
- Belum ada Python frontend scanner API integration.
- Selector candidates perlu ditinjau dan ditingkatkan untuk elemen kompleks/komponen yang belum ada.
- Source inventory statuses masih bersumber dari source audit 26-Nov-2026 dan perlu runtime confirmation.

## Acceptance checklist untuk pengujian pengguna
1. Catalog menampilkan 57 records.
2. Search filter bekerja.
3. `Scan DOM catalog` memperbarui runtime status dan menghasilkan records untuk selector candidates.
4. Skenario dengan selector tak tersedia menjadi blocked/needs_review, bukan fabricated pass.
5. `Run safe checks` menjalankan 57 DOM candidate scenarios plus 13 existing non-security scenarios (jumlah tepat dapat berbeda jika blocked scenarios tidak memiliki selector candidates).
6. Security scenarios tetap dikecualikan dari Run safe checks.
7. Evidence JSON schema 2.0 berisi 57 components, scenario registry, execution results, dan unique scenario summary.
8. Existing homepage interactions remain functional.

## Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
- Satu implementasi terpadu per batch; lakukan verifikasi menyeluruh setelah pemasangan.
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
