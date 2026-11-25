# AI QA Assistant — Checkpoint 25 November 2026
## Pembaruan perencanaan dan metode kerja

**Status:** Checkpoint perencanaan diperbarui. Belum ada perubahan source code aplikasi pada pembaruan ini.

## 1. Lingkungan dan aturan repository

- OS: Windows, PowerShell.
- Laptop aktif: laptop kantor.
- Root aplikasi: `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant`
- Arsip eksternal: `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant_OLD`
- Data eksternal: `C:\Users\RBZ-NB-0004\AI_QA_Assistant_Data`
- Python utama terakhir dilaporkan: 3.15.2.
- Jangan memindahkan virtual environment antarperangkat.
- Root repository harus bersih dari script sekali pakai, patch, generator, backup, data pengguna, evidence, laporan, log, secret, dan venv.
- Simpan backup di `_OLD` eksternal. Arsipkan script sekali pakai ke `_OLD\one_time_scripts`.
- Periksa staged file list sebelum commit/push.
- Satu checkpoint pada satu waktu; berikan perintah PowerShell siap salin dan tunggu output pengguna.
- Jangan menganggap perubahan atau test berhasil tanpa verifikasi.
- Backup sebelum perubahan besar; diagnosis error sebelum patch.
- Jangan bypass CAPTCHA, Cloudflare, WAF, atau kontrol keamanan.
- Hentikan scan setelah batas 403 yang dikonfigurasi.
- Pisahkan data tiap klien; jangan log password, token, atau cookie.

## 2. Tujuan proyek

Membangun AI QA Assistant untuk membantu QA Engineer menguji website frontend dan CMS, mengumpulkan evidence aktual, menemukan potensi bug berdasarkan bukti, dan menghasilkan laporan QA.

**MyDreamZone** adalah Built-in QA Playground resmi untuk pengujian lokal, terdiri dari:
1. Frontend website MyDreamZone.
2. CMS MyDreamZone lokal yang benar-benar berfungsi.

CMS lokal diperlukan agar kita dapat menguji alur frontend dan CMS secara konsisten tanpa bergantung pada website eksternal. CMS harus berupa target uji yang nyata, bukan dashboard statis.

Default server Playground/CMS:
- Bind ke `127.0.0.1`.
- Tidak diekspos ke jaringan publik.
- Tidak berjalan otomatis saat AI QA Assistant dibuka; server hanya dijalankan saat diminta.
- Gunakan data dummy lokal, bukan data/kredensial produksi.

## 3. Kapasitas waktu dan estimasi revisi

Pengguna menyediakan waktu **8–12 jam per hari, Senin sampai Jumat**, dan libur Sabtu/Minggu. Kapasitas teoritis: **40–60 jam per minggu**.

Estimasi lama 23–38 hari kerja didasarkan pada asumsi 4–6 jam fokus per hari. Dengan mengubah asumsi jam kerja, effort kasar yang tersirat adalah sekitar 92–228 jam. Setelah buffer 20–30% untuk integrasi, diagnosis, dan risiko, rentang perencanaan menjadi sekitar **120–295 jam**.

Perkiraan kalender:
- 8 jam/hari: sekitar 3–7,5 minggu.
- 10 jam/hari: sekitar 2,5–6 minggu.
- 12 jam/hari: sekitar 2–5 minggu.

**Target rencana: 4–7 minggu kerja.** Ini estimasi, bukan janji tanggal selesai. Scope CMS, kondisi source aktual, hasil audit, dan temuan integrasi dapat mengubah jadwal. Jam panjang tidak boleh menggantikan review, istirahat, pengujian, dan dokumentasi.

## 4. Master roadmap

Dokumen utama perencanaan dibuat terpisah:
`docs/MASTER_PROJECT_ROADMAP_ACCEPTANCE_CRITERIA.md`

Dokumen tersebut menjadi sumber status untuk:
- Master Project Roadmap & Acceptance Criteria.
- Estimasi dan ketergantungan milestone.
- CMS MyDreamZone.
- Tiga jenis pengujian.
- Matriks requirement dan test case.
- Regression automation.
- Skrip perubahan yang aman.
- Reuse modul.
- Definition of Done dan release validation.

Sebelum melanjutkan coding, tempatkan dokumen roadmap tersebut ke folder `docs` repository dan verifikasi isinya. Jangan menganggap file sudah masuk repository sampai `git status` membuktikannya.

## 5. Metode kerja baru — berlaku untuk seluruh milestone berikutnya

