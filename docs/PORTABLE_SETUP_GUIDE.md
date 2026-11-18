# AI QA Assistant â€” Portable Setup Guide

## Tujuan
Panduan untuk memindahkan dan menjalankan AI QA Assistant pada laptop lain.

## Persyaratan awal
- Windows 10/11 64-bit untuk prosedur PowerShell ini.
- Python 3.14.x 64-bit.
- Koneksi internet saat instalasi dependensi dan browser.
- Ruang penyimpanan yang cukup.

## Isi paket
Paket berisi kode aplikasi, modul, konfigurasi template, dokumentasi portabel, pengujian, dan daftar dependensi.

Data klien, log, laporan, evidence, backup, serta virtual environment tidak disertakan.

## Instalasi pada laptop baru

1. Ekstrak ZIP ke folder kerja, misalnya:
   C:\AI-Projects\AI-QA-Assistant

2. Buka PowerShell pada folder tersebut.

3. Buat virtual environment utama:
   py -3.15 -m venv .venv

4. Aktifkan:
   .\.venv\Scripts\Activate.ps1

5. Jalankan pengujian:
   python -m unittest tests.test_security tests.test_logger_security tests.test_project_manager -v

6. Untuk scanner, buat environment terpisah:
   py -3.14 -m venv .venv-scanner

7. Aktifkan environment scanner:
   .\.venv-scanner\Scripts\Activate.ps1

8. Instal dependensi:
   python -m pip install -r requirements.txt

9. Instal Chromium:
   python -m playwright install chromium

10. Uji Chromium:
    python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('Chromium:', b.version); b.close(); p.stop(); print('STATUS: OK')"

## Catatan penting

