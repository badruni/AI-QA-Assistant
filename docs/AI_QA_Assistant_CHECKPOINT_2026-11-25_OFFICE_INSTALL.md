# AI QA Assistant — Checkpoint 25 November 2026
## Office Installation

### 1. Source
- Repository: https://github.com/badruni/AI-QA-Assistant.git
- Branch: master
- Commit: 5d742582afd68fd219a313f089e287053b30f571
- Source: C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant
- Folder lama: C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant_OLD
- Folder lama dipertahankan sebagai arsip. Belum dihapus.

### 2. Environment
- OS: Windows 10 Home Single Language 64-bit
- PowerShell: 7.7.0
- Python: 3.14.10 64-bit
- Git: 2.56.0.windows.4
- Virtual environment: .venv-scanner

### 3. Instalasi Kantor
Status: BERHASIL menurut output Installer.

Application:
C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant

Python:
C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant\.venv-scanner\Scripts\python.exe

Data:
C:\Users\RBZ-NB-0004\AI_QA_Assistant_Data

Chromium: Installed/verified
Regression: Executed
Installer: Selesai dengan sukses.

Catatan:
Output yang tersedia mengonfirmasi regression test telah dieksekusi,
tetapi tidak mencantumkan jumlah test passed, failed, atau skipped.
Smoke test aplikasi masih perlu dilakukan.

### 4. Rencana Pengembangan Berikutnya

#### I-6 — Git Manager Automatic Clone / Bootstrap
- Git Manager dapat melakukan clone repository GitHub secara otomatis.
- Pengguna laptop baru cukup menjalankan satu file Git_Manager.ps1
  untuk memulai proses instalasi.
- Tetap periksa Git dan Python sebagai prasyarat.
- Lindungi source lokal dan data pengguna yang sudah ada.
- Kembangkan dan uji terlebih dahulu di clone pengembangan.
- Jangan mengubah source kantor sebelum pengujian dan persetujuan.

#### I-7 — Installer Progress Indicator
Tambahkan indikator kemajuan untuk proses yang membutuhkan waktu:
- Memeriksa Python.
- Memeriksa Virtual Environment.
- Memasang Dependensi.
- Full Regression Test.

Ketentuan tampilan:
- Berikan indikator bahwa proses masih berjalan.
- Tidak perlu menampilkan seluruh skenario regression test.
- Tampilkan detail skenario yang gagal saja.
- Tetap tampilkan ringkasan akhir jumlah passed, failed, dan skipped.
- Jangan mengubah hasil atau perilaku pengujian hanya demi tampilan progress.

### 5. Langkah Verifikasi Berikutnya
1. Jalankan aplikasi melalui run_ai_qa_assistant.ps1.
2. Pastikan menu utama tampil.
3. Pastikan aplikasi menggunakan DataRoot eksternal kantor.
4. Lakukan smoke test fitur dasar.
5. Periksa Git status dan pastikan data eksternal tidak masuk ke Git.
6. Pertahankan folder AI-QA-Assistant_OLD sampai data lama dipastikan aman.

### 6. Keamanan dan Integritas
- Jangan menghapus folder OLD sebelum audit data selesai.
- Jangan menyimpan kredensial dalam log.
- Jangan memindahkan virtual environment antarperangkat.
- Backup sebelum perubahan besar.
- Update dokumentasi setiap ada perubahan arsitektur atau dependensi.

## 7. Prosedur Kerja Harian Laptop Kantor dan Rumah

### 7.1 Sebelum Pulang dari Laptop yang Sedang Digunakan
1. Periksa Git status.
2. Jalankan backup melalui Git Manager.
3. Lakukan commit terhadap perubahan source yang memang akan disimpan.
4. Jalankan git push ke GitHub.
5. Pastikan push berhasil dan HEAD sinkron dengan origin/master.

### 7.2 Setelah Berpindah ke Laptop Lain
1. Periksa Git status terlebih dahulu.
2. Jika terdapat perubahan terbaru dari laptop sebelumnya, lakukan git pull.
3. Pastikan perubahan berhasil disinkronkan.
4. Lanjutkan pekerjaan.

### 7.3 Setelah Pekerjaan Selesai
1. Buat backup melalui Git Manager.
2. Commit perubahan source jika diperlukan.
3. Lakukan git push.
4. Verifikasi sinkronisasi Git.

### 7.4 Jika Tidak Sempat Melakukan Git Pull
- Lanjutkan prosedur backup dan push seperti pada bagian 7.1 sebelum meninggalkan laptop.
- Jangan menggunakan force push untuk mengatasi penolakan push.
- Jika remote memiliki commit yang belum tersedia secara lokal, lakukan sinkronisasi dan selesaikan konflik terlebih dahulu.

### 7.5 Aturan Keamanan Sinkronisasi
- Jangan melakukan git pull sebelum memeriksa Git status.
- Jangan menghapus perubahan lokal yang belum di-backup.
- Jangan memasukkan data project, evidence, laporan, log, atau kredensial ke repository.
- Backup data eksternal secara terpisah dari source aplikasi.
- Pastikan push berhasil sebelum menganggap pekerjaan sudah tersimpan di GitHub.
