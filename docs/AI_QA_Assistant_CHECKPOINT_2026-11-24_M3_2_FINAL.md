

\# AI QA Assistant — Checkpoint Final M3.2

Tanggal: 24 November 2026



\## 1. Lingkungan

\- OS: Windows, PowerShell.

\- Folder aplikasi: `C:\\Users\\ASUS\\Projects\\AI\_QA\_Assistant\_RESTORE\_20261123`

\- Python: 3.14.10.

\- Environment: `.venv-scanner`.

\- Playwright: 1.65.1.

\- Chromium: terpasang dan telah diuji.



\## 2. Direktori data eksternal

Lokasi data:



`C:\\Users\\ASUS\\AI\_QA\_Assistant\_Data`



Data yang telah disalin:

\- `projects/`: 57 file.

\- `logs/`: 10 file.



Verifikasi SHA-256:

\- Projects: missing 0, extra 0, mismatch 0.

\- Logs: missing 0, extra 0, mismatch 0.



Data sumber lama tetap dipertahankan.

Folder historis `LOGGER\_TEST` dan `SECURITY\_TEST` juga dipertahankan meskipun tidak memiliki `project\_config.json`.



\## 3. Aktivasi data eksternal

\- `core.data\_paths` berhasil menggunakan direktori eksternal.

\- Project Manager berhasil membaca lima proyek terdaftar.

\- Logger berhasil menulis System Log ke direktori eksternal.

\- Menu aplikasi diuji tanpa menjalankan scanner.



\## 4. Launcher

File: `run\_ai\_qa\_assistant.ps1`



Perilaku:

\- Memilih `.venv-scanner`, `.venv`, atau Python sistem.

\- Menggunakan `%USERPROFILE%\\AI\_QA\_Assistant\_Data`.

\- Menjalankan `agent.py` dari folder aplikasi.

\- Menyimpan kondisi awal `AI\_QA\_DATA\_DIR`.

\- Memulihkan nilai sebelumnya setelah aplikasi selesai.

\- Menghapus variabel jika sebelumnya belum tersedia.



Verifikasi:

\- Sintaks PowerShell valid.

\- Launcher berhasil menjalankan aplikasi.

\- Lima proyek terdaftar berhasil ditampilkan.

\- Aplikasi keluar dengan exit code 0.

\- Pemulihan nilai environment variable yang sebelumnya tersedia berhasil.

\- Pemulihan kondisi tanpa environment variable sebelumnya berhasil.



\## 5. Regression test

Dengan data eksternal aktif:



`Ran 280 tests in 30.930s`



`OK (skipped=3)`



Tidak ada test gagal.



\## 6. Dokumentasi

Dokumentasi berikut telah diperbarui:

\- `docs/PROJECT\_SETUP\_GUIDE.md`

\- `docs/PORTABLE\_SETUP\_GUIDE.md`



Judul Update M3.2 yang duplikat telah dirapikan.

Keterangan pemulihan environment variable telah diperbarui.



Backup sebelum perbaikan akhir:



`backups\\before\_m3\_2\_final\_fix\_20261124\_112100`



Verifikasi SHA-256 backup: 3/3 file cocok.



\## 7. Batasan yang belum selesai

\- Namespace `client\_id` belum diimplementasikan.

\- Isolasi data antar-klien belum selesai.

\- Struktur `clients/{client\_id}/projects/` belum diterapkan.

\- Migrasi baru mencakup `projects/` dan `logs/`.

\- Backup dan test-results masih berada di lokasi aplikasi.

\- Pengujian restore dari direktori data eksternal belum dilakukan.

\- Data sumber lama belum dihapus dan harus tetap dipertahankan.



\## 8. Status milestone

\- M2 — Desain pemisahan data: DISETUJUI.

\- M3.1 — Fondasi lokasi data: SELESAI.

\- M3.2 — Migrasi projects/logs dan launcher: SELESAI DAN DIVERIFIKASI.

\- M3.2 — Pemisahan multi-klien penuh: BELUM SELESAI.

\- M4 — Isolasi klien, backup/restore, portabilitas: BELUM SELESAI.



\## 9. Aturan kerja

\- Kerjakan satu checkpoint pada satu waktu.

\- Verifikasi setiap perubahan.

\- Buat backup sebelum perubahan besar.

\- Jangan menghapus data proyek, log, evidence, report, atau backup.

\- Jangan memindahkan virtual environment antarperangkat.

\- Jangan menyimpan kredensial, token, atau cookie dalam log.

\- Jangan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.

\- Hentikan pemindaian setelah batas 403 yang dikonfigurasi tercapai.

\- Jangan menjalankan git reset, clean, checkout, stage, atau commit tanpa pemeriksaan dan instruksi khusus.
