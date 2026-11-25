# AI QA Assistant --- Project Checkpoint

**Tanggal:** 26 November 2026\
**Perangkat aktif:** Home laptop, Windows / PowerShell\
**Repository:** `C:\Users\ASUS\Projects\AI-QA-Assistant`

## 1. Tujuan proyek

AI QA Assistant membantu QA Engineer melakukan inspeksi website frontend
dan CMS secara black-box, mengumpulkan evidence, dan menghasilkan
laporan QA.

Prinsip wajib: - Hanya menguji website dengan izin. - Workflow scanner
bersifat read-only. - Tidak login, submit form, melakukan aksi
state-changing, atau membaca/menyimpan kredensial. - Tidak bypass
CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan. - Hentikan pemindaian
ketika ambang 403 terkonfigurasi tercapai. - Jangan mengarang temuan
atau evidence. - Pisahkan data setiap klien. - Source code terpisah dari
data pengguna. - Update tidak boleh menghapus data proyek, report,
evidence, atau log. - Backup, versioning, downgrade, dan rollback harus
dipertahankan.

## 2. Lingkungan home laptop

-   Repository: `C:\Users\ASUS\Projects\AI-QA-Assistant`
-   DataRoot eksternal: `C:\Users\ASUS\AI_QA_Assistant_Data`
-   Backup root: `C:\Users\ASUS\AI_QA_Assistant_Backups`
-   Virtual environment lokal: `.venv-scanner`
-   Python scanner: 3.14.10
-   Playwright: 1.65.1
-   python-docx: 1.2.0
-   Chromium: 158.0.8127.18

Jangan memindahkan `.venv-scanner` ke laptop lain. Setiap perangkat
membuat environment sendiri.

## 3. Arsitektur DataRoot

`core/data_paths.py` mewajibkan `AI_QA_DATA_DIR`: - Harus diatur sebelum
menjalankan aplikasi. - Harus berupa absolute path. - Tidak boleh berada
di dalam repository. - Tidak ada fallback diam-diam ke folder
repository. - `PROJECTS_DIR` mengarah ke `<AI_QA_DATA_DIR>\projects`. -
`SYSTEM_LOG_DIR` mengarah ke `<AI_QA_DATA_DIR>\logs`.

Contoh untuk home laptop:

``` powershell
$env:AI_QA_DATA_DIR = Join-Path $env:USERPROFILE "AI_QA_Assistant_Data"
```

Atur kembali variabel ini pada setiap sesi PowerShell baru sebelum
menjalankan aplikasi.

DataRoot eksternal berisi proyek, laporan, evidence, authorization
configs, dan log. Folder `projects/` dan `logs/` lama yang masih ada di
repository belum dihapus. Jangan menghapus atau menggabungkan data lama
dan DataRoot tanpa audit/migrasi terpisah.

## 4. Verifikasi yang sudah dilakukan

### Environment dan test suite --- 26 November 2026

-   `.venv-scanner` berisi dependensi yang dipin di `requirements.txt`.

-   Chromium berhasil dijalankan headless, versi `158.0.8127.18`.

-   Full test suite:

    ``` powershell
    .\.venv-scanner\Scripts\python.exe -m unittest discover -s tests -v
    ```

    Hasil: `Ran 303 tests in 83.303s`, `OK (skipped=3)`, exit code 0.

-   Tiga test yang skipped terkait kondisi symlink/permission pada
    Windows, bukan test failure.

-   Test menggunakan DataRoot sementara:
    `C:\Users\ASUS\AppData\Local\Temp\AI_QA_Assistant_TestData_20261126_002000`

-   `AI_QA_DATA_DIR` sudah dipastikan tidak tersisa setelah test.

-   Aplikasi berhasil dijalankan dengan DataRoot eksternal; menu tampil
    dan aplikasi keluar normal melalui menu 9. Ini hanya startup check,
    bukan pengujian seluruh workflow.

