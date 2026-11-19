# Feature 01 — Request Safety & Rate Limit

## Tujuan
Mengendalikan laju request HTTP dan menghentikan pemindaian setelah ambang respons HTTP 403 berturut-turut tercapai.

## Ruang lingkup
- `core/request_safety.py`: rolling window 60 detik, batas 1–10 request per menit, dan penghentian 403.
- `core/playwright_request_guard.py`: pengendalian request browser dan pembatasan origin.
- `modules/frontend_scanner.py`: penggunaan controller pada homepage, image, dan link inspection.

## Acceptance criteria
- RS-01: Batas request valid antara 1 dan 10 per menit.
- RS-02: Timestamp request dikelola dengan rolling window 60 detik.
- RS-03: Request di bawah batas memperoleh slot.
- RS-04: Request berikutnya menunggu sampai slot tersedia.
- RS-05: Request dapat berlanjut setelah menunggu.
- RS-06: Timestamp kedaluwarsa dihitung satu per satu, bukan berdasarkan menit kalender.
- RS-07: Request browser melewati PlaywrightRequestGuard.
- RS-08: Pemeriksaan link API memanggil controller sebelum request.
- RS-09: Respons non-403 mereset hitungan 403 berturut-turut.
- RS-10: Scanner berhenti ketika ambang 403 tercapai.
- RS-11: Tidak ada request baru setelah controller berhenti.
- RS-12: Pengujian tambahan berjalan tanpa mengakses website publik.

## Bukti dan batasan verifikasi
Test tambahan menggunakan fake clock agar penantian 60 detik dapat diverifikasi tanpa menunggu waktu nyata. Test guard menggunakan mock route; ini membuktikan urutan pemanggilan controller sebelum fetch, bukan pengukuran trafik jaringan nyata.

Pengujian lokal 403 sebelumnya membuktikan `inspect_links()` berhenti setelah tiga respons 403 dan tidak meminta endpoint sentinel. Hasil tersebut merupakan bukti skenario lokal, bukan jaminan semua kemungkinan situs.

## Belum dinyatakan selesai
Paket ini belum mengubah implementasi produksi. Integrasi end-to-end rate limit pada masing-masing `inspect_homepage()`, `inspect_images()`, dan `inspect_links()` masih memerlukan pengujian khusus bila dependency injection controller diperlukan. Fitur baru dapat diterima 100% setelah seluruh test yang relevan dan regression suite lulus serta dokumentasi ditinjau.

## Menjalankan test tambahan
```powershell
& ".\.venv-scanner\Scripts\python.exe" -m unittest tests.test_request_safety_delivery -v
```

## Menjalankan regression suite
```powershell
& ".\.venv-scanner\Scripts\python.exe" -m unittest discover -s tests -v
```