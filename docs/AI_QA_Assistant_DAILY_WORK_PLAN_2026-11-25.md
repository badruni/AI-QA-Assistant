# Jadwal Kerja Harian — AI QA Assistant + MyDreamZone
**Versi:** 1.0
**Dibuat:** 25 November 2026
**Jam kerja:** 10 jam per hari, Senin–Jumat
**Mulai:** Kamis, 26 November 2026
**Target utama:** 25 hari kerja (250 jam)
**Cadangan:** 5 hari kerja (50 jam)
**Target selesai rencana:** Kamis, 31 Desember 2026
**Buffer hingga:** Jumat, 8 Januari 2027

> Jadwal ini adalah rencana kerja, bukan jaminan selesai. Tanggal 25 Desember 2026 dan 1 Januari 2027 diasumsikan libur. Sabtu dan Minggu tidak dijadwalkan. Jika ada hari libur/cuti tambahan, jadwal bergeser.

---

## Cara menggunakan jadwal

- Satu hari = maksimal satu checkpoint utama dengan hasil yang bisa diverifikasi.
- Jangan pindah ke hari berikutnya jika acceptance criteria hari berjalan belum terpenuhi. Jika tertunda, geser pekerjaan berikutnya; jangan menumpuk perubahan besar.
- Jika pekerjaan selesai lebih cepat, gunakan sisa waktu untuk test, review, dokumentasi, dan regression, bukan menambah scope baru.
- Semua backup berada di folder `_OLD` eksternal.
- Script sementara dibuat di luar repository dan diarsipkan setelah digunakan.
- `Pass` hanya diberikan jika hasil aktual dan evidence diperiksa.
- Setiap hari akhiri dengan update matriks requirement/test case, changelog bila perlu, dan checkpoint.

### Pembagian waktu harian (10 jam)

| Aktivitas | Alokasi |
|---|---:|
| Review checkpoint, tujuan, dan audit kondisi awal | 1 jam |
| Implementasi / konfigurasi | 5 jam |
| Unit & integration test | 2 jam |
| E2E / pemeriksaan manual / evidence | 1 jam |
| Dokumentasi, matriks, backup/status, checkpoint | 1 jam |
| **Total** | **10 jam** |

Pembagian dapat berubah mengikuti jenis pekerjaan, tetapi pengujian dan dokumentasi tidak boleh dihilangkan untuk mengejar coding.

---

# Rencana 25 hari kerja utama

## Minggu 1 — Baseline, matriks, dan frontend Playground

### Hari 1 — Kamis, 26 November 2026
**Fokus:** verifikasi dokumen dan kondisi repository.

Pekerjaan:
1. Pastikan Master Project Roadmap dan checkpoint terbaru ada di `docs`.
2. Periksa `git status`, `.gitignore`, allowlist Git Manager, dan struktur `local_test_site`.
3. Audit `playground/index.html`, `assets/app.js`, `assets/styles.css`, seluruh aset, dan `playground_server.py`.
4. Pastikan server lokal tidak sedang berjalan tanpa disengaja.
5. Buat daftar implementasi aktual vs 56 kategori komponen; jangan menganggap tampilan statis sebagai fitur selesai.

Hasil wajib:
- Dua dokumen perencanaan terverifikasi di `docs`.
- Laporan audit kondisi awal dan daftar file yang akan disentuh.
- Tidak ada perubahan source code sebelum audit selesai.
- Status Git dan file untracked tercatat.

### Hari 2 — Jumat, 27 November 2026
**Fokus:** matriks requirement dan test case frontend.

Pekerjaan:
1. Buat `docs/REQUIREMENTS_TEST_MATRIX.md` atau format tabel yang disepakati.
2. Masukkan 56 kategori komponen dan skenario fungsional yang sudah disepakati.
3. Tambahkan kolom requirement ID, test case ID, precondition, langkah, expected result, test level, actual result, status, evidence, bug ID, severity.
4. Tandai status berdasarkan bukti yang sudah ada; carousel saja yang memiliki 8 pemeriksaan manual yang dilaporkan lulus.
5. Tentukan urutan kelompok komponen dan dependency.

Hasil wajib:
- Matriks awal tersedia dan tidak mengklaim fitur belum diuji sebagai Pass.
- Daftar prioritas frontend untuk implementasi berikutnya.

### Hari 3 — Senin, 30 November 2026
**Fokus:** audit dan penyelesaian kelompok komponen navigasi/layout.

