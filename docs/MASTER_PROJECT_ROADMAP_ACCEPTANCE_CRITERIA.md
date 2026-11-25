# Master Project Roadmap & Acceptance Criteria
## AI QA Assistant + Built-in QA Playground (MyDreamZone)

**Versi:** 1.0
**Tanggal:** 25 November 2026
**Status:** Baseline perencanaan — belum seluruh item diverifikasi
**Jam kerja rencana:** Senin–Jumat, 8–12 jam per hari (40–60 jam per minggu); Sabtu dan Minggu libur.

---

## 1. Tujuan proyek

Menyelesaikan AI QA Assistant sebagai aplikasi QA lokal/portabel yang dapat membantu QA Engineer menguji website frontend dan CMS, mengumpulkan evidence yang dapat ditelusuri, mencatat temuan berdasarkan bukti, serta menghasilkan laporan QA.

MyDreamZone menjadi **Built-in QA Playground** resmi untuk menguji kemampuan scanner pada dua target lokal:
1. Frontend website MyDreamZone.
2. CMS MyDreamZone yang benar-benar berfungsi dan menggunakan data lokal.

Git Manager saat ini dipertahankan. Penyempurnaan UI Git Manager ditunda sampai aplikasi utama selesai.

## 2. Prinsip dan batasan

