# AI QA Assistant — Checkpoint 25 November 2026

## 1. Lingkungan kerja aktif

- OS: Windows, PowerShell.
- Laptop kerja: laptop kantor.
- Folder aplikasi aktif:
  `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant`
- Folder arsip di luar repository:
  `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant_OLD`
- Python utama yang terakhir dilaporkan: 3.15.2.
- Virtual environment tidak boleh dipindahkan antarperangkat; setiap laptop membuat environment sendiri.

## 2. Aturan wajib kebersihan repository

Folder `AI-QA-Assistant` adalah **folder aplikasi/source code** yang akan:
1. di-backup dan di-versioning melalui GitHub;
2. menjadi sumber instalasi aplikasi;
3. digunakan untuk proses update, rollback, dan distribusi.

Karena itu, folder utama repository harus tetap bersih dan hanya berisi file yang memang merupakan bagian dari aplikasi, pengujian permanen, konfigurasi, serta dokumentasi yang diperlukan.

### Aturan script sekali pakai

- Jangan menyimpan script PowerShell/Python sekali pakai, patch sementara, generator, atau file kerja sementara di root `AI-QA-Assistant`.
- Script sekali pakai sebaiknya disimpan di lokasi sementara/Downloads di luar repository.
- Setelah digunakan, arsipkan script tersebut ke:
  `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant_OLD\one_time_scripts\`
- Jangan membuat folder `_OLD` di dalam repository aktif.
- Jika sebuah script perlu disimpan untuk audit, simpan salinannya di folder arsip eksternal tersebut.
- Jangan menghapus script sebelum hasil eksekusi dan kebutuhan arsip diverifikasi.

### Aturan backup dan snapshot perubahan

- Backup sebelum perubahan harus disimpan di folder eksternal:
  `C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant_OLD\`
- Gunakan subfolder berdasarkan milestone dan timestamp, misalnya:
  `AI-QA-Assistant_OLD\LP-3.4.1_Hero_Carousel\yyyyMMdd_HHmmss\`
- Jangan menaruh snapshot backup di dalam repository aktif.
- Data proyek, evidence, laporan, log, kredensial, dan virtual environment tetap berada di lokasi data masing-masing dan tidak boleh ikut Git.
- Sebelum Git backup/commit/push, verifikasi staged file list agar tidak ada script sekali pakai, backup, data pengguna, atau file sementara.

## 3. Kebijakan PowerShell Execution Policy

- Jika script lokal yang dibuat untuk proyek ditolak karena tidak ditandatangani, jangan mengubah Execution Policy permanen.
- Bila memang diperlukan dan script sudah diperiksa, gunakan izin sementara untuk proses PowerShell saat ini saja:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`
- `Unblock-File` hanya menghapus penanda file hasil unduhan; tindakan ini bukan pengganti pemeriksaan isi script.
- Tutup sesi PowerShell setelah pekerjaan selesai agar scope Process berakhir.
- Jangan menggunakan `Bypass` pada scope `CurrentUser` atau `LocalMachine` untuk mengatasi masalah ini.

## 4. Status Local QA Playground — MyDreamZone

Fitur resmi yang sedang dibangun:
**AI QA Assistant — Built-in QA Playground (MyDreamZone)**

Tujuan:
- Menjadi target uji lokal resmi untuk menguji kemampuan scanner AI QA Assistant.
- Termasuk dalam repository dan paket installer aplikasi.
- Tidak berjalan otomatis setiap aplikasi dibuka.
- Server hanya dijalankan saat diminta dan bind default ke `127.0.0.1`.
- Tidak mengekspos Playground ke jaringan publik.
- Tidak menggunakan aset/branding BlackXperience; MyDreamZone memiliki identitas orisinal.

### Status milestone visual

- LP-3.1: struktur awal Playground dibuat — selesai.
- LP-3.2: responsive layout — selesai setelah pemeriksaan mobile/tablet.
- LP-3.3: visual rebuild MyDreamZone — dipasang dan ditinjau.
- LP-3.3.3: perbaikan posisi gambar hero — selesai berdasarkan screenshot pengguna.
  - Desktop: kepala ayah sekarang terlihat jauh lebih utuh.
  - Tablet: layout tetap proporsional.
  - Mobile: komposisi tetap baik.
  - Perubahan posisi desktop menggunakan `object-position:center 18%`; aturan mobile tetap `center 48%`.
  - Backup CSS sebelum perubahan berada di lokasi backup yang dibuat oleh langkah tersebut; jangan menganggap lokasinya sudah dipindahkan kecuali diverifikasi.

### Komponen yang direncanakan

Playground perlu mencakup 56 kategori komponen yang sudah disepakati, termasuk header/navigation, hero/carousel, event, winner table, highlights, diskusi/komentar, reels/video, gallery, modal, pagination/load more, dan seluruh varian responsive.

Interaksi fungsional yang wajib disimulasikan/diuji meliputi:
- carousel next/previous/drag/swipe/indicator;
- sidebar expand/collapse/navigation;
- tooltip visibility/position/text;
- winner table horizontal scroll/row hover/data;
- accordion expand/collapse;
- comment reply/nested reply/scroll;
- like click/state;
- infinite scroll/loading/end;
- gallery image loading/layout/viewer;
- responsive grid columns/overflow/alignment;
- bottom navigation active state/navigation;
- modal open/close/overlay/keyboard.