Pekerjaan:
1. Audit header, logo, hamburger, expandable sidebar, overlay navigation, bottom navigation, footer, go-to-top.
2. Periksa responsive header/sidebar/bottom navigation.
3. Implementasikan gap yang memang termasuk requirement dan belum ada.
4. Uji navigasi, active state, expand/collapse, keyboard, overflow, dan viewport.

Hasil wajib:
- Test case komponen navigasi/layout diperbarui dengan actual result.
- Evidence untuk kasus yang diuji.
- Tidak ada regresi pada hero carousel dan tema.

### Hari 4 — Selasa, 1 Desember 2026
**Fokus:** kelompok hero, carousel, CTA, event, winner table, highlights.

Pekerjaan:
1. Audit hero banner, image carousel/slider, indicators, CTA, What's On, event card, winner table, horizontal carousel, highlights, category card.
2. Uji next/previous/indicator/swipe/drag/keyboard pada carousel yang relevan.
3. Uji horizontal scrolling dan tabel pada viewport kecil.
4. Perbaiki hanya gap yang masuk scope.

Hasil wajib:
- Test case kelompok konten/hero memiliki hasil aktual.
- Carousel yang sudah lulus tetap lulus regression.

### Hari 5 — Rabu, 2 Desember 2026
**Fokus:** kelompok diskusi dan komentar.

Pekerjaan:
1. Audit latest discussions, discussion card, comment input/thread, nested comments, like button, comment/view counter.
2. Uji reply dan nested reply, validasi input, like state, counter, scroll container.
3. Pastikan state UI tidak sekadar dekorasi bila requirement meminta interaksi.
4. Tambahkan unit/integration test yang layak untuk logic komponen.

Hasil wajib:
- Alur komentar/like yang masuk scope bekerja dan dibuktikan.
- Matriks diperbarui; bug yang belum selesai tercatat.

## Minggu 2 — Frontend lanjutan dan desain CMS

### Hari 6 — Kamis, 3 Desember 2026
**Fokus:** kelompok reels, video, gallery, masonry, infinite scroll.

Pekerjaan:
1. Audit reels section/video card/play button/gallery/masonry/infinite scroll.
2. Uji loading, empty state, akhir daftar, viewer, scroll, dan tata letak.
3. Pastikan aset lokal; tidak menambahkan aset eksternal.
4. Uji error/asset hilang secara terkendali bila skenario masuk matriks.

Hasil wajib:
- Alur gallery dan konten media dapat diuji.
- Infinite scroll memiliki perilaku loading/end yang jelas jika termasuk implementasi.

### Hari 7 — Jumat, 4 Desember 2026
**Fokus:** kelompok interaksi umum, konten, dan responsive.

Pekerjaan:
1. Audit hover, tooltip, expand/collapse, scrollable containers, modal/popup, floating button, loading indicator.
2. Audit category label, article card, thumbnail, content grid, pagination, load more, image viewer.
3. Uji keyboard, Escape, overlay, focus, tooltip placement, pagination/load more.
4. Audit responsive grid/card/table/carousel/gallery.

Hasil wajib:
- Test case komponen umum dan responsive diperbarui.
- Daftar defect frontend yang tersisa diprioritaskan.

### Hari 8 — Senin, 7 Desember 2026
**Fokus:** frontend regression dan penyelesaian defect prioritas.

Pekerjaan:
1. Jalankan seluruh test frontend yang sudah tersedia.
2. Jalankan pemeriksaan manual desktop/tablet/mobile dan tema gelap/terang.
3. Perbaiki defect blocker/major yang ditemukan.
4. Tambahkan test otomatis untuk logic yang stabil.
5. Review seluruh 56 kategori: implemented, partial, not implemented, atau out of scope (dengan alasan).

Hasil wajib:
- Frontend baseline dan daftar gap terukur.
- Tidak menyatakan seluruh frontend selesai jika masih ada requirement yang belum terpenuhi.

### Hari 9 — Selasa, 8 Desember 2026
**Fokus:** audit arsitektur CMS dan keputusan desain.

Pekerjaan:
1. Audit server Playground dan struktur Python yang ada.
2. Audit dependensi dan modul AI QA Assistant yang dapat digunakan kembali.
3. Tentukan model data CMS, route, autentikasi, penyimpanan media, dan hubungan konten ke frontend.
4. Evaluasi Python + SQLite sebagai opsi ringan; jangan menambah framework sebelum alasan dan dampaknya jelas.
5. Tentukan lokasi data CMS lokal dan mekanisme seed/reset yang tidak menyentuh data klien.

