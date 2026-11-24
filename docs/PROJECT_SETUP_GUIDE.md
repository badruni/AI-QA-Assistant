# AI QA Assistant — Panduan Setup dan Penggunaan

## Tujuan dan batasan

AI QA Assistant menjalankan inspeksi website black-box berdasarkan observasi browser dan respons yang benar-benar diterima. Gunakan hanya pada website yang memiliki izin pengujian. Workflow Unified QA bersifat read-only: tidak login, mengisi atau mengirim formulir, melakukan aksi yang mengubah data, memecahkan CAPTCHA, menghindari Cloudflare Challenge, atau melewati WAF. Redirect tidak diikuti. Jika akses dibatasi, tahap lanjutan yang terdampak dihentikan dan diklasifikasikan.

## Instalasi baru

Lihat [Portable Setup Guide](PORTABLE_SETUP_GUIDE.md) untuk prosedur lengkap. Persyaratan yang diverifikasi pada repo ini adalah Windows 10/11, Python 3.14.x 64-bit, Playwright 1.65.1, python-docx 1.2.0, dan Chromium yang dipasang lewat Playwright. Buat virtual environment lokal baru pada setiap perangkat; jangan salin `.venv` atau `.venv-scanner`.

```powershell
py -3.14 -m venv .venv-scanner
.\.venv-scanner\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
python agent.py
```

Untuk regresi lokal:

```powershell
.\.venv-scanner\Scripts\python.exe -m unittest discover -s tests
```

## Proyek dan data

Dari menu aplikasi, buat proyek memakai ID yang hanya terdiri atas huruf, angka, `_`, atau `-`, lalu pilih proyek aktif. Masukkan URL HTTP(S) hanya setelah cakupan izin dikonfirmasi. Setiap proyek menyimpan konfigurasi, `logs/`, `reports/`, `evidence/`, dan dokumentasi di `projects/<project_id>/`. Jangan memasukkan kredensial ke config, issue, URL query, report, log, atau evidence.

Sebelum Unified QA, buka menu **11. Kelola Otorisasi QA**. Otorisasi dibuat per proyek, terikat ke target URL dari konfigurasi proyek, memiliki pemberi izin dan waktu kedaluwarsa ISO 8601 beserta zona waktu, serta scope `frontend` dan `read_only`. Ketik `YA` hanya setelah izin eksplisit dipastikan. Menu yang sama dapat melihat dan mencabut otorisasi. Jangan mencatat password, token, cookie, atau kredensial sebagai bagian dari otorisasi.

Jangan mengedit atau memindahkan folder proyek ketika aplikasi sedang berjalan. Backup harus dibuat ke lokasi baru yang tidak menimpa backup terdahulu. Prosedur backup, restore staging, update, dan rollback dijelaskan dalam [Portable Setup Guide](PORTABLE_SETUP_GUIDE.md).

### Lokasi data eksternal (opsional)

Secara default, aplikasi menyimpan data proyek di folder `projects/` dan System Log di folder `logs/` pada direktori aplikasi.

Jika ingin memisahkan data dari source code, atur environment variable `AI_QA_DATA_DIR` sebelum menjalankan aplikasi. Gunakan absolute path.

Contoh PowerShell:

```powershell
$env:AI_QA_DATA_DIR = 'D:\AI_QA_Assistant_Data'
python agent.py
```

