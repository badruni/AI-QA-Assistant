# AI QA Assistant — Checkpoint M3.2
Tanggal: 24 November 2026

## 1. Lingkungan
- OS: Windows, PowerShell.
- Folder aplikasi: `<LOCAL_PATH>`
- Python: 3.14.10.
- Environment: `.venv-scanner`.
- Playwright: 1.65.1.
- Chromium: sudah terpasang dan berhasil diuji.

## 2. Backup sebelum M3.2 launcher
Folder backup dokumentasi:

`backups\before_m3_2_launcher_20261124_111141`

File yang dicadangkan:
- `PROJECT_SETUP_GUIDE.md`
- `PORTABLE_SETUP_GUIDE.md`
- `AI_QA_Assistant_CHECKPOINT_2026-11-24.md`

Verifikasi SHA-256: ketiga file cocok dengan sumber.

## 3. Direktori data eksternal
Lokasi:

`<LOCAL_PATH>`

Folder yang telah dimigrasikan:
- `projects/`
- `logs/`

Verifikasi checksum:
- Projects: 57 file sumber dan target; missing 0, extra 0, mismatch 0.
- Logs: 10 file sumber dan target; missing 0, extra 0, mismatch 0.

Data sumber lama tetap dipertahankan. Folder historis `LOGGER_TEST` dan `SECURITY_TEST` juga dipertahankan walaupun tidak memiliki `project_config.json`; keduanya bukan proyek terdaftar di Project Manager.

## 4. Aktivasi data eksternal
`AI_QA_DATA_DIR` telah diuji mengarah ke:

`<LOCAL_PATH>`

Verifikasi:
- `core.data_paths` mengarah ke direktori eksternal.
- Project Manager membaca lima proyek terdaftar.
- Logger berhasil menulis System Log ke direktori eksternal.
- Menu aplikasi diuji tanpa menjalankan scanner.

## 5. Launcher
File baru:

`run_ai_qa_assistant.ps1`

Perilaku:
- Memilih `.venv-scanner`, lalu `.venv`, lalu Python sistem.
- Mengatur `AI_QA_DATA_DIR` berdasarkan `%USERPROFILE%\AI_QA_Assistant_Data`.
- Menjalankan `agent.py` dari folder aplikasi.
- Tidak menyimpan environment variable secara permanen di Windows.

Validasi sintaks PowerShell: valid.

Pengujian manual:
- Application path benar.
- Python path benar.
- Data path benar.
- Project Manager menampilkan lima proyek terdaftar.
- Aplikasi ditutup normal, exit code 0.

## 6. Regression test
Dengan `AI_QA_DATA_DIR` aktif:

`Ran 280 tests in 30.930s`

`OK (skipped=3)`

Tidak ada test gagal.

## 7. Batasan yang masih ada
- Namespace `client_id` belum diimplementasikan.
- Isolasi data antar-klien belum selesai.
- Struktur `clients/{client_id}/projects/` belum diterapkan.
- Migrasi baru mencakup `projects/` dan `logs/`.
- Backup dan test-results masih berada pada lokasi aplikasi.
- Belum dilakukan pengujian restore dari direktori data eksternal.
- Data sumber lama belum dihapus dan harus tetap dipertahankan.

## 8. Status milestone
- M2 — Desain pemisahan data: DISETUJUI.
- M3.1 — Fondasi lokasi data: SELESAI.
- M3.2 — Migrasi projects/logs dan launcher: BERHASIL DIVERIFIKASI.
- M3.2 — Pemisahan multi-klien penuh: BELUM SELESAI.
- M4 — Isolasi klien, backup/restore, portabilitas: BELUM SELESAI.

## 9. Langkah lanjutan
Sebelum mengembangkan namespace `client_id`, tentukan apakah aplikasi akan langsung mendukung beberapa klien terpisah atau tetap menggunakan struktur proyek saat ini untuk sementara. Jangan memindahkan data ke struktur baru sebelum seluruh API path, Project Manager, logger, scanner, evidence, reports, dan pengujian kompatibilitas siap.

## 10. Aturan kerja
- Satu checkpoint pada satu waktu.
- Verifikasi setiap perubahan.
- Backup sebelum perubahan besar.
- Jangan menghapus data proyek, log, evidence, report, atau backup.
- Jangan memindahkan virtual environment antarperangkat.
- Jangan menyimpan kredensial, token, atau cookie dalam log.
- Jangan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.
- Hentikan pemindaian setelah batas 403 yang dikonfigurasi tercapai.
- Jangan menjalankan git reset, clean, checkout, stage, atau commit tanpa instruksi dan pemeriksaan khusus.
