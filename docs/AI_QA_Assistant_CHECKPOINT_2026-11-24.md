\# AI QA Assistant — Checkpoint 24 November 2026



\## 1. Lokasi proyek



Folder proyek:

`C:\\Users\\ASUS\\Projects\\AI\_QA\_Assistant\_RESTORE\_20261123`



Environment:

\- Python 3.14.10

\- Virtual environment: `.venv-scanner`

\- Playwright 1.65.1

\- Browser Chromium sudah terpasang dan berhasil diuji dalam mode headless.



\## 2. Status pemulihan dan backup



Backup sebelum implementasi M3.1:



`C:\\Users\\ASUS\\Projects\\AI\_QA\_Assistant\_PRE\_DATA\_SPLIT\_20261124\_095837`



Log backup:



`C:\\Users\\ASUS\\Projects\\AI\_QA\_Assistant\_PRE\_DATA\_SPLIT\_20261124\_095837.log`



Verifikasi backup:

\- File sumber: 2.341

\- File backup: 2.341

\- Missing: 0

\- Extra: 0

\- Mismatch ukuran/hash: 0

\- Status: BACKUP VERIFIED



Backup dokumentasi:

`backups\\before\_m3\_1\_documentation\\`



File yang dicadangkan:

\- `PROJECT\_SETUP\_GUIDE.md`

\- `PORTABLE\_SETUP\_GUIDE.md`



\## 3. Rancangan arsitektur yang disetujui



Rancangan pemisahan aplikasi dan data telah disetujui:



\- Source code aplikasi tetap berada di folder aplikasi.

\- Data pengguna/klien akan dipisahkan ke direktori eksternal.

\- Data klien direncanakan menggunakan namespace `client\_id`.

\- Data yang belum diketahui kepemilikannya tidak boleh otomatis dimasukkan ke klien tertentu.

\- Template aplikasi tetap berada di folder `config/`.

\- Virtual environment dibuat secara lokal pada setiap perangkat.

\- Migrasi data dilakukan dengan copy dan verifikasi checksum; data lama dipertahankan sampai verifikasi selesai.



\## 4. Implementasi M3.1 — fondasi lokasi data



File baru:

\- `core/data\_paths.py`



File yang diintegrasikan:

\- `core/project\_manager.py`

\- `core/logger.py`

\- `modules/frontend\_scanner.py`



Perilaku `core/data\_paths.py`:

\- Membaca environment variable `AI\_QA\_DATA\_DIR`.

\- Nilai harus berupa absolute path.

\- Jika variabel tidak diatur, aplikasi menggunakan direktori aplikasi sebagai lokasi legacy.

\- Menyediakan `PROJECTS\_DIR` dan `SYSTEM\_LOG\_DIR`.

\- Tidak otomatis membuat direktori data.

\- Environment variable harus ditetapkan sebelum modul aplikasi diimpor/dijalankan.



Contoh konfigurasi PowerShell:



```powershell

$env:AI\_QA\_DATA\_DIR = 'D:\\AI\_QA\_Assistant\_Data'

python agent.py

```



Dengan konfigurasi tersebut:

\- Project data: `D:\\AI\_QA\_Assistant\_Data\\projects`

\- System logs: `D:\\AI\_QA\_Assistant\_Data\\logs`



Variabel tersebut hanya berlaku pada sesi PowerShell saat ini. Belum dibuat sebagai environment variable permanen.



\## 5. Penguatan keamanan path log



`core/logger.py`:

\- `write\_project\_log` sekarang menggunakan `resolve\_project\_directory`.

\- Validasi dilakukan dengan `require\_exists=False` untuk mempertahankan perilaku pembuatan folder log yang dibutuhkan pengujian.

\- Path proyek yang tidak aman ditolak dan tidak ditulis sebagai Project Log.



Konstanta `PROJECTS\_DIR` dan `SYSTEM\_LOG\_DIR` tetap tersedia pada level modul agar pengujian yang melakukan patch terhadap konstanta tersebut tetap berfungsi.



\## 6. Hasil pengujian



Import verification:

\- Project manager menggunakan lokasi projects yang diharapkan.

\- Logger menggunakan lokasi logs yang diharapkan.

\- Frontend scanner menggunakan lokasi projects yang diharapkan.

\- Template tetap dibaca dari `config/project\_template.json`.



External data path test:

\- Lulus.



Legacy path test:

\- Lulus.



Logger security tests:

\- 3 tests passed.



Full regression:

\- 280 tests

\- 3 skipped

\- 0 failed

\- Durasi: 30.641 detik

\- Status: OK



Log regresi:

`test-results\\m3\_1\\data\_paths\_regression\_final.txt`



\## 7. Dokumentasi



Dokumen yang diperbarui:

\- `docs/PROJECT\_SETUP\_GUIDE.md`

\- `docs/PORTABLE\_SETUP\_GUIDE.md`



Keduanya menjelaskan konfigurasi direktori data eksternal, contoh PowerShell, perilaku default legacy, dan batasan implementasi saat ini.



Verifikasi posisi bagian dokumentasi berhasil.



Script sementara:

`update\_docs\_m3\_1.py`



\## 8. Hal yang belum selesai



PENTING:

\- Belum ada pemindahan data proyek maupun log.

\- Belum ada implementasi namespace `client\_id`.

\- Isolasi data antar-klien belum selesai.

\- Belum ada migrasi ke struktur `clients/{client\_id}/projects/`.

\- `AI\_QA\_DATA\_DIR` belum disimpan secara permanen.

\- Lokasi default masih menggunakan direktori legacy aplikasi.

\- Belum dilakukan pengujian pemulihan data dari hasil migrasi eksternal.



Jangan menyatakan pemisahan data klien sudah selesai hanya karena fondasi path eksternal sudah tersedia.



\## 9. Integritas proyek



\- Git worktree sebelumnya sudah memiliki perubahan dan file untracked.

\- Jangan menjalankan git reset, clean, checkout, stage, atau commit tanpa instruksi dan pemeriksaan khusus.

\- Pertahankan folder backup historis dan nested `.git`.

\- Jangan menghapus data proyek, log, evidence, report, atau backup.

\- Jangan memindahkan virtual environment antarperangkat.

\- Jangan menyimpan kredensial, token, atau cookie dalam log.

\- Jangan melakukan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan website.

\- Tetap hentikan pemindaian jika batas 403 yang dikonfigurasi tercapai.



\## 10. Status checkpoint



M2 — Rancangan pemisahan data: DISETUJUI.



M3.1 — Fondasi lokasi data eksternal: IMPLEMENTASI DAN REGRESI SELESAI.



M3.2 — Pemisahan data dan migrasi: BELUM DIMULAI.



M4 — Pengujian isolasi klien, backup/restore, dan portabilitas: BELUM DIMULAI.



\## 11. Rencana lanjutan



Checkpoint berikutnya adalah M3.2.



Urutan yang disarankan:

1\. Tentukan lokasi direktori data eksternal yang akan digunakan.

2\. Periksa struktur dan isi `projects/` serta `logs/` yang ada.

3\. Rancang kompatibilitas antara struktur saat ini dan namespace `client\_id`.

4\. Tentukan pemetaan proyek ke klien berdasarkan informasi yang benar-benar tersedia.

5\. Salin data tanpa menghapus data lama.

6\. Verifikasi jumlah file dan checksum.

7\. Uji aplikasi menggunakan direktori eksternal.

8\. Pastikan seluruh proyek, log, report, dan evidence tetap dapat diakses.



Jangan mulai migrasi sebelum desain M3.2 dan strategi pemetaan klien disetujui.