Dengan konfigurasi tersebut, data proyek berada di `D:\AI_QA_Assistant_Data\projects\` dan System Log berada di `D:\AI_QA_Assistant_Data\logs\`. Template proyek tetap dibaca dari folder `config/` aplikasi.

Pengaturan `$env:` berlaku untuk sesi PowerShell saat ini. Jika variabel tidak diatur, aplikasi kembali menggunakan lokasi data lama di direktori aplikasi. Jangan mengubah lokasi data ketika aplikasi sedang berjalan.

Catatan: konfigurasi ini memusatkan lokasi `projects/` dan `logs/`. Pemisahan namespace berdasarkan klien (`client_id`) dan migrasi data klien merupakan pekerjaan lanjutan; fitur tersebut belum dinyatakan selesai.

## Unified QA Workflow

Pilih menu **10. Unified QA Workflow**. Sebelum request jaringan pertama, workflow menjalankan Authorization Preflight. Target harus cocok dengan otorisasi aktif yang belum kedaluwarsa dan mencakup scope `frontend` serta `read_only`. Jika otorisasi hilang, tidak valid, kedaluwarsa, atau tidak cocok, workflow berstatus `Blocked` dan tidak memulai browser/scanner. Hasil blocked tetap dapat disimpan sebagai report dengan `frontend: null`.

Setelah preflight valid, workflow menjalankan:

1. Frontend QA: homepage, image, dan link inspection.
2. Website Discovery: penemuan halaman same-origin dengan batas halaman.
3. Generic UAT: inspeksi DOM read-only atas halaman discovery.
4. Authentication Discovery: identifikasi sinyal autentikasi tanpa mencoba login.

Satu `RequestSafetyController` mengatur batas request dan ambang 403 lintas workflow setelah Authorization Preflight berhasil. HTTP 401/403/429 dan indikator challenge/WAF dapat menghasilkan `Access Restricted`; controller menghentikan request saat ambang 403 tercapai. Tahap berikutnya dilewati setelah kondisi restricted. HTTP 404/5xx dicatat sebagai hasil gagal sesuai tahap, bukan dianggap bukti bahwa seluruh situs gagal. Otorisasi hanya mencatat izin; aplikasi tidak mengubah konfigurasi Cloudflare/WAF dan tidak melakukan bypass. Jika challenge/block tetap muncul, hentikan pemindaian dan minta akses resmi.

Status `Passed` berarti pemeriksaan teknis yang dilakukan tidak menemukan kondisi gagal dalam ruang lingkup tahap tersebut; ini bukan jaminan kualitas seluruh website. Temuan DOM dan heuristic UAT umumnya `Needs Review` dan harus divalidasi manusia sebelum disebut bug. `Skipped` berarti tahap tidak dijalankan, misalnya akibat pembatasan akses.

## Report dan evidence

Laporan JSON dibuat sebagai file baru di `projects/<project_id>/reports/`; laporan lama tidak ditimpa. Setiap report dan evidence index disimpan di bawah direktori project ID yang tervalidasi. Path di luar direktori proyek ditolak.

Evidence yang **registered** berarti file ada dan metadata/hash SHA-256 tercatat di `evidence_index.json`. Ini belum berarti file masih valid. Evidence hanya **verified** jika `verify_evidence()` menemukan file proyek yang sesuai dan SHA-256 aktual sama dengan hash registry. Frontend QA dan unified report hanya memasukkan evidence ID yang lolos verifikasi. Evidence yang hilang atau berubah tidak diperbaiki atau dihapus otomatis; pertahankan file dan registry untuk investigasi.

Unified QA report juga mencatat status pengumpulan evidence secara terpisah
dari status inspeksi QA melalui field JSON berikut:

- `evidence_status`: `not_required` jika tidak ada screenshot yang diharapkan,
  `verified` jika seluruh evidence yang diharapkan berhasil diverifikasi,
  atau `failed` jika ada evidence yang tidak berhasil diverifikasi.
- `expected_evidence`: jumlah screenshot yang diharapkan dari tahapan workflow.
- `verified_evidence`: jumlah evidence yang berhasil diverifikasi dan dapat
  dicantumkan sebagai evidence terverifikasi.

`result.status` tetap menunjukkan hasil inspeksi QA. Dengan demikian,
inspeksi dapat berstatus `Passed` sementara `evidence_status` berstatus
`failed`. Kegagalan evidence tetap membuat terminal workflow berstatus gagal.


Sanitasi report/evidence/log menerapkan redaksi pada field sensitif dan pola teks sintetis seperti `password=value`, `token=value`, `credential=value`, serta API key. URL yang disimpan sebagai URL menghilangkan query dan fragment; `response_preview` selalu menjadi `[REDACTED]`. Sanitasi berbasis pola tidak dapat mengenali semua format rahasia. Jangan memasukkan kredensial nyata ke judul halaman, teks tautan, metadata, konfigurasi, report, evidence, atau log.

Evidence Viewer dapat menampilkan metadata, membuka screenshot, dan memverifikasi hash. Jangan mengubah file evidence setelah registrasi jika ingin mempertahankan verifikasi; perubahan akan terdeteksi sebagai mismatch.

## Keamanan dan troubleshooting

- **Access Restricted / Cloudflare / WAF:** hentikan dan minta pemilik website menyediakan akses pengujian yang disetujui. Jangan mencoba bypass atau retry untuk menghindari proteksi.
- **Timeout/network error:** verifikasi ketersediaan target dan koneksi pada cakupan izin. Jangan menganggap kegagalan jaringan sebagai bug website.
- **Browser tidak ditemukan:** jalankan `python -m playwright install chromium` dari environment scanner.
- **Report tidak tersimpan:** pertahankan laporan sebelumnya, periksa ruang disk dan hak akses folder proyek; jangan klaim report persisten jika write gagal.
- **Evidence hash mismatch:** evidence tersebut tidak terverifikasi. Pertahankan file dan index, lalu investigasi dari salinan.
- **Sensitive-data filter:** filter pola adalah pertahanan tambahan, bukan jaminan. Jangan memasukkan rahasia nyata saat pengujian.

## Status dokumentasi Milestone 3

Status readiness dan keterbatasan verifikasi ada di [Release Readiness Checklist](RELEASE_READINESS_CHECKLIST.md). Pada M4, backup penuh aplikasi dan data eksternal telah diverifikasi, kemudian berhasil dipulihkan ke direktori staging dan lulus full regression. Pengujian ini menggunakan salinan data pada perangkat pengembangan, bukan simulasi pemulihan bencana atau rollback instalasi produksi. Pemulihan dengan data klien produksi dan pengujian Cloudflare/WAF eksternal belum dilakukan.
### Lifecycle route Playwright

Sebelum scanner menutup browser context, request guard ditandai memasuki shutdown. Route baru yang tiba setelah tanda tersebut tidak menjalankan request atau mengonsumsi kuota controller; route dicoba dihentikan sekali. Kegagalan Playwright atau cancellation pada tindakan terminal hanya ditoleransi ketika shutdown telah dimulai. Error sejenis di luar shutdown tetap diteruskan agar kegagalan jaringan atau implementasi tidak tersembunyi.

## Live Progress Indicator dan integrasi modul

Menu Frontend QA dan Unified QA Workflow menampilkan status tahap serta aktivitas terakhir secara langsung pada worker terpisah agar terminal tetap responsif. Unified QA meneruskan reporter yang sama melalui Frontend, Website Discovery, Generic UAT, dan Authentication Discovery; menu mengakhiri siklus dengan Report Generation. Indikator tidak memakai persentase buatan. Website Discovery menampilkan jumlah halaman yang telah diperiksa tanpa total karena antrean crawl dapat bertambah; UAT dan Authentication Discovery menampilkan jumlah aktual kandidat yang diketahui. Status event bersama adalah `running`, `waiting`, `completed`, `failed`, dan `stopped`. `completed` berarti pemrosesan tahap selesai, sementara hasil QA disebutkan di aktivitas. Hasil Failed/Blocked/Timeout menghasilkan terminal `failed`; Access Restricted menghasilkan `stopped`. Kegagalan evidence verification atau penyimpanan report juga menghasilkan status gagal. Authentication Discovery tetap read-only dan tidak mencoba login. Menu belum menyediakan aksi pembatalan pengguna.

Mekanismenya reusable melalui `core.progress_tracking.ProgressReporter` dan `ProgressEvent`. Modul lain dapat memakai reporter yang sama tanpa membuat progress system baru:

```python
from core.progress_tracking import ProgressReporter

