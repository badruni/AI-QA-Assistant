# AI QA Assistant — Portable Setup Guide

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
- Backup data sebelum melakukan perubahan besar.

## Status pengembangan terbaru

- Project Manager: selesai.
- Logging dan Sensitive Data Filter: selesai.
- Konfigurasi scanner: berhasil diuji.
- Homepage Inspection: selesai.
- WAF Detection: selesai dan diuji dengan simulasi lokal.
- Broken Images: selesai diimplementasikan; 3 test lulus.
- Broken Links Inspection: selesai diimplementasikan; 8 test lulus menggunakan server lokal.
- Regression test terbaru: 67 test lulus, 0 gagal.
- Homepage Inspection: 7 test lulus.
- HTTP Response Details: status code, status text, dan preview response body hingga 500 karakter.
- Website Discovery: selesai diimplementasikan; 6 test lulus.

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
- 6 test Website Discovery lulus.
- Seluruh 67 regression test lulus.

Article Listing merupakan inspeksi khusus yang kondisional, bukan persyaratan universal setiap website.

Catatan keamanan:
- Hindari mencatat exception mentah browser atau jaringan.
- Gunakan metadata aman untuk aktivitas dan hasil proses.
- Sensitive data filter merupakan perlindungan tambahan, bukan jaminan seluruh rahasia terdeteksi.
