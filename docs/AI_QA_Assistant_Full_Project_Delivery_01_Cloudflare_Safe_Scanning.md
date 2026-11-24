# AI QA Assistant --- Full Project Delivery 01

## Cloudflare Safe Scanning

**Tanggal:** 20 November 2026\
**Status:** Draft untuk review --- belum disetujui GO\
**Repository:** `AI-QA-Assistant`\
**Branch:** `master`

------------------------------------------------------------------------

## 1. Tujuan milestone

Menyediakan proses pemindaian website yang aman ketika target
menggunakan Cloudflare atau mekanisme pembatasan akses lain. Aplikasi
harus dapat:

-   memindai website yang dapat diakses secara normal;
-   memindai website yang dilindungi Cloudflare setelah pemilik/admin
    memberikan akses resmi;
-   mencatat bukti dan status pembatasan akses;
-   menghentikan pekerjaan yang terdampak ketika challenge, WAF block,
    atau pembatasan akses terdeteksi;
-   membedakan pembatasan akses dari bug website.

Aplikasi **tidak mengubah konfigurasi Cloudflare**. Allowlisting IP atau
aturan WAF yang dibatasi scope dilakukan oleh admin website. Aplikasi
hanya mencatat otorisasi dan konfirmasi admin, lalu menjalankan scan
normal ketika akses memang tersedia.

## 2. Batasan keamanan yang tidak boleh berubah

1.  Tidak melewati atau menyelesaikan CAPTCHA, Cloudflare challenge,
    WAF, atau kontrol keamanan lain.
2.  Tidak melakukan credential guessing dan tidak mengakses password,
    token, cookie, atau session.
3.  Tidak menonaktifkan atau melemahkan `RequestSafetyController`,
    `PlaywrightRequestGuard`, pembatasan origin, redirect protection,
    request rate limit, maupun ambang penghentian 403.
4.  Jika challenge atau block tetap muncul, hentikan tahap terdampak,
    simpan status aman, dan minta akses resmi dari admin.
5.  `Access Restricted` bukan temuan bug website.
6.  Data otorisasi dipisahkan per proyek/klien. Tidak menyimpan rahasia
    atau kredensial.
7.  Tidak melakukan scan eksternal kecuali target dan scope secara
    eksplisit diotorisasi.

## 3. Baseline yang diketahui

### 3.1 Verifikasi pengujian

-   Full regression terakhir yang dilaporkan: **252 tests, OK**, pada 20
    November 2026.
-   Pengujian terarah Access Classification dan Unified QA Workflow:
    **18 tests sukses**.
-   Tes 403 threshold sebelumnya: threshold tercapai dan request
    berikutnya tidak dikirim.
-   Tes redirect sebelumnya: redirect eksternal tidak diikuti.
-   Pengujian Cloudflare yang tersedia saat ini menggunakan
    fixture/lokal; akurasi pada Cloudflare eksternal belum dibuktikan.
-   Clean install pada laptop kedua belum dilakukan.
-   Pengujian pemindaian eksternal belum dilakukan.

Catatan: baseline 252 tes berasal dari checkpoint sebelum milestone ini.
Tes terarah 18 sukses merupakan hasil yang dilaporkan pengguna pada sesi
audit ini. Tidak ada source code yang diubah selama audit desain.

### 3.2 Repository baseline

Hasil `git status --short --branch` terakhir:

-   Branch `master`, tracking `origin/master`.
-   32 tracked files modified.
-   Banyak untracked files termasuk modul, test, dokumentasi, audit, dan
    batch scripts.
-   Tidak ada staged files.

Semua perubahan yang ada harus dipertahankan. `batch_scripts` adalah
folder kerja lokal yang sebagian besar memang tidak dilacak Git. Jangan
menghapus, membersihkan, memindahkan, atau otomatis menambahkan
file-file tersebut ke Git.

Dilarang menjalankan `git reset`, `git clean`, stash, checkout, atau
operasi destruktif lain untuk "membersihkan" working tree. Tidak ada
commit, push, merge, atau release tanpa persetujuan.

