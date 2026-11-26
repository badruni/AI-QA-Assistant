# Living QA Playground — Implementation Blueprint
Tanggal: 26 November 2026
Status: Baseline implementasi untuk memulai QA Lab Foundation

## 1. Tujuan
Mengembangkan satu website MyDreamZone lokal menjadi Living QA Playground. Website utama tetap dipertahankan; lima QA Lab menjadi area pengujian di dalam website yang sama. Pola baru yang ditemukan, direproduksi, dan diverifikasi dapat dipertahankan sebagai regression scenario.

## 2. Keputusan scope
- Pertahankan website MyDreamZone dan navigasi Home, Articles, Events, Gallery, Community.
- Tambahkan QA Lab sebagai landing page dengan dropdown akses langsung ke lima lab.
- Lima lab: Normal Scenarios, Negative Test Lab, Accessibility Lab, Responsive Lab, Security Behavior Lab.
- Negative scenarios tersedia di Negative Test Lab dan tidak merusak homepage normal.
- Baseline katalog: 56 komponen + Accordion #57.
- Seluruh 16 Recommended Extensions masuk scope evaluasi/implementasi; Accordion dan Sticky Elements tidak dihitung ganda.
- Sticky Elements diuji sebagai perilaku Header/Responsive Header.
- Tidak menambah dependency tanpa kebutuhan yang terbukti.

## 3. Arsitektur target
### Frontend Playground
- `index.html`: shell MyDreamZone, navigasi, area halaman.
- `assets/styles.css`: layout, responsive behavior, state visual, accessibility focus.
- `assets/app.js`: navigasi lab, renderer katalog, scenario interactions.
- `assets/data/component-catalog.js` (atau JSON): definisi komponen, extension, kategori, status, test coverage.
- `assets/data/scenarios.js` (atau JSON): scenario registry dengan expected result dan metadata.
- `labs/`: halaman/fixture lab bila pemisahan file diperlukan; jangan memecah file hanya demi abstraksi.

### Local server
- Pertahankan loopback-only binding dan path containment.
- Tambahkan endpoint Security Behavior Lab secara eksplisit, terisolasi, dan hanya untuk fixture lokal.
- Jangan mengubah server sampai endpoint contract dan regression test siap.

### AI QA Assistant integration (tahap berikutnya)
- Scanner Orchestrator -> DOM Inventory -> Component Detector -> Scenario Planner -> Safe Interaction Runner -> Evidence -> Result Analyzer -> Report/Regression.
- Deteksi komponen, hasil pengujian, dan temuan bug adalah status terpisah.
- Detection confidence: confirmed / probable / needs_review.
- Test result: not_run / passed / failed / blocked / not_applicable / needs_review.

## 4. Data registry minimum
### Component record
`component_id`, `name`, `group`, `source` (baseline/extension), `implementation_status`, `description`, `detection_hints`, `relevant_labs`, `scenario_ids`, `evidence_refs`, `last_verified`.

### Scenario record
`scenario_id`, `component_id`, `lab_id`, `title`, `purpose`, `preconditions`, `steps`, `expected_result`, `actual_result`, `test_level`, `status`, `evidence_refs`, `bug_id`, `notes`, `last_verified`.

Jangan menyimpan credential, cookie, token, atau nilai input sensitif dalam registry, log, screenshot, maupun report.

## 5. Lab behavior
- Normal: hanya perilaku normal dan placeholder yang memang diharapkan.
- Negative: fixture gagal yang disengaja, selalu diberi komentar `NEGATIVE TEST` atau `INTENTIONAL BUG REPRODUCTION`.
- Accessibility: keyboard, focus, accessible name, role, label, state, struktur semantik.
- Responsive: desktop/tablet/mobile, overflow, clipping, overlap, target size.
- Security Behavior: endpoint lokal terkontrol; tanpa bypass CAPTCHA/WAF/Cloudflare atau akses ke target eksternal.

Komentar fixture:
- `NORMAL PLACEHOLDER`: kondisi awal yang normal dan sumber nilai dinamis.
- `NEGATIVE TEST`: skenario gagal terencana.
- `INTENTIONAL BUG REPRODUCTION`: reproduksi bug dengan expected behavior yang dijelaskan.

