# Checkpoint A — Component Detection Accuracy: Semantics Fix Batch

Tanggal: 26 November 2026

## Masalah yang diperbaiki
Hasil sebelumnya menampilkan Runtime Detection 35 detected, 21 not detected, 1 needs review bersamaan dengan 52 Passed. Angka tersebut berasal dari dua konsep berbeda. Label Passed dan logika evaluasi sebelumnya menyamakan source_status bukan not_implemented dengan ekspektasi harus ditemukan, sehingga komponen PARTIAL dinilai seolah-olah wajib ditemukan.

## Perubahan batch
- Memisahkan `runtime_detection` (`detected`, `not_detected`, `needs_review`) dari `expectation_status` (`match`, `mismatch`, `review`).
- Source `not_implemented` + runtime `not_detected` = expectation match; ini bukan bukti global ketiadaan fitur.
- Source `implemented` + runtime `detected` = expectation match; ini bukan bukti perilaku lulus.
- Source `partial` selalu expectation review, baik kandidat ditemukan maupun tidak, karena kelengkapan fitur belum terbukti.
- Selector ditemukan untuk CMP-025/CMP-026 diberi klasifikasi `static_visual_match`; tidak mengklaim counter dinamis.
- CMP-035 diberi klasifikasi `specialized_partial_match`; drawer tidak disamakan dengan reusable accordion/disclosure.
- CMP-043 diberi klasifikasi `partial_match`; highlight tile tidak disamakan dengan article card lengkap.
- CMP-033 memisahkan CSS hover evidence dari keyboard-equivalent validation; behavior dan keyboard tetap `not_tested`.
- Dashboard mengubah label `Passed` menjadi `Expectation Match` dan memberi keterangan bahwa ini bukan behavior pass.
- Evidence JSON mengekspor runtime counts, expectation counts, scenario execution counts, dan behavior_not_tested secara terpisah.
- Scan DOM catalog menjalankan tiap component scenario satu kali; menghindari pemindaian ganda pada tombol scan.

## Makna status
- `detected`: selector atau sinyal CSS kandidat ditemukan.
- `not_detected`: selector kandidat tidak ditemukan pada dokumen aktif; bukan bukti mutlak fitur tidak ada.
- `needs_review`: pemeriksaan tidak konklusif atau kandidat tidak tersedia/invalid.
- `match`: hasil runtime konsisten dengan source inventory.
- `mismatch`: hasil runtime bertentangan dengan source inventory.
- `review`: source partial atau evidence belum cukup.
- `behavior_status=not_tested`: fungsi komponen belum diuji melalui interaksi.

## Batasan
Belum ada Playwright interaction tests. Hover CSS detection bukan validasi interaksi pointer maupun keyboard. Perilaku counter, article card, drawer, dan komponen lainnya belum diuji. Browser runtime verification tetap harus dilakukan pada perangkat pengguna.

## Verifikasi build
- JavaScript syntax check dengan Node jika tersedia.
- ZIP integrity test.
- Static assertions untuk pemisahan runtime/expectation/behavior dan evidence summary.
- Tidak ada dependensi baru.

## Batch workflow yang disepakati
1. Checkpoint A — Component Detection Accuracy: 1 batch.
2. Checkpoint B — Component Detection Stabilization: 1 batch.
3. Checkpoint C — Scenario Engine: 1 batch.
4. Checkpoint D — Playwright Scanner Integration: 1 batch.
5. Checkpoint E — Evidence & Bug Analysis: 1 batch.
6. Checkpoint F — QA Report & Regression: 1 batch.

Satu batch per checkpoint; verifikasi tetap dilakukan sebelum pindah checkpoint.

## Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
- Satu implementasi terpadu per batch; analisis, perubahan terkait, dokumentasi, dan verifikasi diselesaikan dalam batch tersebut.
- Jangan menganggap implementasi berhasil sebelum hasil verifikasi tersedia.
- Pertahankan fitur yang berfungsi; backup sebelum perubahan besar.
- Jangan menghapus data proyek, laporan, evidence, atau log.
- Pisahkan kode aplikasi dari data pengguna/klien.
- Jangan menyimpan password, token, cookie, atau kredensial di log.
- Jangan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan; hentikan pemindaian setelah batas 403 terkonfigurasi tercapai.
- Setiap laptop membuat virtual environment sendiri; jangan memindahkan venv.
- Jangan menambah dependensi tanpa alasan; utamakan gratis, lokal, ringan, portabel.
- Perbarui dokumentasi untuk perubahan arsitektur, dependensi, cara menjalankan, dan riwayat perubahan.
- Visi produk: satu website MyDreamZone dengan lima QA Lab terisolasi — Normal Scenarios, Negative Test Lab, Accessibility Lab, Responsive Lab, Security Behavior Lab.

## Addendum — CMP-033 CSSOM traversal correction

Tanggal: 26 November 2026

### Bukti runtime yang diterima
Pemeriksaan manual di Chrome DevTools menunjukkan tujuh aturan `:hover` dapat dibaca. Pemeriksaan DOM menunjukkan seluruh trigger selector dan target selector memiliki jumlah elemen lebih dari nol:
- `.main-nav a:hover`: 6 trigger / 6 target
- `tbody tr:hover`: 3 trigger / 3 target
- `.highlight-card:hover img`: 5 trigger / 5 target
- `.reel-image:hover img`: 1 trigger / 1 target
- `.gallery-image:hover img`: 3 trigger / 3 target
- `.hero-arrow:hover`: 2 trigger / 2 target
- `.qa-lab-card:hover`: 5 trigger / 5 target

### Perubahan tambahan
Traversal CSSOM kini memproses `selectorText` pada rule saat ini sebelum menelusuri `cssRules` bertingkat. Ini menghindari kemungkinan rule style terlewat karena traversal sebelumnya melakukan `return` segera ketika menemukan properti `cssRules`.

### Batas verifikasi
- Bukti CSS hover dan keberadaan elemen target bukan bukti interaksi hover berhasil saat mouse diarahkan.
- `behavior_status` tetap `not_tested`.
- `keyboard_equivalent_status` tetap `not_tested`.
- Browser runtime setelah pemasangan batch ini wajib diverifikasi ulang melalui Scan DOM catalog.