Hasil wajib:
- Dokumen desain CMS ringkas dan keputusan arsitektur beserta alasannya.
- Daftar file/dependensi yang akan berubah.
- Backup plan sebelum implementasi.

### Hari 10 — Rabu, 9 Desember 2026
**Fokus:** fondasi CMS, database, konfigurasi, dan autentikasi.

Pekerjaan:
1. Implementasikan struktur backend/database sesuai desain yang disetujui.
2. Buat schema/migrasi atau inisialisasi database yang dapat diulang dengan aman.
3. Implementasikan login/logout dan session.
4. Password harus di-hash; jangan log kredensial.
5. Terapkan proteksi route dan otorisasi di sisi server.
6. Tambahkan unit dan integration test dasar.

Hasil wajib:
- Database dapat dibuat/diinisialisasi ulang sesuai prosedur.
- Login valid/invalid, logout, proteksi route, dan session diuji.
- Server hanya bind `127.0.0.1`.

## Minggu 3 — CMS fungsional

### Hari 11 — Kamis, 10 Desember 2026
**Fokus:** CMS dashboard dan artikel.

Pekerjaan:
1. Dashboard memakai data database aktual.
2. Implementasikan artikel create/read/update/delete.
3. Implementasikan draft/publish dan validasi input.
4. Pastikan data tetap ada setelah server restart.
5. Tambahkan unit/integration test.

Hasil wajib:
- CRUD artikel dan status publikasi lulus test yang disepakati.
- Dashboard menangani data kosong dan error.

### Hari 12 — Jumat, 11 Desember 2026
**Fokus:** event, komentar, dan moderasi.

Pekerjaan:
1. Implementasikan CRUD event dan validasi tanggal/status.
2. Implementasikan daftar komentar, moderasi, balasan/status sesuai scope.
3. Pastikan input divalidasi di server.
4. Uji role yang diizinkan dan ditolak.
5. Tambahkan integration test.

Hasil wajib:
- Event dan komentar dapat dikelola dari CMS.
- Perubahan status tercermin di data dan UI.

### Hari 13 — Senin, 14 Desember 2026
**Fokus:** media, galeri, upload aman.

Pekerjaan:
1. Implementasikan upload media ke lokasi data yang ditentukan.
2. Batasi tipe dan ukuran file.
3. Cegah path traversal, overwrite file arbitrer, dan nama file berbahaya.
4. Implementasikan preview dan penanganan file invalid.
5. Tambahkan test untuk upload valid/invalid.

Hasil wajib:
- Upload yang valid berhasil.
- File invalid ditolak dengan aman.
- File disimpan di lokasi yang tidak tercampur dengan source repository.

### Hari 14 — Selasa, 15 Desember 2026
**Fokus:** pengguna, role, pengaturan, pencarian, pagination.

Pekerjaan:
1. Implementasikan role minimal admin/editor.
2. Verifikasi otorisasi di server untuk setiap aksi penting.
3. Implementasikan pengaturan yang tersimpan.
4. Implementasikan search/filter/pagination sesuai scope.
5. Uji empty state, batas input, akses ditolak, dan data invalid.

Hasil wajib:
- Role dan permission diuji.
- Search/filter/pagination memberikan hasil konsisten.

### Hari 15 — Rabu, 16 Desember 2026
**Fokus:** integrasi CMS dengan frontend dan CMS E2E.

Pekerjaan:
1. Hubungkan konten publish dari CMS ke frontend lokal.
2. Uji draft tidak tampil sebagai konten publik.
3. Uji edit/publish/unpublish dan konsistensi data.
4. Siapkan seed/reset dataset.
5. Buat E2E alur login → edit artikel → publish → lihat frontend.
6. Buat E2E alur akses ditolak untuk role yang tidak berwenang.

Hasil wajib:
- Alur CMS ke frontend dapat diulang.
- Dataset dapat di-reset tanpa menyentuh data klien.
- CMS memiliki unit/integration/E2E test dasar.

## Minggu 4 — Ground truth dan integrasi scanner

### Hari 16 — Kamis, 17 Desember 2026
**Fokus:** Ground Truth design dan baseline sehat.

Pekerjaan:
1. Tentukan katalog bug, ID, severity, lokasi, langkah reproduksi, expected result.
2. Buat dataset baseline tanpa bug.
3. Buat mekanisme seed/reset terkontrol.
4. Pisahkan ground truth dari data yang terlihat oleh scanner.
5. Tentukan format evaluasi temuan dan evidence.