Belum boleh mengklaim semua interaksi di atas sudah diimplementasikan atau lulus. Verifikasi satu per satu.

## 5. LP-3.4.1 — Hero Carousel: status No-Go

Tujuan tahap:
- Membuat hero carousel benar-benar mengganti gambar.
- Tombol Previous dan Next.
- Indikator slide yang dapat dipilih.
- Drag/swipe.
- Keyboard panah ketika area carousel difokuskan.
- Menggunakan gambar lokal yang sudah tersedia.

### Percobaan terakhir

Script:
`LP-3.4.1_Hero_Carousel.ps1`

Lokasi saat dicoba:
`C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant\LP-3.4.1_Hero_Carousel.ps1`

Pengguna menjalankan:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Unblock-File .\LP-3.4.1_Hero_Carousel.ps1
.\LP-3.4.1_Hero_Carousel.ps1
```

Execution Policy sementara berhasil mengizinkan script berjalan. Namun script berhenti pada pemeriksaan blok indikator HTML:

```text
Exception: ...\LP-3.4.1_Hero_Carousel.ps1:73
Blok indikator carousel HTML tidak cocok atau tidak unik. Tidak ada file yang diubah.
```

### Diagnosis berdasarkan urutan script

- Script memuat `index.html`, `app.js`, dan `styles.css`.
- Script memeriksa kecocokan tiga blok sumber sebelum membuat backup dan sebelum menulis perubahan.
- Pemeriksaan blok HTML indikator gagal pada baris 72–73.
- Pembuatan folder backup baru dilakukan setelah semua pemeriksaan, pada baris 82 dan seterusnya.
- Karena eksekusi berhenti pada baris 73, script tidak mencapai tahap backup maupun penulisan file.
- Dengan demikian, berdasarkan alur script yang diperiksa, tidak ada file aplikasi yang diubah dan backup LP-3.4.1 belum dibuat.
- Penyebab langsung: asumsi script bahwa HTML indikator adalah satu string persis tidak cocok dengan markup aktual. Jangan mengubah file aplikasi untuk menyesuaikan asumsi script sebelum markup aktual diperiksa.

### Langkah berikutnya — diagnosis saja, jangan patch dahulu

1. Periksa isi aktual bagian `.hero-visual` dan `.hero-dots` dari:
   `local_test_site\playground\index.html`
2. Periksa blok kode indikator `.dot` dalam:
   `local_test_site\playground\assets\app.js`
3. Ambil output terarah menggunakan `Select-String` atau pembacaan rentang file, bukan dump seluruh file.
4. Bandingkan markup aktual dengan pola yang dicari script.
5. Rancang ulang script agar memakai pemeriksaan yang sesuai dengan markup nyata, idempotent, membuat backup eksternal sebelum perubahan, dan melakukan rollback jika penulisan gagal.
6. Uji sintaks script sebelum diberikan kepada pengguna.
7. Simpan script revisi di luar root repository. Setelah selesai digunakan, arsipkan script ke `_OLD`.
8. Jangan melanjutkan ke milestone berikutnya sampai carousel benar-benar diuji pada browser.

**Status LP-3.4.1: NO-GO / belum ada perubahan aplikasi.**

## 6. Alur kerja milestone berikutnya

Setiap milestone wajib:
1. Menjelaskan tujuan dan ruang lingkup.
2. Memeriksa kondisi awal.
3. Membuat backup eksternal bila ada perubahan.
4. Menjalankan satu batch perubahan yang terukur.
5. Memverifikasi perubahan aktual dan fitur lama.
6. Memberikan hasil Go/No-Go berdasarkan bukti.
7. Memperbarui dokumentasi dan checkpoint bila ada perubahan arsitektur, dependensi, cara instalasi, atau cara menjalankan.
8. Menjaga root repository bebas dari script sekali pakai dan backup.

## 7. Aturan keamanan dan integritas QA

- Jangan mengarang hasil pengujian, bug, evidence, atau informasi website.
- Temuan harus berdasarkan bukti yang benar-benar diamati.
- Jangan menyimpan password, token, cookie, atau kredensial dalam log.
- Pisahkan data setiap klien.
- Jangan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan.
- Hentikan pemindaian setelah batas 403 yang dikonfigurasi tercapai.
- Gunakan target lokal atau target yang secara eksplisit diotorisasi.
- Jangan mengklaim test lulus tanpa output verifikasi.

## 8. Git dan instalasi

- GitHub: `https://github.com/badruni/AI-QA-Assistant.git`
- Branch utama: `master`.
- Root repository hanya berisi file aplikasi yang memang dibutuhkan untuk source control dan instalasi.
- Sebelum backup/commit/push:
  - periksa `git status`;
  - periksa staged file list;
  - pastikan script sekali pakai dan backup tidak ikut;
  - pastikan data proyek, evidence, laporan, log, kredensial, dan virtual environment tidak ikut.
- Gunakan Git Manager sesuai alur yang sudah tersedia.
- Jangan menganggap push berhasil sebelum output Git membuktikannya.

## 9. Instruksi saat melanjutkan sesi

Mulai dari diagnosis LP-3.4.1, bukan langsung mengulang script lama.

Perintah PowerShell harus siap salin dan diberikan satu checkpoint pada satu waktu. Tunggu output pengguna sebelum melanjutkan. Jika ada error, diagnosis dahulu. Jangan meminta pengguna mengedit kode manual bila dapat disediakan script otomatis yang aman.
