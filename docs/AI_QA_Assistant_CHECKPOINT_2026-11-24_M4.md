# AI QA Assistant — Checkpoint M4
Tanggal: 24 November 2026

## 1. Konteks proyek

Folder aplikasi:
`<LOCAL_PATH>`

Data eksternal:
`<LOCAL_PATH>`

Tujuan M4 adalah memverifikasi backup dan restore aplikasi beserta data eksternal melalui staging terpisah, tanpa menimpa aplikasi aktif atau menghapus data sumber.

## 2. Backup dokumentasi sebelum pembaruan

Lokasi:
`backups\before_m4_documentation_20261124_132851`

Tiga dokumen telah dicadangkan. Verifikasi SHA-256: 3/3 cocok.

Checkpoint M3.2 tetap dipertahankan sebagai catatan historis.

## 3. M4.4 — Full backup

Lokasi backup:
`<LOCAL_PATH>`

Struktur:
- `01_APPLICATION/`
- `02_EXTERNAL_DATA/projects/`
- `02_EXTERNAL_DATA/logs/`
- `manifest.json`
- `manifest.sha256`
- Tiga log Robocopy.

Virtual environment root `.venv-scanner` dan root `__pycache__` dikecualikan dari salinan aplikasi. Folder `.git` dan folder historis lainnya tetap dipertahankan.

Hasil verifikasi SHA-256:
- Aplikasi: 2.486 file cocok.
- Data projects: 57 file cocok.
- Data logs: 11 file cocok.
- Total: 2.554 file cocok.
- Missing: 0.
- Extra: 0.
- Mismatch: 0.

Manifest checksum:
`2DD3B9369B2308F70A8E2A232969832DA8789507E8F60348A88C0E34745613DB`

Status: BERHASIL DAN TERVERIFIKASI.

## 4. M4.5 — Restore staging

Lokasi restore:
`<LOCAL_PATH>`

Aplikasi, projects, dan logs dipulihkan ke direktori staging terpisah.

Verifikasi SHA-256 backup terhadap hasil restore:
- Aplikasi: 2.486/2.486 cocok.
- Projects: 57/57 cocok.
- Logs: 11/11 cocok.
- Total: 2.554 file cocok.
- Missing: 0.
- Extra: 0.
- Mismatch: 0.

Status: BERHASIL.

## 5. Functional smoke test

Pada aplikasi hasil restore:
- Python 3.14.10 berhasil digunakan.
- Import `core.data_paths` berhasil.
- Import `core.project_manager` berhasil.
- `DATA_ROOT`, `PROJECTS_DIR`, dan `SYSTEM_LOG_DIR` menunjuk ke direktori restore.
- Project Manager menemukan 5 proyek valid:
  - `001` — Black Experience
  - `AUTH_TEST_20261120` — Authorization Local Test
  - `LOCAL_SCANNER_TEST` — Local Scanner Test
  - `QA-DEMO-001` — QA Demo - SauceDemo
  - `QUICK_TEST_PORTABILITY_2026` — Quick Test Portability

Tidak ada scanner yang dijalankan dalam smoke test ini.

## 6. Full regression pada hasil restore

Log:
`restore_logs\FULL_REGRESSION_TEST.txt`

Hasil:
- Total test: 280
- Skipped: 3
- Failed: 0
- Durasi: 40.630 detik
- Python test exit code: 0
- Status: `OK (skipped=3)`

Beberapa test menampilkan pesan:
`Screenshot evidence registration failed; inspection continues.`

Test terkait tetap berakhir `ok`. Pesan ini dicatat sebagai keterbatasan hasil evidence; tidak boleh dianggap sebagai bukti bahwa semua screenshot berhasil diregistrasi.

## 7. Batasan dan hal yang belum diverifikasi

- Pengujian restore dilakukan ke direktori staging, bukan menimpa instalasi aktif.
- Rollback instalasi produksi belum diuji.
- Simulasi kerusakan atau kehilangan data nyata belum dilakukan.
- Pemulihan dengan data klien produksi belum diverifikasi.
- Pengujian Cloudflare/WAF eksternal tidak dilakukan.
- Isolasi namespace `client_id` dan struktur `clients/{client_id}/projects/` belum diimplementasikan.
- Backup ini adalah salinan direktori terverifikasi, bukan bukti bahwa proses backup/restore otomatis sudah menjadi fitur aplikasi.
- Virtual environment tidak disalin; setiap perangkat harus membuat environment sendiri.

## 8. Status milestone

- M2 — Desain pemisahan data: DISETUJUI.
- M3.1 — Fondasi lokasi data: SELESAI.
- M3.2 — Migrasi projects/logs dan launcher: SELESAI DAN DIVERIFIKASI.
- M3.2 — Pemisahan multi-klien penuh: BELUM DIIMPLEMENTASIKAN.
- M4.1 — Audit backup/restore: SELESAI.
- M4.2–M4.3 — Verifikasi backup lama: SELESAI.
- M4.4 — Full backup dan manifest: SELESAI DAN TERVERIFIKASI.
- M4.5 — Restore staging, smoke test, dan full regression: SELESAI.
- M4 — Backup dan restore staging: SELESAI.
- Rollback produksi dan disaster recovery: BELUM DIVERIFIKASI.

## 9. Aturan kerja berikutnya

1. Kerjakan satu checkpoint pada satu waktu.
2. Jangan menganggap langkah berhasil sebelum hasil diverifikasi.
3. Buat backup sebelum perubahan besar.
4. Jangan menghapus data proyek, log, evidence, report, atau backup.
5. Jangan memindahkan virtual environment antarperangkat.
6. Pertahankan batas keamanan scanner dan hentikan pemindaian saat ambang 403 tercapai.
7. Lanjutkan ke Page Inspection setelah checkpoint ini disimpan dan diverifikasi.