Jangan mengulang test suite atau startup check tanpa alasan. Tidak ada
klaim bahwa seluruh workflow website telah diuji ulang pada checkpoint
ini.

## 5. Audit source path

Audit source aktif pada `agent.py`, `core/*.py`, dan `modules/*.py`
menghasilkan 38 kecocokan untuk pola: - `PROJECTS_DIR`,
`SYSTEM_LOG_DIR`, `APP_ROOT`, `AI_QA_DATA_DIR` - Path
`projects`/`logs` - `Path.cwd`, `os.getcwd`, `os.path.abspath`,
`os.path.join`, `__file__`, `mkdir`, dan `open`

Hasil yang terlihat menunjukkan modul utama memakai jalur terpusat: -
`project_manager.py` menggunakan `PROJECTS_DIR` dari
`core.data_paths`. - `logger.py` menggunakan `PROJECTS_DIR` dan
`SYSTEM_LOG_DIR` dari `core.data_paths`. - `frontend_scanner.py`
menggunakan `PROJECTS_DIR` dari `core.data_paths`. - Modul evidence,
report, document, dan documentation mengakses proyek melalui
`PROJECTS_DIR` yang diimpor dari `project_manager.py`.

**Batas kesimpulan:** audit berbasis pola ini belum membuktikan secara
formal bahwa tidak ada setiap kemungkinan legacy path. Jangan menyatakan
audit menyeluruh selesai sebelum meninjau seluruh lokasi operasi file
dan hasil audit tambahan jika diperlukan.

## 6. Kondisi data lama dan DataRoot

Audit inventaris sebelumnya: - Repository `projects`: 7 proyek. -
DataRoot `projects`: 7 proyek. - Enam proyek identik byte-per-byte;
`LOCAL_SCANNER_TEST` berbeda. - Pada `LOCAL_SCANNER_TEST`, terdapat file
yang hanya ada di DataRoot, termasuk authorization config, screenshot,
konfigurasi sebelum redirect, dan report. - Evidence index dan log juga
memiliki entri yang berbeda antara repository dan DataRoot.

Tidak ada migrasi, penghapusan, atau overwrite yang dilakukan.
Pertahankan kedua lokasi sampai ada keputusan migrasi yang terencana.

## 7. Dokumentasi DataRoot --- status pekerjaan

Dokumen sumber yang diperiksa: - `docs/PROJECT_SETUP_GUIDE.md` -
`docs/PORTABLE_SETUP_GUIDE.md`

Keduanya sebelumnya masih menjelaskan data proyek/log berada di dalam
repository. Dua versi pembaruan telah disiapkan sebagai file terpisah: -
`PROJECT_SETUP_GUIDE_UPDATED.md` - `PORTABLE_SETUP_GUIDE_UPDATED.md`

File hasil pembaruan tersebut belum menggantikan file di repository.
Langkah berikutnya: 1. Unduh kedua file hasil pembaruan. 2. Di
PowerShell repository, buat backup kedua dokumen asli ke direktori
backup baru yang unik. 3. Salin file hasil pembaruan ke
`docs\PROJECT_SETUP_GUIDE.md` dan `docs\PORTABLE_SETUP_GUIDE.md`. 4.
Periksa diff dan pastikan tidak ada bagian yang hilang/berubah di luar
pembaruan DataRoot. 5. Verifikasi command dan link relatif di dokumen.

Contoh backup lokal (jalankan dari root repository; pilih nama backup
yang belum ada):

``` powershell
$BackupName = "BEFORE_DATAROOT_DOC_REPLACE_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupPath = Join-Path $env:USERPROFILE "AI_QA_Assistant_Backups\$BackupName"

if (Test-Path -LiteralPath $BackupPath) {
    throw "Backup path sudah ada. Pilih nama baru."
}

New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
Copy-Item -LiteralPath ".\docs\PROJECT_SETUP_GUIDE.md" -Destination $BackupPath
Copy-Item -LiteralPath ".\docs\PORTABLE_SETUP_GUIDE.md" -Destination $BackupPath
```