## 4. Audit arsitektur yang sudah tersedia

  ---------------------------------------------------------------------------
  Area                                    Kondisi yang teramati
  --------------------------------------- -----------------------------------
  `core/access_classification.py`         Klasifikasi indikator Cloudflare
                                          challenge/block dan generic access
                                          restriction sudah ada

  `core/request_safety.py`                Batas request per menit dan
                                          penghentian berdasarkan consecutive
                                          403 sudah ada

  `core/playwright_request_guard.py`      Same-origin guard, sensitive-query
                                          rejection, redirect blocking,
                                          request guard sudah ada

  `modules/frontend_scanner.py`           Homepage, image, link inspection;
                                          integrasi classifier dan request
                                          guard

  `modules/website_discovery.py`          Discovery halaman dan penghentian
                                          ketika akses dibatasi

  `modules/generic_uat_inspection.py`     Inspeksi DOM read-only dan
                                          klasifikasi akses

  `modules/authentication_discovery.py`   Discovery autentikasi read-only;
                                          tidak login atau membaca kredensial

  `modules/qa_workflow.py`                Unified workflow memakai satu
                                          safety controller dan melewati
                                          tahap berikutnya saat akses
                                          dibatasi

  `core/progress_tracking.py`             Progress event dengan status
                                          running, waiting, completed,
                                          failed, stopped

  `core/project_manager.py`               Penyimpanan proyek terisolasi dan
                                          helper path aman

  `core/report_manager.py`                Laporan JSON unik, atomik, sanitasi
                                          data sensitif dan path

  `core/evidence_manager.py`              Registry evidence dan verifikasi
                                          SHA-256

  `core/document_manager.py`              Pola penyimpanan dokumen JSON
                                          atomik yang dapat dijadikan
                                          referensi
  ---------------------------------------------------------------------------

### 4.1 Catatan klasifikasi yang harus diperbaiki

Audit classifier menunjukkan potensi false positive: kondisi
`just_a_moment_challenge` dapat mengklasifikasikan challenge sebagai
Cloudflare meskipun marker Cloudflare tidak ditemukan. Desain perbaikan
harus membedakan:

-   `CLOUDFLARE_CHALLENGE`: terdapat indikator Cloudflare yang cukup dan
    indikator challenge;
-   `SECURITY_CHALLENGE`: challenge terdeteksi tetapi provider tidak
    cukup terbukti;
-   `CLOUDFLARE_WAF_BLOCK`: indikator Cloudflare dan frasa block yang
    relevan;
-   `CLOUDFLARE_ACCESS_RESTRICTED`: indikator Cloudflare dengan HTTP
    401/403/429;
-   generic `WAF_BLOCK`, `HTTP_ACCESS_RESTRICTED`, atau
    `HTTP_RATE_LIMITED` jika provider tidak teridentifikasi.

Jangan menganggap satu judul generik seperti "Just a moment" sebagai
bukti Cloudflare.

### 4.2 Konsistensi resource inspection

Homepage saat ini dapat menggunakan status HTTP, title, dan body untuk
klasifikasi. Image/link inspection pada beberapa jalur lebih banyak
mengandalkan status HTTP. Dalam milestone ini, audit implementasi harus
menentukan cara konsisten mengklasifikasikan resource response tanpa
membaca/menyimpan konten sensitif secara berlebihan. Jika body response
tidak tersedia atau tidak aman dibaca, gunakan status HTTP dan indikator
yang memang tersedia; jangan mengarang provider.

## 5. Desain Authorization Manager

### 5.1 Struktur penyimpanan yang diusulkan

``` text
projects/
└── CLIENT_A/
    ├── project_config.json
    ├── authorization/
    │   ├── authorization_records.json
    │   └── history/
    ├── reports/
    ├── evidence/
    ├── logs/
    └── documentation/
```

Data authorization terpisah dari `project_config.json` dan laporan
inspeksi. Semua path harus dibuat melalui helper path aman proyek
(`get_project_path` / `resolve_project_path`).

