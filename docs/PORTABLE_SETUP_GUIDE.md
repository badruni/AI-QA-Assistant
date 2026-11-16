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
- Broken Links: belum dibuat.
- Homepage Inspection: 7 test lulus.
- HTTP Response Details: status code, status text, dan preview response body hingga 500 karakter.
- Regression test: 53 test lulus.

## Checkpoint lanjutan

Lanjutkan pengembangan pemeriksaan Broken Links pada frontend scanner.

Paket ini merupakan snapshot pengembangan, bukan rilis produksi.

## Catatan versi

Paket ini merupakan snapshot pengembangan, bukan rilis produksi.