## 6. Tahapan implementasi dan acceptance
### D1 — QA Lab Foundation (mulai sekarang)
Deliverable:
- QA Lab landing page.
- Dropdown desktop dan mobile.
- Lima lab dapat dibuka dan berpindah tanpa merusak navigasi lama.
- Navigasi keyboard dan focus state dasar.
Acceptance:
- Semua menu lama tetap berfungsi.
- Semua lima lab dapat diakses dari dropdown dan landing page.
- Tidak ada error JS atau request asset baru yang gagal.
- Tampilan desktop dan mobile tidak overflow.
- Homepage tetap normal; negative fixtures hanya berada di Negative Test Lab.

### D2 — Component Catalog
- Daftarkan 57 komponen dan 16 extension tanpa duplikasi.
- Tampilkan ID, nama, kategori, status implementasi, lab relevan.
- Status source tidak otomatis dianggap runtime Pass.

### D3 — Scenario Registry
- Setiap scenario punya expected result, status awal Not Run, dan relasi komponen/lab.
- Negative scenario dipisahkan dari normal fixture.

### D4 — Component expansion
Prioritaskan kelompok komponen yang belum ada/parsial sesuai dependensi dan nilai pengujian. Pertahankan semua fungsi lama.

### D5 — CMS Playground
Bangun alur CMS lokal yang benar-benar bekerja; tetapkan model konten, autentikasi demo lokal, CRUD aman, preview, validasi, dan relasi ke frontend. Jangan menyimpan kredensial nyata.

### D6 — Scanner, evidence, regression
Integrasi bertahap dengan scanner yang sudah ada. Pertahankan request guard, rate limit, stop threshold 403, client isolation, dan evidence sanitization.

### D7 — Release validation
Regression, dokumentasi penggunaan, setup portabel, backup/rollback, dan validasi paket.

## 7. Strategi implementasi
- Satu paket perubahan terintegrasi per milestone, bukan edit manual satu komponen per sesi.
- Sebelum perubahan: verifikasi root, Git status, dan file sumber; backup eksternal.
- Skrip menolak kondisi awal yang tidak cocok, membuat backup terverifikasi, menulis perubahan terkontrol, menjalankan pemeriksaan, dan memberi instruksi rollback.
- Tidak commit/push kecuali diminta.
- Jangan menggunakan destructive Git commands.
- Jangan menghapus data proyek, evidence, report, log, backup, atau virtual environment.

## 8. Batasan bukti
Status inventory 21 Implemented, 19 Partial, 16 Not Implemented adalah hasil source inspection awal, bukan runtime test seluruh komponen. Hasil browser yang pernah tercatat (HTTP 200, 12 img, 20 buttons, 32 links, nol page/console/request errors) hanya berlaku untuk audit browser awal pada waktu tersebut.

## 9. Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
1. Satu batch konkret per tahap; hindari audit berulang yang tidak membuka jalan ke implementasi.
2. Jelaskan tujuan dan hasil yang diharapkan.
3. Jangan menganggap berhasil sebelum diverifikasi.
4. Diagnosis error sebelum perubahan.
5. Backup sebelum perubahan signifikan.
6. Pertahankan fitur yang berfungsi dan perubahan lokal pengguna.
7. Jalankan regression relevan dan perbarui dokumentasi.
8. Utamakan solusi gratis, lokal, ringan, portabel.
9. Isolasi data klien dan jangan menyimpan secret.
10. Jangan bypass CAPTCHA, Cloudflare, WAF; patuhi batas 403.
11. Jangan memindahkan virtual environment antarperangkat.
12. Jangan commit kecuali diminta; hindari destructive Git commands.
13. Setiap checkpoint mencatat status, backup, perubahan, bukti, risiko, dan next action.
14. Pertahankan visi **Living QA Playground**: setiap pola baru yang diamati, direproduksi, dan diverifikasi dapat menjadi skenario regression permanen.

## 10. Checkpoint aktif
**D1 — QA Lab Foundation.**
Langkah implementasi berikutnya: ambil snapshot aman dari tiga file frontend terkini (`index.html`, `assets/app.js`, `assets/styles.css`) dan Git status laptop kerja. Snapshot ini bukan audit tambahan; ini memastikan perubahan lokal yang sudah ada tetap dipertahankan sebelum skrip implementasi terintegrasi dibuat.
