# D1 — QA Lab Foundation

Tanggal: 26 November 2026

## Tujuan
Menambahkan fondasi navigasi Living QA Playground ke website MyDreamZone yang sudah ada, tanpa mengganti homepage, aset, atau interaksi yang telah berjalan.

## Perubahan
- Menambahkan tautan QA Lab ke navigasi desktop dan drawer mobile.
- Menambahkan landing page Living QA Playground.
- Menyediakan lima area tujuan: Normal Scenarios, Negative Test Lab, Accessibility Lab, Responsive Lab, dan Security Behavior Lab.
- Navigasi menggunakan URL hash sehingga dapat dibuka langsung melalui `#qa-lab` dan `#lab-*`.
- Saat QA Lab aktif, homepage disembunyikan; saat kembali ke navigasi situs, homepage tampil kembali.
- Menambahkan gaya responsive dan focus-visible untuk navigasi QA Lab.
- Mempertahankan carousel, modal galeri, toast, tema, drawer, konten homepage, dan aset yang sudah ada.

## Batasan D1
D1 hanya fondasi navigasi dan halaman lab. Belum ada skenario interaktif, endpoint simulasi, pemindaian, pengumpulan evidence, atau hasil pengujian otomatis. Ketersediaan halaman lab bukan bukti bahwa skenario pengujian sudah berjalan.

## Verifikasi setelah pemasangan
1. Pastikan homepage tampil normal di `/`.
2. Klik QA Lab di desktop; pastikan landing page tampil.
3. Buka `#lab-normal`, `#lab-negative`, `#lab-accessibility`, `#lab-responsive`, dan `#lab-security`; pastikan masing-masing tujuan dapat diakses.
4. Kembali ke `#home`; pastikan homepage tampil lagi.
5. Ulangi navigasi melalui drawer mobile.
6. Uji tema, carousel hero, modal galeri, dan tombol kembali ke atas.
7. Periksa Console browser; tidak boleh ada error JavaScript baru.

## File yang diubah
- `local_test_site/playground/index.html`
- `local_test_site/playground/assets/app.js`
- `local_test_site/playground/assets/styles.css`

## Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
- Kerjakan satu checkpoint dalam satu waktu dan tunggu hasil verifikasi sebelum melanjutkan.
- Jangan menganggap implementasi berhasil sebelum diuji.
- Pertahankan kode dan fitur yang sudah berfungsi; backup sebelum perubahan besar.
- Jangan menghapus data proyek, laporan, evidence, atau log.
- Pisahkan kode aplikasi dari data pengguna/klien.
- Jangan menyimpan password, token, cookie, atau kredensial dalam log.
- Jangan melakukan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.
- Hentikan pemindaian setelah batas 403 yang dikonfigurasi tercapai.
- Setiap laptop membuat virtual environment sendiri; jangan memindahkan venv.
- Perbarui dokumentasi untuk perubahan arsitektur, dependensi, dan cara menjalankan.
- Visi proyek: satu website MyDreamZone dengan lima lab QA terpisah; negative test harus terisolasi dan tidak merusak homepage normal.