### 5.2 Data record yang diusulkan

  -----------------------------------------------------------------------
  Field                               Tujuan
  ----------------------------------- -----------------------------------
  `authorization_id`                  ID unik record

  `project_id`                        Ikatan ke proyek

  `target`                            Host/domain dan scope URL yang
                                      diizinkan

  `approved_by`                       Nama/peran pihak yang memberikan
                                      izin

  `approval_reference`                Referensi tiket/email/dokumen;
                                      jangan menyalin rahasia

  `approved_at`                       Waktu persetujuan

  `expires_at`                        Masa berlaku

  `approved_scope`                    Batas target, metode, dan aktivitas
                                      yang diizinkan

  `status`                            `Pending`, `Approved`, `Revoked`,
                                      `Expired`

  `allowlisting_status`               `Not Required`, `Pending`,
                                      `Confirmed`

  `admin_confirmation`                Identitas/pernyataan konfirmasi
                                      admin dan waktu konfirmasi

  `notes`                             Catatan non-rahasia

  `created_at`, `updated_at`          Audit timestamps
  -----------------------------------------------------------------------

Tidak boleh menyimpan password, token, cookie, session, API key, atau
kredensial.

### 5.3 Aturan keputusan otorisasi

-   Record `Approved` harus memiliki target dan scope yang cocok dengan
    target scan.
-   Persetujuan yang kedaluwarsa atau dicabut tidak valid.
-   Jika allowlisting diperlukan, status harus `Confirmed` sebelum
    aplikasi menandai akses sebagai siap.
-   `Pending`, `Revoked`, `Expired`, scope tidak cocok, atau konfirmasi
    admin belum ada berarti scan tidak boleh dimulai untuk target yang
    mensyaratkan otorisasi tersebut.
-   Status `Not Required` hanya boleh dipilih jika memang tidak
    diperlukan untuk target tersebut dan keputusan itu dicatat.
-   Otorisasi tidak mengesampingkan challenge/block yang benar-benar
    diamati. Jika masih terblokir, hentikan scan.
-   Aplikasi tidak memverifikasi konfigurasi Cloudflare secara langsung;
    status `Confirmed` adalah pernyataan/konfirmasi admin yang dicatat.

### 5.4 Riwayat dan penyimpanan

-   Simpan snapshot record saat perubahan status, dengan timestamp dan
    aktor.
-   Gunakan pola temporary-file lalu atomic replace yang konsisten
    dengan `report_manager.py`/`document_manager.py`.
-   Validasi schema dan project ID setiap read/write.
-   Gunakan path containment dan tolak symlink/junction sesuai helper
    yang sudah ada.
-   Hindari lost update: sebelum menulis, validasi record terbaru;
    implementasikan penulisan terkontrol agar dua update bersamaan tidak
    saling menimpa. Jika locking lintas proses belum tersedia,
    dokumentasikan batasan dan gunakan mekanisme sederhana yang sesuai
    platform tanpa dependency baru.
-   Backup dan rollback tidak boleh menghapus data proyek atau
    authorization records yang sudah ada.

## 6. Integrasi workflow dan laporan

### 6.1 Sebelum scan

1.  Validasi project dan target.
2.  Muat record otorisasi untuk target.
3.  Periksa status, expiry, scope, dan allowlisting confirmation.
4.  Jika belum valid, hentikan sebelum request jaringan dan berikan
    status yang jelas (misalnya
    `Authorization Required`/`Access Restricted` sesuai model status
    yang disepakati).
5.  Jika valid, lanjutkan menggunakan Playwright dan seluruh guard yang
    sudah ada.

### 6.2 Saat scan berlangsung

-   Jika challenge, WAF block, HTTP restriction, atau threshold 403
    terjadi, hentikan tahap terdampak.
-   Jangan mencoba menyelesaikan challenge atau mengubah browser
    identity.
-   Tahap berikutnya yang menggunakan safety controller bersama harus
    dilewati.
-   Progress terminal harus `stopped` untuk access restriction.
-   Evidence yang disimpan hanya evidence aman yang benar-benar diamati.

### 6.3 Laporan