Hasil wajib:
- Ground truth versi awal terdokumentasi.
- Baseline sehat dapat di-reset dan diverifikasi.

### Hari 17 — Jumat, 18 Desember 2026
**Fokus:** seeded bug frontend dan CMS.

Pekerjaan:
1. Tambahkan skenario frontend: broken image/link, accessible name/label, dan validasi/interaksi sesuai scope.
2. Tambahkan skenario CMS: role/access, validasi, publikasi, dan upload invalid sesuai scope.
3. Pastikan bug hanya berada pada Playground lokal.
4. Verifikasi setiap seeded bug benar-benar ada dan dapat direproduksi.
5. Pastikan reset mengembalikan baseline sehat.

Hasil wajib:
- Seeded bug memiliki bukti aktual.
- Ground truth tidak mencemari source data produksi/klien.

### Hari 18 — Senin, 21 Desember 2026
**Fokus:** audit scanner dan rancangan integrasi frontend/CMS.

Pekerjaan:
1. Audit scanner, config, request guard, rate limit, 403 stop, authorization, evidence, report.
2. Identifikasi alur autentikasi CMS yang sah dan aman untuk scanner.
3. Tentukan batas origin, session, dan halaman yang boleh dipindai.
4. Reuse modul yang tersedia; jangan membuat ulang progress/logging/evidence/security.
5. Buat integration test plan.

Hasil wajib:
- Desain integrasi scanner disetujui sebelum perubahan kode.
- Tidak ada asumsi API modul tanpa inspeksi source/test.

### Hari 19 — Selasa, 22 Desember 2026
**Fokus:** integrasi scanner ke frontend Playground.

Pekerjaan:
1. Konfigurasikan MyDreamZone frontend sebagai target lokal.
2. Jalankan page inspection dan kemampuan scanner yang sudah ada.
3. Uji navigasi internal sesuai batas request.
4. Uji evidence dan laporan.
5. Uji request guard, redirect, rate limit, dan 403 threshold.

Hasil wajib:
- Scanner dapat menguji frontend lokal dengan evidence aktual.
- Kebijakan keamanan tetap berlaku.

### Hari 20 — Rabu, 23 Desember 2026
**Fokus:** integrasi scanner CMS authenticated.

Pekerjaan:
1. Implementasikan alur autentikasi scanner menggunakan akun uji lokal yang sah.
2. Jangan menulis password/token/cookie ke log, report, atau checkpoint.
3. Uji halaman CMS yang diizinkan.
4. Uji session expired, akses ditolak, logout, dan 403 threshold.
5. Pastikan evidence terhubung ke project yang benar.

Hasil wajib:
- Scanner mengakses hanya halaman CMS yang diizinkan.
- Session dan kredensial ditangani secara aman.
- Akses yang ditolak dilaporkan secara benar.

## Minggu 5 — Kemampuan scanner, regression, installer, release

### Hari 21 — Kamis, 24 Desember 2026
**Fokus:** scanner capability gap dan ground truth evaluation.

Pekerjaan:
1. Uji broken links/images.
2. Uji responsive/theme inspection yang tersedia atau implementasikan gap prioritas.
3. Evaluasi temuan scanner terhadap ground truth.
4. Hitung true positive, false positive, false negative; precision/recall jika sampel memadai.
5. Catat batasan dan temuan yang belum dapat dideteksi.

Hasil wajib:
- Laporan evaluasi scanner dengan data aktual.
- Tidak mengklaim akurasi tanpa dataset dan perhitungan.

### Hari 22 — Senin, 28 Desember 2026
**Fokus:** functional interaction testing dan visual regression scope.

Pekerjaan:
1. Audit apakah interaksi aman dapat diuji otomatis.
2. Implementasikan skenario interaksi yang sudah disepakati dan tidak destruktif.
3. Evaluasi visual regression baseline dan threshold bila masuk scope.
4. Uji false alarm antar-viewport/theme.
5. Tambahkan regression test untuk bug yang sudah diperbaiki.

Hasil wajib:
- Status tiap kemampuan scanner jelas: Pass/Partial/Not implemented.
- Tidak ada aksi destruktif tanpa izin eksplisit.

### Hari 23 — Selasa, 29 Desember 2026
**Fokus:** regression automation dan installer integration.