Jangan menganggap pembaruan dokumentasi sudah terpasang sebelum salinan
dan verifikasi dilakukan.

## 8. Status task pada sesi ini

1.  **Audit DataRoot / legacy path:** audit pola source aktif telah
    dilakukan; indikasi yang terlihat konsisten dengan DataRoot. Audit
    belum menjadi bukti formal untuk semua jalur file.
2.  **Pembaruan setup docs:** draft dua dokumen sudah dibuat, tetapi
    belum disalin ke repository dan belum diverifikasi melalui diff.
3.  **Checkpoint:** file checkpoint ini menjadi handoff untuk
    melanjutkan verifikasi dokumen.

Jangan menyatakan ketiga task final selesai sampai: - kedua dokumen
terpasang di repository, - diff dan instruksi PowerShell diverifikasi, -
kesimpulan audit path dicatat dengan batasan yang tepat.

## 9. Aturan kerja untuk sesi berikutnya

-   Gunakan PowerShell Windows.
-   Kerjakan satu checkpoint pada satu waktu.
-   Berikan perintah siap salin dan tunggu hasilnya.
-   Jangan menganggap command berhasil sebelum output diverifikasi.
-   Backup sebelum perubahan besar.
-   Jangan gunakan `git add .`, `git reset`, `git checkout`,
    `git clean`, atau perintah destruktif.
-   Jangan menghapus data repository lama atau DataRoot.
-   Jika ada error, diagnosis dahulu sebelum mengubah kode.

## 10. Roadmap berikutnya

Setelah tiga task DataRoot dan dokumentasi selesai, lanjutkan roadmap AI
QA Assistant sesuai urutan yang telah disepakati. Setelah itu kembali ke
pekerjaan Playground dan CMS QA.

Catatan Playground: - Local-only, `127.0.0.1`, port 8000. - Jangan
restart server tanpa diminta. - MyDreamZone adalah konsep
otomotif/keluarga/komunitas fiktif; jangan menyalin brand, konten, atau
aset BlackXperience. - 56 kategori komponen, dual theme. - LP-3.4.1
carousel sudah diverifikasi manual (8 checks). - LP-3.4.2 modal/popup
adalah pekerjaan berikutnya dan belum dimulai.

## 11. Katalog 56 kategori komponen frontend MyDreamZone

Pada 26 November 2026, pengguna memberikan daftar lengkap 56 kategori komponen yang menjadi baseline cakupan audit dan pengujian frontend Playground. Daftar di bawah dicatat sesuai materi yang diberikan pengguna; daftar ini bukan hasil rekonstruksi atau tebakan.

### 1. Navigation & Layout

| No. | Komponen |
|---:|---|
| 1 | Header |
| 2 | Logo |
| 3 | Hamburger Menu |
| 4 | Expandable Sidebar |
| 5 | Overlay Navigation |
| 6 | Bottom Navigation |
| 7 | Footer |
| 8 | Floating Go to Top |

### 2. Homepage & Content

| No. | Komponen |
|---:|---|
| 9 | Hero Banner |
| 10 | Image Carousel / Slider |
| 11 | Carousel Indicator |
| 12 | CTA Button |
| 13 | What's On Section |
| 14 | Event Card |
| 15 | Winner Table |
| 16 | Horizontal Carousel |
| 17 | Highlights Section |
| 18 | Category Card |
| 19 | Latest Discussions |
| 20 | Discussion Card |
| 21 | Comment Input |
| 22 | Comment Thread |
| 23 | Nested Comments |
| 24 | Like Button |
| 25 | Comment Counter |
| 26 | View Counter |
| 27 | Reels Section |
| 28 | Video Card |
| 29 | Video Play Button |
| 30 | Gallery Section |
| 31 | Masonry Grid |
| 32 | Infinite Scroll |

### 3. Interactive Components