Laporan inspeksi tetap disimpan melalui `save_inspection_report`.
Tambahkan snapshot referensi minimal: - `authorization_id`; - status
otorisasi saat scan; - status konfirmasi allowlisting; - target/scope
yang telah disanitasi; - timestamp pemeriksaan otorisasi.

Jangan menyalin seluruh catatan personal atau rahasia ke laporan.
Laporan lama harus tetap dapat dibaca dan backward-compatible.

## 7. Daftar file kandidat

Daftar final harus disesuaikan saat implementasi setelah backup dan
pemeriksaan diff terakhir. Kandidat perubahan:

**Core** - `core/access_classification.py` - modul baru
`core/authorization_manager.py` (nama final dapat disesuaikan dengan
konvensi repo) - `core/report_manager.py` - kemungkinan
`core/project_manager.py` hanya jika helper yang ada belum cukup -
kemungkinan `core/progress_tracking.py` hanya jika status/aktivitas baru
memang diperlukan

**Workflow** - `modules/qa_workflow.py` -
`modules/frontend_scanner.py` - `modules/website_discovery.py` -
`modules/generic_uat_inspection.py` -
`modules/authentication_discovery.py`

**Tests** - `tests/test_access_classification.py` - test baru untuk
authorization manager, isolasi proyek, expiry/scope/status, atomic
write, sanitasi, workflow gate, report snapshot, dan regression. - test
integrasi yang sudah ada terkait request guard, 403 threshold, redirect,
dan workflow harus tetap lulus.

**Docs** - `docs/PROJECT_SETUP_GUIDE.md` -
`docs/PORTABLE_SETUP_GUIDE.md` - `docs/RELEASE_READINESS_CHECKLIST.md` -
checkpoint baru untuk milestone ini.

Jangan mengubah file kandidat hanya karena tercantum di sini. Ubah hanya
bila kebutuhan dan diff audit membuktikannya.

## 8. Acceptance criteria

  -----------------------------------------------------------------------
  ID                                  Kriteria penerimaan
  ----------------------------------- -----------------------------------
  CF-01                               Website normal yang diotorisasi
                                      dapat dipindai

  CF-02                               Target yang memerlukan akses admin
                                      hanya dapat dipindai setelah record
                                      valid dan konfirmasi akses tercatat

  CF-03                               Cloudflare challenge
                                      teridentifikasi secara konservatif

  CF-04                               Cloudflare WAF block
                                      teridentifikasi secara konservatif

  CF-05                               Generic security challenge tidak
                                      salah diberi label Cloudflare

  CF-06                               HTTP 401/403/429 diklasifikasikan
                                      sebagai pembatasan akses

  CF-07                               Scope target yang tidak cocok
                                      menolak scan sebelum request

  CF-08                               Expired/revoked/pending
                                      authorization menolak scan

  CF-09                               Jika allowlisting diperlukan dan
                                      belum confirmed, scan ditolak

  CF-10                               Challenge/block saat scan
                                      menghentikan pekerjaan terdampak

  CF-11                               Access Restricted tidak dilaporkan
                                      sebagai website bug

  CF-12                               Same-origin, redirect blocking,
                                      sensitive-query rejection tetap
                                      aktif

  CF-13                               Rate limit dan 403 threshold tetap
                                      aktif

  CF-14                               Unified workflow melewati tahapan
                                      lanjutan setelah akses dibatasi

  CF-15                               Progress terminal sesuai hasil
                                      faktual

  CF-16                               Evidence hanya terdaftar jika file
                                      benar-benar ada dan SHA-256 valid

  CF-17                               Laporan menyimpan snapshot
                                      authorization yang aman dan tetap
                                      backward-compatible

  CF-18                               Tidak ada credential/token/cookie
                                      dalam log, report, atau
                                      authorization record

  CF-19                               Data authorization antar proyek
                                      terisolasi

  CF-20                               Backup/rollback tidak menghapus
                                      data proyek atau perubahan kerja
                                      yang sudah ada
  -----------------------------------------------------------------------

## 9. Test plan

### Unit tests

