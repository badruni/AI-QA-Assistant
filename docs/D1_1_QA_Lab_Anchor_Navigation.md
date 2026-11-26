# D1.1 — QA Lab Anchor Navigation Correction

Tanggal: 26 November 2026

## Temuan berdasarkan verifikasi visual
QA Lab sebelumnya menggunakan href `#qa-lab`, tetapi section memiliki ID `qaLab`. Selain itu, route handler menyembunyikan elemen `#home` dan tidak memerintahkan viewport untuk berpindah ke section QA Lab. Akibatnya, pengguna tetap berada pada posisi scroll sebelumnya dan perlu menggulir manual.

## Koreksi
- Menyamakan ID section menjadi `qa-lab`.
- Menghapus perilaku menyembunyikan elemen `#home`; homepage tetap utuh.
- Setelah route QA Lab aktif, viewport diarahkan dengan smooth scroll ke landing page atau sub-lab yang diminta.
- Menambahkan scroll offset untuk menghindari section tertutup header sticky.
- Tidak mengubah komponen homepage atau skenario lab.

## Verifikasi yang masih diperlukan
Uji di browser lokal:
1. Klik QA Lab dari posisi atas homepage; viewport harus bergerak ke awal Living QA Playground.
2. Klik setiap kartu lab; viewport harus bergerak ke bagian lab yang dipilih.
3. Klik Kembali ke MyDreamZone; viewport harus menuju bagian homepage.
4. Pastikan homepage tetap utuh dan tidak ada error Console.

## Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)
- Satu checkpoint per giliran; tunggu verifikasi sebelum melanjutkan.
- Jangan menganggap perubahan berhasil sebelum diuji.
- Pertahankan kode dan fitur yang sudah berfungsi; backup sebelum perubahan besar.
- Jangan menghapus data proyek, laporan, evidence, atau log.
- Pisahkan kode aplikasi dari data pengguna/klien.
- Jangan menyimpan password, token, cookie, atau kredensial dalam log.
- Jangan melakukan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.
- Hentikan pemindaian setelah batas 403 terkonfigurasi tercapai.
- Setiap laptop membuat virtual environment sendiri; jangan memindahkan venv.
- Perbarui dokumentasi untuk perubahan arsitektur, dependensi, dan cara menjalankan.
- Visi: satu website MyDreamZone dengan lima lab QA terpisah; negative test terisolasi dari homepage normal.