Pekerjaan:
1. Kelompokkan unit, integration, E2E, security, regression tests.
2. Buat entry point/perintah regression terdokumentasi.
3. Pastikan test stabil dijalankan otomatis.
4. Integrasikan Playground/CMS/assets ke installer.
5. Pastikan server tidak auto-run dan hanya bind localhost.
6. Pastikan DataRoot tetap eksternal.

Hasil wajib:
- Perintah regression terdokumentasi dan hasilnya dapat diulang.
- Installer memuat komponen yang disetujui tanpa membawa data runtime/secret.

### Hari 24 — Rabu, 30 Desember 2026
**Fokus:** dokumentasi, fresh clone, portability, backup/restore.

Pekerjaan:
1. Perbarui installation/setup guide, user guide, troubleshooting, changelog.
2. Uji fresh clone pada folder terpisah.
3. Buat environment baru; jangan menyalin venv.
4. Jalankan installer dan regression.
5. Uji backup/restore data sesuai kemampuan aplikasi yang tersedia.
6. Verifikasi tidak ada kehilangan data, log, evidence, laporan, atau proyek.

Hasil wajib:
- Fresh clone berhasil atau kegagalan terdokumentasi dengan diagnosis.
- Dokumentasi sesuai perilaku aktual.

### Hari 25 — Kamis, 31 Desember 2026
**Fokus:** final release gate dan keputusan Go/No-Go.

Pekerjaan:
1. Jalankan full unit test.
2. Jalankan full integration test.
3. Jalankan E2E frontend dan CMS.
4. Jalankan regression suite.
5. Periksa security: localhost binding, request guard, 403 stop, auth, isolasi data, secret logging.
6. Periksa Git diff/staged list.
7. Periksa semua requirement dan evidence.
8. Catat known issues dan keputusan Go/No-Go.
9. Buat checkpoint akhir dan backup.

Hasil wajib:
- Release checklist terisi dengan bukti.
- Tidak ada blocker/critical issue yang belum ditangani atau diterima secara eksplisit.
- Jika belum memenuhi, gunakan buffer; jangan memaksakan status selesai.

---

# Buffer / contingency — 5 hari kerja

Hari buffer bukan scope tambahan. Gunakan hanya untuk menyelesaikan hambatan, perbaikan regression, atau pekerjaan yang bergeser.

| Hari | Tanggal | Penggunaan |
|---|---|---|
| B1 | Senin, 4 Januari 2027 | Perbaikan blocker/major yang tertunda |
| B2 | Selasa, 5 Januari 2027 | Perbaikan integrasi CMS/scanner dan retest |
| B3 | Rabu, 6 Januari 2027 | Perbaikan E2E/regression flaky dan retest |
| B4 | Kamis, 7 Januari 2027 | Fresh clone/installer/backup-restore ulang |
| B5 | Jumat, 8 Januari 2027 | Final audit, dokumentasi, checkpoint, Go/No-Go |

Jika seluruh pekerjaan selesai sebelum buffer, gunakan waktu tersisa untuk review dan stabilisasi. Jangan otomatis menambahkan fitur baru.

---

## Batasan harian wajib

Satu hari dianggap selesai jika:
1. Deliverable hari tersebut tersedia.
2. Acceptance criteria hari tersebut diperiksa.
3. Test yang relevan dijalankan dan hasil aktual dicatat.
4. Evidence tersedia untuk klaim yang membutuhkan bukti.
5. Matriks requirement diperbarui.
6. Tidak ada perubahan tak terencana yang belum dicatat.
7. Checkpoint harian mencatat pekerjaan selesai, belum selesai, risiko, dan langkah berikutnya.

Jika tidak selesai:
- Catat apa yang belum selesai dan penyebabnya.
- Jangan tandai Pass.
- Geser milestone berikutnya berdasarkan dependency.
- Gunakan buffer sebelum mengurangi test atau acceptance criteria.

## Status jadwal

- **Belum dimulai:** seluruh tanggal merupakan rencana.
- **Berjalan:** pekerjaan hari tersebut sedang dilakukan.
- **Selesai:** seluruh deliverable dan acceptance criteria diverifikasi.
- **Tertunda:** ada hambatan; alasan dan dampak tanggal dicatat.

## Catatan scope

Jadwal ini mengikuti Master Project Roadmap & Acceptance Criteria versi 1.0. Git Manager UI tetap ditunda. Tidak ada fitur baru yang ditambahkan di luar scope yang disetujui. Jika audit menemukan kebutuhan perubahan arsitektur atau scope, dokumentasikan dampak waktu dan minta persetujuan sebelum mengubah rencana.