-   Cloudflare marker + challenge phrase.
-   Generic challenge tanpa provider marker.
-   Judul "Just a moment" saja tidak cukup.
-   Cloudflare block phrase.
-   HTTP 401/403/429.
-   Parameter sensitif tidak tersimpan.
-   Authorization record schema dan required fields.
-   Pending/Approved/Revoked/Expired.
-   Expiry boundary dan timezone.
-   Target/scope matching.
-   Allowlisting Not Required/Pending/Confirmed.
-   Project isolation.
-   Atomic write failure cleanup.
-   Path traversal/symlink/junction rejection.
-   History append dan consistency.

### Integration tests

-   Authorization gate menolak request ketika belum valid.
-   Authorization valid melanjutkan workflow normal.
-   Challenge/block menghentikan workflow.
-   Satu shared RequestSafetyController tetap digunakan.
-   403 threshold tidak mengirim request setelah batas.
-   Redirect eksternal tidak diikuti.
-   Laporan menyimpan authorization snapshot yang benar.
-   Evidence registry dan SHA-256 tetap valid.
-   Progress menjadi stopped pada access restriction.
-   Existing reports schema lama tetap dapat dibaca.

### Regression

Jalankan full suite:

``` powershell
& .\.venv-scanner\Scripts\python.exe -m unittest discover -s .\tests -v
```

Kriteria: semua test lulus; setiap skip harus memiliki alasan lingkungan
yang jelas dan tidak boleh menyembunyikan kegagalan.

### External validation

Hanya pada staging/target yang secara eksplisit diotorisasi dan setelah
admin mengonfirmasi allowlisting atau scoped WAF rule. Jika
challenge/block masih muncul, hentikan dan catat hasilnya. Tidak ada
bypass.

## 10. Backup, rollback, dan data preservation

Sebelum penerapan: 1. Buat backup timestamped di folder `backups/` yang
tidak masuk Git. 2. Backup hanya file source/docs yang akan diubah,
beserta manifest path, ukuran, dan SHA-256. 3. Jangan menyalin atau
mengubah `projects/`, `reports/`, `evidence/`, `logs/`, atau data klien.
4. Simpan working tree baseline; jangan menganggap perubahan
tracked/untracked saat ini sebagai hasil milestone baru. 5. Verifikasi
backup dengan membandingkan jumlah file dan SHA-256.

Rollback: - Hanya mengembalikan file yang diubah oleh batch milestone
ini. - Sebelum restore, verifikasi hash/current state dan minta
konfirmasi bila ada perubahan setelah penerapan. - Jangan menghapus file
untracked atau file kerja pengguna. - Jangan melakukan Git
reset/clean/stash. - Authorization records yang sudah dibuat tidak boleh
terhapus oleh rollback kode. Backup data otorisasi terpisah jika migrasi
schema memang diperlukan.

## 11. Batch PowerShell yang akan disiapkan

Semua script harus memakai `$ErrorActionPreference = "Stop"`, validasi
root project, preflight, dan log tanpa rahasia.

1.  `Prepare_Cloudflare_Safe_Scanning_Batch.ps1`
    -   memeriksa root, interpreter, status Git, daftar target file,
        baseline test;
    -   membuat backup dan manifest hash;
    -   tidak mengubah source.
2.  `Apply_Cloudflare_Safe_Scanning_Batch.ps1`
    -   hanya dijalankan setelah GO;
    -   memvalidasi backup dan baseline;
    -   menerapkan file perubahan secara terkontrol;
    -   tidak mengubah data proyek/klien.
3.  `Verify_Cloudflare_Safe_Scanning_Batch.ps1`
    -   menjalankan focused tests, full regression, diff check, secret
        scan;
    -   memverifikasi laporan/evidence dan status Git;
    -   menghasilkan verification report.
4.  `Rollback_Cloudflare_Safe_Scanning_Batch.ps1`
    -   menampilkan file target dan hash;
    -   meminta konfirmasi eksplisit;
    -   memulihkan hanya file yang dimiliki batch ini;
    -   tidak menghapus data proyek atau file lain.