| No. | Komponen |
|---:|---|
| 33 | Hover Interaction |
| 34 | Tooltip |
| 35 | Expand / Collapse |
| 36 | Scrollable Container |
| 37 | Horizontal Scroll |
| 38 | Vertical Scroll |
| 39 | Modal / Popup |
| 40 | Floating Button |
| 41 | Loading Indicator |

### 4. Content & Navigation Components

| No. | Komponen |
|---:|---|
| 42 | Category Label |
| 43 | Article Card |
| 44 | Content Thumbnail |
| 45 | Content Grid |
| 46 | Pagination |
| 47 | Load More / More Threads |
| 48 | Gallery Image Viewer |

### 5. Responsive Components

| No. | Komponen |
|---:|---|
| 49 | Responsive Header |
| 50 | Responsive Sidebar |
| 51 | Responsive Bottom Navigation |
| 52 | Responsive Grid |
| 53 | Responsive Carousel |
| 54 | Responsive Card |
| 55 | Responsive Table |
| 56 | Responsive Gallery |

### Kaitannya dengan AI QA Assistant

Katalog ini menjadi salah satu dasar katalog komponen dan pemetaan kemampuan pengujian frontend oleh AI QA Assistant. Contoh pengujian yang diberikan pengguna:

| Komponen | Pengujian yang dapat dilakukan AI QA |
|---|---|
| Carousel | Next, previous, drag, swipe, indicator |
| Sidebar | Hover, expand, collapse, navigation |
| Tooltip | Visibility, positioning, text |
| Winner Table | Horizontal scroll, row hover, data visibility |
| Accordion | Expand, collapse |
| Comment Thread | Reply, nested reply, scroll |
| Like Button | Click, state change |
| Infinite Scroll | Load next content, loading, end state |
| Gallery | Image loading, layout, image viewer |
| Responsive Grid | Column changes, overflow, alignment |
| Bottom Navigation | Navigation, active state |
| Modal | Open, close, overlay, keyboard interaction |

**Catatan:** Accordion tercantum sebagai contoh kemampuan pengujian, tetapi bukan salah satu dari 56 nama kategori pada daftar bernomor. Jangan menambahkannya sebagai kategori ke-57 tanpa keputusan scope. Contoh pengujian di atas juga bukan batas kemampuan final scanner; skenario aktual perlu ditetapkan dan diverifikasi per komponen.

### Aturan penggunaan katalog

1. Gunakan 56 nama dan pengelompokan di atas sebagai baseline resmi inventaris Playground.
2. Pada audit, beri status per kategori: implemented, partial, not implemented, atau out of scope (dengan alasan). Jangan menyimpulkan status hanya dari keberadaan markup/tampilan statis.
3. Setiap kategori yang masuk scope harus dipetakan ke requirement dan satu atau lebih test case, termasuk precondition, langkah, expected result, actual result, status, dan referensi evidence.
4. Pengujian hanya boleh melaporkan perilaku yang benar-benar diamati. Jangan mengarang hasil, bug, atau evidence.
5. Katalog ini menjadi dasar pekerjaan A3 pada Master Roadmap dan penyusunan `docs/REQUIREMENTS_TEST_MATRIX.md` sesuai jadwal Day 2 pada Daily Work Plan.
6. Daftar ini mencatat cakupan komponen frontend Playground; bukan pernyataan bahwa seluruh komponen sudah diimplementasikan atau diuji.

## 12. Status handoff setelah pencatatan katalog

- Daftar lengkap 56 kategori telah diberikan langsung oleh pengguna dan dicatat pada bagian 11.
- Pertanyaan tentang sumber daftar 56 kategori yang sebelumnya belum terjawab kini terselesaikan untuk baseline kerja: gunakan daftar yang diberikan pada sesi 26 November 2026.
- Laporan audit Playground dan inventaris status implementasi aktual vs 56 kategori masih harus dibuat.
- Matriks requirement/test case belum dibuat; tetap ikuti urutan Daily Work Plan (Day 2), setelah audit Day 1 selesai.
- Belum ada perubahan source code aplikasi yang dilakukan melalui pencatatan ini.