progress = ProgressReporter(ui_event_sink)
progress.emit("Website Discovery", "waiting", "Menunggu antrean halaman")
progress.emit("Website Discovery", "running", "Memeriksa halaman berikutnya", 3, None)
progress.emit("Website Discovery", "completed", "Discovery selesai; hasil QA: Passed", 8, None)
```

Gunakan `current`/`total` hanya dari pekerjaan nyata. Untuk pekerjaan yang totalnya belum diketahui, `total` harus `None`; UI menampilkan aktivitas tanpa persentase. `ui_event_sink` menerima satu `ProgressEvent` dan dapat meneruskannya ke queue UI. Terminal adalah status pemrosesan, bukan ringkasan keberhasilan QA: status kegiatan memuat hasil observasi, dan Failed/Blocked/Timeout tidak boleh ditandai completed. Unified Evidence Collection selesai hanya bila seluruh screenshot yang dihasilkan cocok dengan registry dan SHA-256; kegagalan verifikasi/report membuat terminal workflow gagal.

### Input masa berlaku otorisasi
Menu Kelola Otorisasi QA menerima tanggal dalam format `DD-MM-YYYY` dan waktu 24 jam `HH:MM` WIB (UTC+07:00). Contoh: `31-12-2026` dan `23:59`. Aplikasi mengonversi input tersebut ke ISO 8601 untuk penyimpanan dan validasi. Tanggal kedaluwarsa ditampilkan dalam format Indonesia, misalnya `31 Desember 2026, 23:59 WIB`.

## Update M3.2 — 24 November 2026
Launcher menyimpan kondisi AI_QA_DATA_DIR sebelum aplikasi berjalan dan mengembalikannya setelah aplikasi selesai. Jika variabel sebelumnya belum tersedia, launcher menghapusnya kembali. Pengaturan ini tidak mengubah environment variable Windows secara permanen.

### Direktori data eksternal aktif

Direktori data eksternal yang digunakan pada perangkat ini:

`<USER_HOME>\AI_QA_Assistant_Data`

Struktur yang sudah diverifikasi:
- `projects/`
- `logs/`

Data `projects/` dan `logs/` telah disalin dari direktori aplikasi ke direktori eksternal. Verifikasi SHA-256 menunjukkan:
- Projects: 57 file sumber, 57 file target, 0 missing, 0 extra, 0 mismatch.
- Logs: 10 file sumber, 10 file target, 0 missing, 0 extra, 0 mismatch.

Data sumber lama tetap dipertahankan.

### Cara menjalankan aplikasi

Gunakan launcher dari PowerShell pada folder utama aplikasi:

```powershell
.\run_ai_qa_assistant.ps1
```

Launcher:
- Menggunakan `.venv-scanner` jika tersedia, lalu `.venv`, kemudian Python sistem.
- Mengatur `AI_QA_DATA_DIR` ke `%USERPROFILE%\AI_QA_Assistant_Data`.
- Menjalankan `agent.py` dari folder aplikasi.
- Tidak menyimpan environment variable secara permanen di Windows.

### Verifikasi

- Launcher berhasil dijalankan.
- Python yang digunakan: `.venv-scanner\Scripts\python.exe`.
- Project Manager berhasil membaca 5 proyek terdaftar dari data eksternal.
- Aplikasi ditutup normal dengan exit code 0.
- Full regression: 280 tests, 3 skipped, 0 failed.

### Batasan yang belum selesai

- Namespace `client_id` belum diimplementasikan.
- Isolasi data antar-klien belum selesai.
- Struktur `clients/{client_id}/projects/` belum diterapkan.
- Migrasi `projects/` dan `logs/` sudah dilakukan, tetapi belum mencakup seluruh kategori data seperti backups dan test-results.
- Backup dan restore staging data eksternal telah diverifikasi pada M4; rollback produksi dan pemulihan bencana nyata belum diuji.

Jangan menyatakan isolasi multi-klien atau keseluruhan migrasi data sudah selesai.