## 12. Risiko dan mitigasi

  -----------------------------------------------------------------------
  Risiko                              Mitigasi
  ----------------------------------- -----------------------------------
  False positive Cloudflare           Klasifikasi konservatif dan fixture
                                      tests

  Authorization stale/expired         Validasi expiry setiap scan

  Scope terlalu luas                  Scope eksplisit dan exact target
                                      matching

  Admin belum benar-benar allowlist   Status confirmation dicatat sebagai
                                      pernyataan admin; block aktual
                                      tetap menghentikan scan

  Race condition saat update record   Controlled write, validation, dan
                                      test concurrent update

  Data klien tercampur                Project-scoped path dan isolation
                                      tests

  Rollback menghapus kerja pengguna   Manifest file-owned dan rollback
                                      scoped

  Regression pada scanner             Full regression dan focused
                                      security tests
  -----------------------------------------------------------------------

## 13. Batasan yang belum dapat diklaim

-   Akurasi klasifikasi pada semua variasi Cloudflare eksternal belum
    terbukti.
-   Aplikasi tidak dapat membuktikan konfigurasi allowlisting Cloudflare
    secara mandiri; status confirmed berasal dari admin.
-   Clean install laptop kedua belum diverifikasi.
-   Backup/restore produksi belum diuji pada data klien nyata; yang
    tersedia adalah drill sintetis.
-   Tidak ada klaim bahwa milestone ini telah diimplementasikan atau
    diterima.

## 14. Keputusan yang diminta

Paket ini adalah **rancangan delivery untuk ditinjau**, bukan instruksi
untuk menjalankan perubahan sekarang.

-   **GO:** setujui implementasi sesuai ruang lingkup dan acceptance
    criteria.
-   **NO GO:** jangan mengubah source; revisi desain terlebih dahulu.
-   **GO dengan revisi:** catat revisi yang diperlukan sebelum batch
    apply dibuat.

Sampai persetujuan eksplisit diberikan, tidak ada source code,
dependency, project data, atau Git state yang boleh diubah oleh
milestone ini.

## 15. Implementation addendum — 2026-11-20

The project owner approved GO for the Cloudflare Safe Scanning implementation. The following initial authorization integration is now present in the source package:

- `core/authorization_manager.py` stores project-scoped records at `authorization/authorization.json`, with an audit history and atomic writes.
- Menu 11 in `agent.py` allows the operator to view, create/replace, and revoke authorization for the active project. The target is taken from the project scanner configuration; the menu does not accept a separate target URL.
- Scanner entry points in menus 4, 5, and 6, plus Unified QA menu 10, validate an active record before making website requests.
- The required workflow scopes are `frontend` and `read_only`. Missing, expired, revoked, mismatched, malformed, or unreadable authorization fails closed.
- A blocked Unified QA result is recorded as `Blocked` with no fabricated frontend result (`frontend: null`). The report includes authorization status and message.
- Administrator access confirmation is recorded when supplied. It does not configure Cloudflare/WAF, prove allowlisting, or override a challenge/block. If access remains restricted, the scanner stops under the existing request-safety rules.

Verification performed against the source archive on 2026-11-20:
- 41 focused authorization/workflow/menu tests passed (excluding the browser-dependent local end-to-end test).
- 209 selected regression tests passed after excluding Playwright-dependent test modules and the browser-based Unified QA end-to-end test.
- A complete 268-test run could not be fully verified in this audit runtime: 35 tests that launch Playwright failed because this runtime did not have the required Chromium browser and/or could not run Playwright Sync API in the test's asyncio context. These failures are environment limitations observed during this audit; they are not counted as passes.
- The local browser end-to-end test and a real external Cloudflare/WAF scan remain unverified in this environment.

This addendum records implementation and test status; it does not constitute final release acceptance.

### Input masa berlaku otorisasi
Menu Kelola Otorisasi QA menerima tanggal dalam format `DD-MM-YYYY` dan waktu 24 jam `HH:MM` WIB (UTC+07:00). Contoh: `31-12-2026` dan `23:59`. Aplikasi mengonversi input tersebut ke ISO 8601 untuk penyimpanan dan validasi. Tanggal kedaluwarsa ditampilkan dalam format Indonesia, misalnya `31 Desember 2026, 23:59 WIB`.