- Kerjakan satu checkpoint yang terukur pada satu waktu.
- Jangan mengklaim fitur atau test lulus tanpa bukti aktual.
- Sebelum perubahan besar, buat backup eksternal dan verifikasi backup.
- Script sekali pakai berada di luar repository; setelah dipakai arsipkan ke `AI-QA-Assistant_OLD\one_time_scripts\`.
- Repository root hanya berisi source code, test permanen, konfigurasi, dan dokumentasi yang diperlukan.
- Data klien, evidence, laporan, log, kredensial, backup, dan virtual environment tidak boleh ikut Git kecuali ada kebutuhan yang disetujui secara eksplisit.
- Gunakan kembali modul progress, logging, evidence, keamanan, request guard, dan data path yang sudah ada.
- Jangan menambah dependensi tanpa alasan dan keputusan yang jelas.
- Setiap laptop membuat virtual environment sendiri; jangan memindahkan venv antarperangkat.
- Playground/CMS lokal bind ke `127.0.0.1` secara default dan tidak berjalan otomatis saat aplikasi dibuka.
- Tidak melakukan bypass CAPTCHA, Cloudflare, WAF, autentikasi, atau kontrol keamanan target.
- Hentikan pemindaian setelah batas 403 yang dikonfigurasi tercapai.
- Pisahkan data tiap klien dan jangan mencatat password, token, atau cookie.

## 3. Metode pengembangan dan verifikasi

Setiap requirement mengikuti siklus:

1. Requirement dan ruang lingkup.
2. Acceptance criteria yang dapat diuji.
3. Pemeriksaan kondisi awal dan dependensi.
4. Backup jika ada perubahan berisiko.
5. Implementasi.
6. Unit test.
7. Integration test.
8. End-to-end test bila alur pengguna/browser relevan.
9. Pemeriksaan manual dan evidence.
10. Regression test yang relevan.
11. Dokumentasi, matriks status, dan checkpoint.
12. Keputusan Go/No-Go.

### Tiga tingkat pengujian wajib

| Jenis | Tujuan | Contoh untuk proyek |
|---|---|---|
| Unit test | Menguji satu fungsi/modul secara terisolasi | Parser konfigurasi, validasi URL, klasifikasi status, sanitasi log, aturan severity |
| Integration test | Menguji kerja sama beberapa komponen | Scanner + PlaywrightRequestGuard + RequestSafetyController; CMS + database; evidence manager + report manager |
| End-to-end test (E2E) | Menguji alur pengguna dari awal sampai akhir | Buka website lokal, login CMS, edit/publish konten, jalankan scanner, lihat evidence dan laporan |

Ketentuan:
- Unit test dan integration test dijalankan otomatis sejauh layak.
- E2E dijalankan otomatis untuk alur stabil yang dapat diulang; pemeriksaan visual/responsive tertentu tetap dapat memerlukan verifikasi manual.
- Test harus memeriksa hasil yang diharapkan, bukan hanya bahwa program tidak crash.
- Simpan hasil test dan evidence tanpa membocorkan kredensial.
- Regression suite harus dapat dijalankan dengan satu perintah atau entry point terdokumentasi.

## 4. Estimasi waktu berdasarkan jam kerja baru

Ketersediaan pengguna: **8–12 jam per hari, Senin–Jumat = 40–60 jam per minggu**.

Estimasi sebelumnya 23–38 hari kerja mengasumsikan sekitar 4–6 jam fokus per hari. Dengan asumsi effort yang sama, estimasi matematis menjadi sekitar 92–228 jam. Setelah memperhitungkan ketidakpastian, integrasi, diagnosis, dan buffer 20–30%, gunakan rentang perencanaan **120–295 jam**.

| Kapasitas | Perkiraan kalender kerja untuk 120–295 jam |
|---|---:|
| 8 jam/hari, 5 hari/minggu | 3–7,5 minggu |
| 10 jam/hari, 5 hari/minggu | 2,5–6 minggu |
| 12 jam/hari, 5 hari/minggu | 2–5 minggu |

**Target perencanaan yang disarankan: 4–7 minggu kerja.** Rentang ini lebih realistis daripada menjanjikan tanggal pasti. Jika scope CMS membesar, scanner menemukan masalah arsitektur, atau integrasi membutuhkan redesign, jadwal dapat bertambah.

Jam kerja panjang tidak berarti seluruh jam merupakan waktu coding efektif. Sisihkan waktu untuk review, test, dokumentasi, istirahat, dan diagnosis. Jangan mengorbankan verifikasi demi mengejar tanggal.

## 5. Roadmap utama dan acceptance criteria

Status yang digunakan:
- **Selesai**: ada bukti implementasi dan verifikasi yang tercatat.
- **Berjalan**: sudah dikerjakan sebagian.
- **Belum**: belum ada bukti penyelesaian.
- **Tertunda**: sengaja tidak diprioritaskan saat ini.

Persentase tidak boleh ditentukan hanya dari jumlah file atau tampilan. Persentase proyek dihitung setelah bobot requirement disepakati dan status didukung evidence.

### Fase A — Frontend MyDreamZone Playground

**Tujuan:** menyelesaikan target frontend lokal yang dapat digunakan untuk menguji komponen dan interaksi nyata.

| ID | Requirement / hasil yang diharapkan | Acceptance criteria | Status |
|---|---|---|---|
| A1 | Struktur, tema, layout responsif | Desktop/tablet/mobile diperiksa; tidak ada overflow kritis; tema terang/gelap berfungsi | Selesai sebagian; LP-3.1–3.3.3 |
| A2 | Hero carousel | Next/Previous, indikator, swipe/drag, keyboard, tema dan responsive bekerja | Lulus berdasarkan 8 pemeriksaan manual pengguna (LP-3.4.1) |
| A3 | Seluruh 56 kategori komponen | Tiap kategori punya requirement, implementasi nyata atau keputusan scope, dan test case | Belum; jangan klaim seluruh 56 selesai |
| A4 | Interaksi komponen | Setiap interaksi punya positive, negative/boundary case yang relevan | Belum |
| A5 | Aksesibilitas dasar | Navigasi keyboard, label, fokus, semantic markup dan kontras dasar diperiksa | Belum menyeluruh |
| A6 | Frontend test suite | Unit/integration/E2E relevan terdokumentasi dan dapat diulang | Belum |

Catatan: 56 kategori komponen tetap mengikuti daftar yang sudah disepakati dalam checkpoint proyek. Matriks test case harus memetakan setiap kategori ke satu atau lebih skenario.

### Fase B — CMS MyDreamZone lokal

**Tujuan:** membangun CMS kecil namun fungsional untuk menjadi target pengujian CMS lokal, bukan sekadar dashboard statis.

**Arah arsitektur awal:** pertimbangkan Python backend + SQLite agar ringan dan lokal. Ini masih keputusan desain yang harus dikonfirmasi setelah inspeksi struktur source, dependensi, dan pola server yang sudah ada. Jangan langsung menambahkan framework/dependensi sebelum audit.

| ID | Modul | Acceptance criteria minimum | Status |
|---|---|---|---|
| B1 | Login/logout dan sesi | Login valid/invalid, logout, proteksi route, sesi berakhir diuji | Belum |
| B2 | Dashboard | Data ringkasan berasal dari database; kondisi kosong/error ditangani | Belum |
| B3 | Artikel | Create/read/update/delete, draft/publish, validasi input, data persisten | Belum |
| B4 | Event | CRUD, validasi tanggal/status, data persisten | Belum |
| B5 | Galeri/media | Upload lokal, tipe/ukuran dibatasi, preview, file invalid ditolak | Belum |
| B6 | Komentar | Daftar, moderasi, balasan/status dan validasi | Belum |
| B7 | Pengguna dan role | Role minimal admin/editor; akses diuji di sisi server | Belum |
| B8 | Pengaturan | Pengaturan tersimpan dan tervalidasi | Belum |
| B9 | Search/filter/pagination | Hasil konsisten, empty state, batas input diuji | Belum |
| B10 | Integrasi frontend | Konten yang dipublikasikan CMS tampil sesuai aturan di frontend lokal | Belum |
| B11 | Reset/seed data uji | Dataset dapat diinisialisasi ulang tanpa menyentuh data klien | Belum |
| B12 | CMS test suite | Unit, integration, dan E2E untuk alur CMS tersedia | Belum |

Persyaratan keamanan CMS:
- Tidak menggunakan kredensial produksi.
- Sediakan akun/dataset dummy lokal.
- Password disimpan dengan hashing yang sesuai, tidak plaintext.
- Validasi dan otorisasi dilakukan di server, bukan hanya menyembunyikan tombol UI.
- Upload disimpan di lokasi data yang aman, tidak dapat menimpa file arbitrer.
- Default bind `127.0.0.1`; tidak ada akses publik.
- Jangan membuat fitur bypass autentikasi atau mekanisme keamanan.

### Fase C — Bug simulation dan Ground Truth

**Tujuan:** membuat dataset kondisi baik dan buruk yang hasil sebenarnya telah diketahui sehingga kualitas scanner dapat diukur.

Acceptance criteria:
- Setiap seeded bug mempunyai ID, deskripsi, lokasi, expected result, severity yang diharapkan, dan langkah reproduksi.
- Bug hanya disisipkan pada lingkungan Playground lokal.
- Ada dataset baseline tanpa bug.
- Ada dataset seeded bug yang dapat di-reset.
- Ground truth tidak disajikan kepada scanner selama pengujian blind.
- Hasil scanner dibandingkan dengan ground truth.
- Hitung true positive, false positive, false negative, dan precision/recall bila datanya memadai.
- Evidence yang dihasilkan scanner harus benar-benar menunjuk kondisi yang ditemukan.

Contoh skenario: broken image, broken internal link, tombol tanpa accessible name, input tanpa label, validasi form bermasalah, role tidak sesuai, akses route tanpa izin, dan alur publikasi yang gagal.

Status: **Belum**.

### Fase D — Integrasi scanner frontend dan CMS

Acceptance criteria:
- Project config dapat memilih target frontend dan CMS dengan jelas.
- CMS authenticated scanning hanya menggunakan akun uji yang sah dan izin eksplisit.
- Login/session dikelola aman; password/token/cookie tidak dicatat ke log atau laporan.
- Request guard, rate limit, origin allowlist, dan penghentian 403 tetap berlaku.
- Redirect dan request lintas origin tetap mengikuti kebijakan keamanan.
- Scanner dapat membedakan access restricted, failed, passed, dan status lain secara konsisten.
- Evidence dan laporan terhubung ke project/client yang benar.
- Data antar proyek/klien terisolasi.
- Uji skenario sukses, gagal, session expired, akses ditolak, dan batas 403.

Status: **Belum terintegrasi**.

### Fase E — Penyempurnaan kemampuan scanner

Daftar kemampuan dan acceptance criteria:

| Kemampuan | Kriteria selesai |
|---|---|
| Page inspection | Elemen halaman dan statusnya dikumpulkan secara konsisten |
| Broken links | Link internal diperiksa dengan batas request dan hasil dapat direproduksi |
| Broken images | Gambar rusak/response gagal terdeteksi dan evidence tersedia |
| Responsive inspection | Viewport yang disepakati diperiksa dan overflow/layout issue dicatat dengan bukti |
| Theme inspection | Tema yang tersedia diperiksa dan state tema tercatat |
| Visual regression | Baseline, screenshot pembanding, threshold dan false alarm dievaluasi |
| Functional interaction testing | Interaksi yang diizinkan diuji dengan skenario eksplisit; tindakan destruktif tidak dilakukan tanpa izin |
| CMS inspection | Halaman dan alur CMS yang diizinkan diperiksa dengan autentikasi yang aman |

Status: sebagian telah tersedia; tiap kemampuan harus diaudit terhadap kode dan test sebelum dinyatakan selesai.

### Fase F — Installer, portability, dan dokumentasi

Acceptance criteria:
- Installer memasang aplikasi, Playground, CMS, aset, dan dependency sesuai desain.
- Server Playground/CMS tidak berjalan otomatis saat aplikasi dibuka.
- Default bind lokal `127.0.0.1`.
- DataRoot eksternal tetap terpisah dari source code.
- Update tidak menghapus data proyek, evidence, laporan, atau log.
- Environment dibuat per perangkat; venv tidak disalin antar laptop.
- Fresh clone dan instalasi bersih berhasil.
- Panduan instalasi, konfigurasi, penggunaan, troubleshooting, backup/restore, dan changelog diperbarui.
- Tidak ada data klien, secret, log, evidence, atau backup di paket source tanpa izin/kebutuhan.

Status: installer aplikasi utama telah diuji pada fresh clone sebelumnya; integrasi Playground/CMS dan validasi rilis akhir belum selesai.

### Fase G — Release validation

Acceptance criteria:
- Jalankan seluruh unit test.
- Jalankan seluruh integration test.
- Jalankan E2E suite untuk frontend dan CMS.
- Jalankan regression suite penuh.
- Verifikasi instalasi pada fresh clone/folder bersih.
- Verifikasi server hanya bind ke localhost.
- Verifikasi data dan evidence berada di DataRoot yang benar.
- Verifikasi backup/restore dan tidak ada kehilangan data.
- Periksa Git diff dan staged file sebelum commit/push.
- Catat known issues dan keputusan release.
- Tidak ada blocker/critical issue yang belum ditangani atau diterima secara eksplisit.

Status: belum untuk keseluruhan rilis Playground + CMS.

### Fase H — Git Manager UI

**Tertunda, bukan dibatalkan.** Git Manager saat ini sudah berfungsi dan tidak menjadi prioritas. Penyempurnaan menu/flow Push Backup dan Pull Restore baru dilakukan setelah aplikasi utama dan release validation selesai, sesuai checkpoint sebelumnya.

## 6. Matriks Requirement & Test Case

Buat satu matriks yang menjadi sumber status resmi. Simpan sebagai dokumen permanen di `docs/` (format awal Markdown atau CSV; jangan menambah tool/dependensi tanpa kebutuhan).

Kolom minimum:
- Requirement ID
- Area / modul
- Requirement
- Test Case ID
- Preconditions
- Test steps
- Expected result
- Test level (Unit / Integration / E2E / Manual)
- Actual result
- Status (Not Run / Pass / Fail / Blocked / N/A)
- Evidence reference
- Bug ID
- Severity
- Owner/notes
- Last verified date

Aturan:
- Satu requirement dapat memiliki banyak test case.
- `Pass` hanya setelah hasil aktual diperiksa.
- `Blocked` berbeda dari `Fail`.
- `N/A` harus disertai alasan.
- Evidence reference menunjuk lokasi yang benar, bukan nama file tebakan.
- Jangan memasukkan secret atau data sensitif ke matriks.
- Matriks diperbarui pada setiap checkpoint yang mengubah status.

## 7. Otomatisasi regression

- Identifikasi test yang stabil dan deterministik.
- Kelompokkan test: unit, integration, E2E, security, regression.
- Buat satu entry point terdokumentasi untuk menjalankan suite yang sesuai.
- E2E dapat dipisah dari unit test agar feedback cepat.
- Simpan output test dengan identitas commit/build.
- Jika test gagal, hentikan klaim Go; diagnosis dahulu.
- Jangan menghapus atau melemahkan test yang gagal hanya untuk membuat suite hijau.
- Catat test yang di-skip beserta alasan.
- Regression baseline yang pernah diverifikasi: fresh clone pada commit `7fe5253` menjalankan 280 tests, `OK (skipped=3)` (277 lulus, 3 skipped, 0 failure/error). Hasil ini adalah baseline historis, bukan bukti status source terbaru.

## 8. Skrip perubahan yang aman

Setiap script installer/patch harus:
1. Memastikan root project benar.
2. Memastikan file input ada dan pola/versi sumber cocok.
3. Menolak melanjutkan jika kondisi awal tidak sesuai.
4. Membuat backup eksternal sebelum menulis.
5. Menulis secara terkontrol.
6. Memvalidasi hasil (file, sintaks, test, checksum bila relevan).
7. Menyediakan rollback atau instruksi pemulihan.
8. Menampilkan hasil PASS/FAIL yang jujur.
9. Tidak menaruh script sementara di root repository.
10. Idempotent bila memang aman untuk dibuat idempotent.

## 9. Reuse modul dan batas arsitektur

Sebelum membuat modul baru, audit apakah kebutuhan dapat dipenuhi modul yang sudah ada, terutama:
- `core.progress_tracking`
- `core.logger`
- `core.evidence_manager`
- `core.data_paths`
- `core.path_safety`
- `core.request_safety`
- `core.playwright_request_guard`
- `core.authorization_manager`
- `core.result_status`
- `core.report_manager`

Jangan mengasumsikan API modul tanpa memeriksa implementasi dan test terkini. Jika reuse tidak layak, dokumentasikan alasan sebelum menambah abstraksi/dependensi.

## 10. Urutan prioritas dan dependency

Urutan kerja yang direkomendasikan:
1. Selesaikan audit requirement dan matriks test frontend.
2. Selesaikan komponen/interaksi frontend per kelompok.
3. Audit arsitektur server lokal yang ada.
4. Finalisasi desain CMS dan database setelah audit.
5. Bangun modul CMS secara bertahap dan uji tiap modul.
6. Integrasikan CMS dengan frontend dan data lokal.
7. Buat baseline dan seeded bug/ground truth.
8. Integrasikan scanner untuk frontend dan CMS.
9. Lengkapi kemampuan scanner yang masuk scope rilis.
10. Otomatiskan regression test.
11. Integrasikan Playground/CMS ke installer dan dokumentasi.
12. Regression, fresh clone, backup/restore, release validation.
13. Setelah itu baru pertimbangkan penyempurnaan Git Manager UI.

## 11. Pengukuran kemajuan

Jangan memakai angka persentase perkiraan tanpa bobot yang disepakati. Gunakan:
- jumlah requirement yang disetujui;
- jumlah requirement dengan implementasi terverifikasi;
- jumlah test case Pass/Fail/Blocked/Not Run;
- severity dan jumlah defect terbuka;
- tingkat deteksi ground truth (precision/recall jika relevan);
- hasil regression dan fresh clone.

Persentase requirement dapat dihitung:
`requirements verified / total approved requirements × 100`
Namun angka ini tidak menggantikan kualitas test atau severity. Laporkan juga jumlah test case Pass dan defect blocker/critical yang masih terbuka.

## 12. Risiko dan buffer

Risiko utama:
- CMS scope membesar melampaui kebutuhan Playground.
- Arsitektur backend/database bertabrakan dengan struktur yang sudah ada.
- Authenticated scanning menambah kompleksitas session dan security.
- Visual regression menghasilkan false positive akibat perbedaan rendering.
- E2E browser tests lebih lambat/flaky dibanding unit tests.
- Installer/data separation menimbulkan masalah pada fresh clone.
- Perubahan satu komponen merusak fitur lama.

Mitigasi:
- CMS tetap minimal sesuai test coverage yang dibutuhkan.
- Audit sebelum menentukan framework/dependensi.
- Buat acceptance criteria sebelum implementasi.
- Gunakan fixture/seed data dan reset yang aman.
- Pisahkan unit/integration/E2E.
- Sisihkan buffer 20–30%.
- Jangan menggabungkan banyak milestone dalam satu patch besar.

## 13. Definition of Done proyek

Proyek dapat dinyatakan **selesai sesuai scope rilis** apabila:
1. Seluruh requirement yang disetujui memiliki status dan bukti.
2. Frontend Playground dan CMS lokal memenuhi acceptance criteria.
3. Scanner terintegrasi dan diuji pada kedua target.
4. Ground truth menunjukkan kemampuan deteksi terukur.
5. Unit, integration, dan E2E test berjalan dengan hasil tercatat.
6. Regression suite lulus atau seluruh pengecualian diketahui dan disetujui.
7. Evidence dan laporan dapat ditelusuri dan tidak mengandung secret.
8. Security, isolasi data, rate limit, 403 stop, dan localhost binding diverifikasi.
9. Installer, fresh clone, portability, backup/restore telah divalidasi.
10. Dokumentasi dan checkpoint terbaru tersedia.
11. Known issues dan keputusan release dicatat.

**Catatan:** “100% tanpa kendala” tidak dapat dijamin untuk software. Target yang dapat dibuktikan adalah seluruh scope yang disepakati telah selesai dan tervalidasi, dengan tidak ada blocker/critical issue yang belum diselesaikan atau diterima secara eksplisit.