Setiap requirement/fitur harus melewati:
1. Definisi kebutuhan dan scope.
2. Acceptance criteria yang terukur.
3. Pemeriksaan kondisi awal, source, dan dependensi.
4. Backup eksternal bila perubahan berisiko.
5. Implementasi terbatas.
6. Unit test.
7. Integration test.
8. End-to-end test bila alur pengguna/browser relevan.
9. Pemeriksaan manual dan evidence.
10. Regression test relevan.
11. Update matriks requirement/test case, dokumentasi, dan checkpoint.
12. Keputusan Go/No-Go berdasarkan bukti.

### Tiga jenis pengujian wajib

- **Unit test:** menguji fungsi/modul secara terisolasi. Contoh: parsing konfigurasi, validasi URL, klasifikasi status, sanitasi log.
- **Integration test:** menguji kerja sama komponen. Contoh: scanner + PlaywrightRequestGuard + RequestSafetyController; CMS + database; evidence manager + report manager.
- **End-to-end test (E2E):** menguji alur pengguna dari awal sampai akhir. Contoh: buka frontend, login CMS, ubah/publish konten, jalankan scanner, periksa evidence dan laporan.

Unit/integration diotomatisasi sejauh layak. E2E diotomatisasi untuk alur stabil yang bisa diulang; aspek visual/responsive tertentu tetap memerlukan pemeriksaan manual. Test harus memeriksa expected result, bukan hanya aplikasi tidak crash.

## 6. Enam perbaikan efisiensi yang disepakati

1. **Satu dokumen roadmap utama.** Semua milestone, status, estimasi, dan dependency dicatat di Master Project Roadmap & Acceptance Criteria.
2. **Satu matriks requirement dan test case.** Setiap requirement dipetakan ke test case, expected/actual result, status, dan evidence.
3. **Otomatisasi regression test.** Test stabil dijalankan ulang otomatis agar tidak perlu diuji manual setiap kali.
4. **Skrip instalasi/perubahan yang aman.** Validasi awal, backup eksternal, perubahan, validasi akhir, dan rollback bila diperlukan.
5. **Reuse modul yang sudah ada.** Audit dan gunakan modul progress, logging, evidence, data path, path safety, request safety, authorization, result status, dan report sebelum membuat modul baru.
6. **Kerja berdasarkan dependency.** CMS dan alur data harus jelas sebelum scanner CMS divalidasi; ground truth harus tersedia sebelum kualitas deteksi diukur.

## 7. Prioritas dan scope freeze

Pengguna menyatakan tidak mengharapkan perubahan scope tambahan selain hal yang sudah tercatat dalam checkpoint dan roadmap. Terapkan **scope freeze**:
- Jangan menambahkan fitur baru atas inisiatif sendiri.
- Jangan melakukan redesign besar tanpa alasan yang ditemukan saat audit atau persetujuan pengguna.
- Perubahan yang diperlukan untuk memenuhi requirement yang telah disepakati tetap boleh diusulkan, tetapi jelaskan alasan, dampak, dan minta persetujuan bila mengubah scope/dependensi.
- Pertahankan fitur yang sudah berjalan.

Urutan prioritas:
1. Selesaikan Frontend MyDreamZone Playground (seluruh kategori/interaksi yang disepakati).
2. Audit struktur server lokal dan rancang CMS minimal yang fungsional.
3. Bangun CMS MyDreamZone dan integrasi data dengan frontend.
4. Buat seeded bug dan ground truth.
5. Integrasikan scanner untuk frontend dan CMS.
6. Lengkapi kemampuan scanner yang masuk scope rilis.
7. Otomatiskan unit, integration, E2E, dan regression test.
8. Integrasikan Playground/CMS ke installer dan dokumentasi.
9. Jalankan regression penuh, fresh clone, portability, backup/restore, dan release validation.
10. Baru pertimbangkan penyempurnaan UI Git Manager.

## 8. Status pekerjaan terakhir yang diketahui

### AI QA Assistant
- Modul Project Manager, logging/rotation, Sensitive Data Filter, scanner Playwright, External DataRoot, evidence/report, request safety, authorization, progress tracking, dan sejumlah workflow sudah tersedia.
- Baseline fresh clone historis: commit `7fe5253`; 280 test dijalankan, `OK (skipped=3)` — 277 lulus, 3 skipped, 0 failure/error.
- Angka tersebut adalah hasil historis dan bukan bukti status source terbaru.
- Broken images/links, responsive inspection, theme inspection, visual regression, functional interaction testing, integrasi CMS, backup/restore manager reusable, dan final release validation masih perlu diaudit/dilengkapi sesuai scope.
- CMS scanning kini menjadi kebutuhan resmi untuk diuji melalui CMS lokal MyDreamZone.