- Jangan memindahkan folder .venv atau .venv-scanner antarperangkat.
- Buat ulang environment pada setiap laptop.
- Jangan memasukkan data klien ke paket distribusi kode.
- Jangan menyimpan password, token, cookie, atau kredensial dalam konfigurasi maupun log.
- Periksa konfigurasi proyek sebelum melakukan pemindaian.
- Gunakan hanya website yang telah mendapat izin pengujian.
- Simpan seluruh batch script pengembangan dan perbaikan di folder `batch_scripts\`, bukan di root repository.
- Jalankan batch script dari root repository agar path relatif tetap sesuai.
- Simpan backup dan arsip di folder `backups\`.
- Backup data sebelum melakukan perubahan besar.

## Status pengembangan terbaru

- Project Manager: selesai.
- Logging dan Sensitive Data Filter: selesai.
- Konfigurasi scanner: berhasil diuji.
- Homepage Inspection: selesai.
- WAF Detection: selesai dan diuji dengan simulasi lokal.
- Broken Images: selesai diimplementasikan; 3 test lulus.
- Broken Links Inspection: selesai diimplementasikan; 8 test lulus menggunakan server lokal.
- Regression test terbaru: 74 test lulus, 0 gagal.
- Homepage Inspection: 7 test lulus.
- HTTP Response Details: status code, status text, dan preview response body hingga 500 karakter.
- Website Discovery: selesai diimplementasikan; 13 test lulus.

## Checkpoint lanjutan

Website Discovery tahap pertama telah diimplementasikan dan diuji.

Pengembangan berikutnya:
- Memperkuat klasifikasi halaman dan validasi hasil discovery.
- Mengembangkan Generic UAT Inspection berdasarkan komponen yang ditemukan.
- Mengembangkan UI/UX Evaluation dengan evidence.
- Mengembangkan inspeksi khusus seperti Article Listing hanya jika relevan.
- Mengintegrasikan hasil discovery ke alur aplikasi dan laporan QA.

Paket ini merupakan snapshot pengembangan, bukan rilis produksi.


## Pembaruan Website Discovery

2026-11-17:
- Modul `modules/website_discovery.py` tersedia.
- Maksimum awal 20 halaman per pemindaian.
- Menggunakan request guard dan safety controller yang sudah tersedia.
- Penemuan halaman internal dan deteksi komponen DOM.
- Screenshot untuk halaman yang berhasil diperiksa.
- Tidak melakukan interaksi yang mengubah data atau bypass mekanisme keamanan.
- 13 test Website Discovery lulus.
- Seluruh 74 regression test lulus.

Article Listing merupakan inspeksi khusus yang kondisional, bukan persyaratan universal setiap website.

Catatan keamanan:
- Hindari mencatat exception mentah browser atau jaringan.
- Gunakan metadata aman untuk aktivitas dan hasil proses.
- Sensitive data filter merupakan perlindungan tambahan, bukan jaminan seluruh rahasia terdeteksi.

## Generic UAT Inspection

Generic UAT merupakan tahap inspeksi DOM read-only setelah Website Discovery.
Modul baru berada di `modules/generic_uat_inspection.py` dan test-nya berada
di `tests/test_generic_uat_inspection.py`.

Tidak ada aksi klik atau submit formulir. Screenshot disimpan di folder evidence
masing-masing proyek. Seluruh request tetap menggunakan request guard dan
safety controller yang sudah ada. Temuan awal dicatat sebagai `Needs Review`
dan perlu validasi lanjutan sebelum disebut bug. Jika Website Discovery berstatus
`Access Restricted`, tahap Generic UAT dilewati. Heuristik accessible name/label
bersifat awal dan bukan implementasi penuh perhitungan nama aksesibel WCAG.


## Authentication Discovery

2026-11-17:
- Modul `modules/authentication_discovery.py` menambahkan deteksi indikasi login
  secara read-only.
- Pemeriksaan tidak melakukan login, mengisi kredensial, klik, atau submit.
- Nilai password, OTP, token, cookie, dan session tidak dibaca atau disimpan.
- `NO_LOGIN_DETECTED` memiliki confidence LOW dan tidak membuktikan ketiadaan
  fitur autentikasi.
- Jalankan regression test dengan:
  `.\.venv-scanner\Scripts\python.exe -m unittest tests.test_authentication_discovery -v`


## Penyimpanan Laporan Inspeksi JSON

Hasil Generic UAT Inspection dan Authentication Discovery disimpan otomatis
sebagai file JSON terpisah di `projects/<PROJECT_ID>/reports/`. Setiap eksekusi
menghasilkan nama file unik sehingga laporan sebelumnya tidak ditimpa.
Laporan memuat tipe inspeksi, versi skema, waktu UTC, ID proyek, dan hasil
terstruktur. URL pada field URL disimpan tanpa query string maupun fragment.
Field yang namanya mengindikasikan password, token, secret, cookie, credential,
authorization, atau API key akan disamarkan. Hanya nama metrik inspeksi yang diizinkan secara eksplisit yang dikecualikan. Screenshot tetap berada di folder
evidence dan dirujuk dengan path relatif jika berada di dalam folder proyek.
Jika penyimpanan laporan gagal, hasil inspeksi tetap ditampilkan dan aplikasi
memberikan peringatan.

## Evidence Management

Evidence Management menyimpan metadata evidence per proyek pada
`evidence/evidence_index.json`. File evidence tetap berada di folder proyek dan
tidak dipindahkan oleh modul registrasi. Indeks mencatat ID unik, sumber, jenis,
waktu UTC, path relatif, ukuran file, SHA-256, URL halaman yang telah disanitasi,
dan relasi finding bila tersedia. Jalankan pengujian dengan:
`python -m unittest tests.test_evidence_manager -v`.

## Evidence Management ? screenshot registry integration

- Screenshot hasil Frontend Homepage Scanner, Website Discovery, dan Generic UAT didaftarkan ke `evidence/evidence_index.json` melalui `core/evidence_manager.py`.
- File screenshot tetap disimpan di `evidence/screenshots/`; integrasi tidak memindahkan atau menghapus evidence yang sudah ada.
- Registrasi dilakukan hanya setelah screenshot berhasil dibuat. Kegagalan pencatatan tidak menggagalkan proses inspeksi dan hanya menghasilkan peringatan generik tanpa detail exception.
- Metadata menyimpan sumber inspeksi dan URL halaman yang disanitasi oleh Evidence Manager.

## Evidence Viewer

Evidence Viewer dapat dibuka dari menu utama aplikasi. Viewer bekerja pada proyek
aktif; jika belum ada proyek aktif, pengguna diminta memilih proyek terlebih dahulu.
Fitur meliputi daftar evidence, detail metadata, membuka screenshot menggunakan
aplikasi bawaan Windows, dan verifikasi integritas SHA-256.

Viewer hanya membaca indeks dan file evidence. Viewer tidak menghapus, memindahkan,
atau mengubah evidence. Path file divalidasi agar tetap berada di dalam folder
evidence proyek. Attachment ditampilkan sebagai metadata dan tidak dibuka otomatis.

### Membuka screenshot pada Windows

Evidence Viewer mencoba membuka screenshot melalui asosiasi aplikasi default Windows.
Jika pemanggilan langsung menghasilkan WinError 1155, aplikasi meneruskan permintaan
melalui Windows Explorer agar asosiasi aplikasi modern (misalnya Paint 3D) tetap
digunakan. Aplikasi tidak memaksa Paint klasik dan tidak mengubah asosiasi file Windows.