### MyDreamZone Frontend
- LP-3.1 struktur awal: selesai.
- LP-3.2 responsive layout: selesai berdasarkan pemeriksaan sebelumnya.
- LP-3.3 visual rebuild: dipasang dan ditinjau.
- LP-3.3.3 perbaikan posisi family hero: selesai berdasarkan screenshot pengguna.
- LP-3.4.1 Hero Carousel: lulus berdasarkan 8 pemeriksaan manual yang dilaporkan pengguna: slide awal, next, previous, 4 indikator, swipe/drag, keyboard arrows, dark/light theme, desktop/tablet/mobile.
- Belum ada klaim seluruh 56 kategori atau seluruh interaksi selesai.
- LP-3.4.2 berikutnya perlu diawali inspeksi implementasi yang ada; modal/popup pernah diusulkan sebagai kandidat, tetapi jangan langsung patch tanpa memeriksa source dan urutan requirement.

### Git
Status terakhir yang dilaporkan sebelumnya:
```text
?? docs/AI_QA_Assistant_CHECKPOINT_2026-11-25.md
?? local_test_site/playground/
?? local_test_site/playground_server.py
```
Status ini belum diperiksa ulang. Tidak ada commit/push Playground yang terverifikasi setelah output tersebut. Periksa `.gitignore`, allowlist, isi file, dan kebutuhan installer sebelum staging.
- Git Manager saat ini berfungsi dan bukan prioritas.
- Penyempurnaan UI Git Manager ditunda sampai aplikasi utama selesai.

## 9. CMS MyDreamZone — arahan awal, belum implementasi

CMS minimal yang perlu dievaluasi:
- Login/logout dan session.
- Dashboard dengan data aktual.
- Artikel: CRUD, draft/publish.
- Event: CRUD.
- Galeri/media: upload aman, validasi tipe/ukuran, preview.
- Komentar: daftar dan moderasi.
- Pengguna dan role minimal admin/editor.
- Pengaturan.
- Search/filter/pagination.
- Koneksi konten CMS ke frontend lokal.
- Seed/reset dataset uji.

SQLite + backend Python adalah kandidat arsitektur ringan, **belum diputuskan**. Sebelum memilih framework atau menambah dependensi:
1. Periksa `playground_server.py` dan struktur Playground.
2. Periksa dependensi dan pola server yang telah ada.
3. Periksa apakah aplikasi sudah punya komponen yang dapat digunakan ulang.
4. Buat rancangan data dan alur frontend-CMS.
5. Baru ajukan keputusan arsitektur dan backup sebelum implementasi.

CMS harus memiliki otorisasi sisi server, password hashing, upload yang dibatasi, data dummy, dan tidak menyimpan secret di log.

## 10. Matriks requirement dan test case

Satu matriks permanen harus dibuat di `docs/` dan menjadi sumber status resmi. Kolom minimum:
- Requirement ID, area/modul, requirement.
- Test Case ID, preconditions, test steps, expected result.
- Test level (Unit/Integration/E2E/Manual).
- Actual result, status (Not Run/Pass/Fail/Blocked/N/A).
- Evidence reference, Bug ID, severity, notes, tanggal verifikasi.

Pass hanya setelah actual result diverifikasi. Blocked berbeda dari Fail. N/A harus punya alasan. Evidence harus merujuk ke artefak aktual. Jangan masukkan secret.

## 11. Git Manager UI — ditunda

Menu Git Manager saat ini sudah berfungsi. Perubahan UI Push Backup / Pull Restore yang pernah diminta tetap dicatat sebagai penyempurnaan pasca-penyelesaian aplikasi. Jangan mengerjakannya sekarang.

## 12. Langkah pertama sesi berikutnya

Jangan langsung menulis CMS atau patch fitur.

1. Pengguna menempatkan `MASTER_PROJECT_ROADMAP_ACCEPTANCE_CRITERIA.md` ke `docs/` repository.
2. Verifikasi keberadaan file dan `git status`.
3. Lakukan audit terarah struktur `local_test_site/playground`, `playground_server.py`, dependensi, dan `.gitignore`.
4. Mulai matriks requirement/test case berdasarkan requirement yang sudah disepakati.
5. Lanjutkan satu checkpoint pada satu waktu.

**Checkpoint ini mencatat rencana dan keputusan. Tidak ada klaim bahwa CMS, seluruh komponen Playground, integrasi scanner, atau release validation telah selesai.**
