# AI QA Assistant - Project Setup Guide

## 1. Tujuan
AI QA Assistant adalah aplikasi black-box QA untuk menguji website client melalui URL frontend dan, jika diizinkan serta tersedia, akun CMS.
Tidak membutuhkan source code website.

Prinsip utama:
- Setiap client memiliki folder proyek terpisah.
- Hasil scan harus berdasarkan bukti nyata.
- AI tidak boleh mengarang hasil pengujian atau bug.
- Aktivitas pengujian harus mematuhi izin dan batas akses client.

## 2. Profil perangkat pengembangan
Perangkat saat ini:
- OS: Windows 10 Home Single Language 64-bit
- RAM: 8 GB
- Free storage saat pencatatan: 147 GB
- Python utama: 3.15.2 64-bit
- Python scanner: 3.14.10 64-bit
- Pip scanner: gunakan versi yang tersedia di environment
- Project path: C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant
- Environment utama: .venv
- Environment scanner: .venv-scanner
- Git: belum terpasang

Python utama dan Python scanner dipisahkan agar kompatibilitas dependensi browser automation lebih terjaga.

## 3. Instalasi Windows dari awal
1. Install Python yang sesuai dengan kebutuhan masing-masing environment.
2. Buka PowerShell.
3. Masuk ke root folder proyek.
4. Buat environment utama:
   py -3.15 -m venv .venv
5. Aktifkan environment utama:
   .\.venv\Scripts\Activate.ps1
6. Buat environment scanner:
   py -3.14 -m venv .venv-scanner
7. Aktifkan environment scanner:
   .\.venv-scanner\Scripts\Activate.ps1
8. Pastikan interpreter benar:
   python --version
   python -c "import sys; print(sys.executable)"
9. Instal dependensi scanner:
   python -m pip install -r requirements.txt
10. Instal browser Chromium:
   python -m playwright install chromium

Catatan:
- Perintah instalasi dependensi harus dijalankan saat .venv-scanner aktif.
- Pastikan requirements.txt menggunakan versi paket yang sesuai.
- Chromium perlu dipasang terpisah dari paket Python Playwright.
- Jangan menyalin folder .venv atau .venv-scanner antar laptop atau OS.
- Buat ulang environment pada setiap perangkat.
- Jika Python 3.14 belum tersedia, pasang terlebih dahulu sebelum membuat environment scanner.

## 4. Menjalankan aplikasi
Untuk aplikasi utama, dari root folder proyek dan setelah .venv aktif:
   python agent.py

Untuk pekerjaan scanner, aktifkan environment scanner:
   .\.venv-scanner\Scripts\Activate.ps1

Scanner diakses melalui menu Scanner pada aplikasi utama.

Environment .venv-scanner digunakan untuk pengembangan dan pengujian modul scanner. Jangan menjalankan file scanner secara langsung melalui entry point yang belum didokumentasikan.

## 5. Konfigurasi per client
Setiap client memiliki folder sendiri:
   projects/<project_id>/

Struktur folder client mencakup:
- project_config.json
- logs/
- documentation/
- reports/
- evidence/screenshots/
- evidence/attachments/

Atur URL frontend dan CMS berdasarkan informasi resmi dari client.
CMS boleh dinonaktifkan jika akses belum tersedia.

Jangan menyimpan password CMS, token, cookie, atau rahasia client dalam file konfigurasi maupun source code.

Proyek aktif saat ini:
- Project ID: 001
- Project name: Black Experience
- Frontend: https://www.blackxperience.com/
- CMS: belum tersedia
- Frontend scan: enabled
- CMS scan: disabled
- Pemeriksaan gambar: enabled
- Pemeriksaan link: enabled
- Batas request: maksimal 10 per menit
- Penghentian setelah 3 kali 403 berturut-turut

## 6. Keamanan dan WAF
- Hanya uji website dengan izin.
- Jangan bypass CAPTCHA, challenge, atau WAF.
- Jangan menyamarkan automation untuk menghindari proteksi.
- Gunakan request rate rendah.
- Hentikan pemeriksaan host jika terjadi 403, rate limit, atau IP restriction berulang.
- Klasifikasikan akses terblokir sebagai Blocked, Access Restricted, atau Inconclusive.
- Jangan menyebut akses terblokir sebagai bug tanpa bukti.
- Jangan mencatat password, token, cookie, API key, atau kredensial mentah.
- Jangan mencatat raw HTML, respons autentikasi, session header, atau exception browser/jaringan mentah.

Sensitive Data Filter adalah perlindungan tambahan berbasis pola, bukan jaminan bahwa semua rahasia dapat terdeteksi.

### WAF Detection
- Scanner mendeteksi indikator kuat halaman blokir berdasarkan judul dan teks halaman.
- Halaman blokir WAF yang mengembalikan HTTP 200 tetap diklasifikasikan sebagai Access Restricted jika indikator kuat ditemukan.
- Deteksi diuji menggunakan simulasi server lokal, termasuk indikator BOT_HEADLESS.
- Deteksi ini tidak melakukan bypass atau penyamaran automation.

## 7. Portabilitas
Pindahkan source code, konfigurasi yang diizinkan, test case, template, dan dokumentasi.

Jangan pindahkan:
- .venv/
- .venv-scanner/
- __pycache__/

Buat ulang environment dan instal ulang dependensi pada laptop tujuan.
Pasang Chromium melalui perintah Playwright setelah instalasi paket.

Periksa kebijakan perusahaan sebelum memindahkan data client, laporan, screenshot, atau evidence.
### Pengelolaan batch script

- Simpan seluruh batch script pengembangan dan perbaikan di folder `batch_scripts\`, bukan di root repository.
- Jalankan batch script dari root repository agar path relatif tetap sesuai.
- Simpan backup dan arsip di folder `backups\`.
- Jangan menghapus batch script lama atau arsip sumber sebelum memastikan penggantinya tersedia dan terverifikasi.

## 8. Status proyek
- Fondasi aplikasi: implemented
- System Log dan Project Log: implemented
- Sensitive Data Filter: implemented dan diuji
- Project Manager: implemented dan diuji
- Environment scanner: disiapkan
- Playwright: 1.65.1
- Chromium: berhasil dijalankan
- Frontend scanner module: tersedia dan dikembangkan bertahap
- Homepage Inspection: selesai dan diuji
- WAF Detection: selesai dan diuji dengan simulasi lokal
- Broken Images Inspection: selesai dan diuji
- Broken Links Inspection: selesai diimplementasikan dan diuji
- Regression test scanner: 61 test berhasil
- CMS automation: belum dibuat
- AI/Ollama integration: belum dibuat

## 9. Riwayat perubahan
2026-11-13:
- Membuat struktur folder awal.
- Menambahkan agent.py.
- Menambahkan config/project_template.json.
- Menambahkan core/result_status.py.
- Menambahkan dokumentasi portable awal.
- Menambahkan core/logger.py.
- Menambahkan System Log dan Project Log.
- Menambahkan Sensitive Data Filter.
- Menambahkan core/project_manager.py.
- Mengintegrasikan Project Manager ke agent.py.
- Membuat proyek Black Experience dengan ID 001.

## 10. Logging dan troubleshooting
- System Log disimpan di folder logs/ pada root proyek.
- Project Log disimpan di projects/<project_id>/logs/.
- Log menggunakan format yang mudah dibaca pengguna.
- INFO: aktivitas normal.
- WARNING: kondisi yang perlu diperhatikan.
- ERROR: kesalahan yang diketahui.
- Exception: kesalahan tak terduga beserta traceback teknis yang telah disaring.
- Log mendukung rotasi harian dan rotasi berdasarkan ukuran.
- Log lama tidak dihapus otomatis sampai kebijakan retensi disetujui.
- Jangan mencatat password, token, cookie, atau rahasia client.
- Periksa file log terbaru sesuai konteks System Log atau Project Log.
- Sertakan pesan error dan DETAIL TEKNIS yang sudah disanitasi saat meminta bantuan developer.

## 11. Sensitive Data Filter
Status: Implemented and tested.

Modul:
- core/security.py
- core/logger.py
- tests/test_security.py
- tests/test_logger_security.py

Data yang diuji:
- Password dan username.
- Access token dan refresh token.
- API key.
- Authorization dan Cookie.
- Kredensial pada URL.
- JWT.

Aturan:
- Jangan mencatat kredensial mentah atau sebagian nilainya.
- Jangan mencatat isi respons autentikasi atau HTML halaman secara mentah.
- Hindari memasukkan exception mentah browser atau jaringan ke log.
- Gunakan metadata aman untuk aktivitas dan hasil proses.
- Filter merupakan perlindungan tambahan, bukan jaminan seluruh rahasia terdeteksi.

## 12. Pengujian
Jalankan pengujian fondasi dengan environment utama aktif:
   python -m unittest tests.test_security tests.test_logger_security tests.test_project_manager -v

Hasil terakhir yang tercatat:
- 19 pengujian berhasil.
- 0 pengujian gagal.

Pengujian browser dilakukan terpisah setelah modul scanner tersedia.

## 13. Scanner environment
Environment scanner menggunakan:
- Python 3.14.10
- Playwright 1.65.1
- Chromium

Lokasi environment:
   .venv-scanner/

Verifikasi paket:
   python -m pip show playwright

Verifikasi browser:
   python -m playwright install --list

Tes Chromium:
   python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('Chromium:', b.version); b.close(); p.stop(); print('STATUS: OK')"

Hasil verifikasi terakhir:
- Chromium: 158.0.8127.18
- STATUS: OK

## 14. Riwayat perubahan konfigurasi scanner
2026-11-13:
- Menambahkan environment .venv-scanner dengan Python 3.14.10.
- Menginstal Playwright 1.65.1.
- Memasang browser Chromium.
- Memverifikasi Chromium berhasil dijalankan.
- Menambahkan Playwright ke requirements.txt.
- Menambahkan .venv-scanner/ ke .gitignore.

## 15. Riwayat pengembangan scanner
2026-11-16:
- Menyelesaikan Homepage Inspection.
- Menambahkan WAF Detection berbasis indikator konten halaman.
- Menambahkan test simulasi halaman WAF HTTP 200.
- Memverifikasi 5 test Homepage Inspection lulus pada tahap awal.
- Memverifikasi seluruh 48 regression test lulus pada tahap awal.

Pembaruan 2026-11-16:
- Mengimplementasikan Broken Images Inspection.
- Menguji gambar valid, HTTP 404, dan konten gambar tidak valid; 3 test lulus.
- Menambahkan HTTP Response Details pada Homepage Inspection: status code, status text, dan preview response body hingga 500 karakter.
- Memverifikasi 7 test Homepage Inspection lulus.
- Memverifikasi seluruh 53 regression test lulus.

Pembaruan 2026-11-17:
- Mengimplementasikan Broken Links Inspection pada frontend scanner.
- Memeriksa link internal menggunakan HTTP request tanpa mengikuti redirect.
- Mengklasifikasikan status HTTP: 2xx, 3xx, 4xx, 5xx, dan akses terbatas.
- Memeriksa anchor link dan menghindari pemeriksaan berulang untuk URL internal yang sama.
- Link eksternal tidak diperiksa otomatis.
- Request pemeriksaan tidak menggunakan cookie browser.
- Menghentikan pemeriksaan sesuai batas keamanan setelah threshold 403 tercapai.
- Menambahkan 8 test Broken Links Inspection menggunakan server lokal.
- Pada pembaruan sebelumnya, 61 regression test berhasil; 0 gagal.
## 16. Catatan pengembangan berikutnya

### Specialized Inspection: Article Listing (conditional)

Article Listing Inspection hanya dijalankan jika Website Discovery menemukan halaman atau komponen daftar artikel yang relevan. Ketiadaan fitur artikel pada website bukan bug.

Pemeriksaan daftar artikel akan mencakup:

- Pagination Inspection: memastikan perpindahan halaman benar-benar mengubah daftar artikel.
- Memastikan artikel pada Page 1, Page 2, Page 3, dan Page 5 sesuai dengan halaman yang dipilih.
- Memastikan indikator halaman aktif ikut berubah.
- Mendeteksi daftar artikel yang tidak berubah atau berisi duplikasi tidak wajar.
- Mendukung pagination dinamis/AJAX tanpa mengharuskan reload halaman.
- Article Filter Inspection: memeriksa filter Latest, Trending, Popular, dan Event.
- Dynamic Section Header Inspection:
  - Latest: Latest Article.
  - Trending: More Trending.
  - Popular: More Popular.
  - Event: Latest Event.
- Memastikan filter aktif, heading, dan daftar artikel sesuai pilihan.
- Memeriksa konsistensi pagination setelah filter berubah.
- Memeriksa error JavaScript selama interaksi.
- Mengumpulkan screenshot evidence sebelum dan sesudah interaksi.

Pengembangan berikutnya:
- Memastikan hasil pemeriksaan dan data setiap client terpisah.
- Menyimpan screenshot dan evidence secara terstruktur.
- Menyusun laporan bug berdasarkan bukti.
- Menambahkan pemeriksaan responsive dan interaksi.
- CMS automation dilakukan setelah akses dan izin tersedia.

Article Listing Inspection dikembangkan sebagai modul terpisah dari Broken Links Inspection.
## 17. Website Discovery

Pembaruan 2026-11-17:

- Mengimplementasikan modul `modules/website_discovery.py`.
- Menambahkan penemuan halaman internal berdasarkan tautan yang ditemukan.
- Membatasi discovery maksimum 20 halaman per pemindaian pada implementasi awal.
- Menggunakan PlaywrightRequestGuard dan RequestSafetyController yang sudah tersedia.
- Hanya mengunjungi URL dalam origin proyek yang diizinkan.
- Redirect lintas origin tidak diikuti.
- Mendeteksi heading, navigasi, link, button, form, input, gambar, dan kandidat card.
- Menghasilkan klasifikasi awal homepage, product, article, form, listing, dan unknown.
- Klasifikasi merupakan inferensi berdasarkan URL dan struktur DOM, bukan kepastian fungsi halaman.
- Menyimpan screenshot halaman yang berhasil diperiksa.
- Tidak mengirim formulir atau menekan tombol yang dapat mengubah data.
- Tidak melakukan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan lainnya.
- Akses terbatas dan kendala teknis tidak otomatis dianggap sebagai bug website.
- Menambahkan 13 test Website Discovery menggunakan server lokal.
- Memverifikasi seluruh 74 regression test berhasil; 0 gagal.

Catatan keamanan:
- Hindari mencatat exception mentah browser atau jaringan ke log.
- Gunakan metadata aman untuk aktivitas dan hasil proses.
- Filter sensitive data merupakan perlindungan tambahan, bukan jaminan bahwa seluruh rahasia terdeteksi.

Batas 20 halaman merupakan batas maksimum awal dan dapat dievaluasi berdasarkan kondisi website serta hasil pengujian lapangan.

## 18. Generic UAT Inspection

Generic UAT Inspection adalah tahap inspeksi DOM read-only setelah Website Discovery.

Cakupan tahap awal:
- Memeriksa tautan tanpa tujuan atau accessible name.
- Memeriksa tombol tanpa accessible name.
- Memeriksa input tanpa label yang terdeteksi.
- Memeriksa gambar tanpa atribut alt.
- Merangkum navigasi, formulir, kartu, tautan, tombol, input, dan gambar.
- Menyimpan screenshot di `projects/<project_id>/evidence/screenshots`.

Batasan dan keamanan:
- Hanya halaman hasil Website Discovery dengan status `Passed` yang diperiksa.
- Project ID hasil Discovery harus sama dengan konfigurasi proyek.
- Request menggunakan `PlaywrightRequestGuard` dan `RequestSafetyController`.
- Request eksternal dan redirect di luar origin proyek diblokir oleh guard.
- Tidak ada klik tombol, pengiriman formulir, atau pembacaan nilai input.
- Batas request per menit dan penghentian setelah batas HTTP 403 tetap berlaku.
- Indikasi struktur/aksesibilitas menggunakan status `Needs Review`, bukan vonis bug fungsional.
- Tahap ini belum membuktikan alur bisnis atau perilaku interaktif.
- Jika Website Discovery berstatus `Access Restricted`, Generic UAT tidak dijalankan.
- Accessible name tautan memperhitungkan teks alternatif gambar di dalam tautan.
- Input bertipe button, submit, reset, dan image tidak dihitung sebagai field yang membutuhkan label.
- Pemeriksaan accessible name/label merupakan heuristik awal, bukan implementasi penuh perhitungan nama aksesibel WCAG.

Menu aplikasi:
- Pilihan 5: Generic UAT Inspection.
- Pilihan 6: Keluar.


## Authentication Discovery

2026-11-17:
- Menambahkan deteksi indikasi autentikasi secara read-only.
- Pemeriksaan hanya dilakukan pada halaman Website Discovery berstatus PASSED.
- Sinyal yang diamati meliputi password field, OTP hints, pola form login,
  petunjuk social login, SSO, teks login, dan URL autentikasi.
- Tidak mengisi field, mencoba kredensial, klik tombol login, atau submit form.
- Tidak membaca nilai input, password, token, cookie, maupun session.
- `LOGIN_DETECTED` berarti ada indikasi pada DOM yang diamati, bukan verifikasi
  bahwa seluruh mekanisme autentikasi telah ditemukan.
- `NO_LOGIN_DETECTED` ber-confidence LOW dan bukan bukti bahwa website tidak
  memiliki halaman/member authentication.
- Jika tidak ada halaman yang dapat diperiksa atau akses dibatasi, hasilnya
  `NEEDS_REVIEW` atau `ACCESS_RESTRICTED`.


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

Evidence disimpan terpisah per proyek di `projects/<project_id>/evidence/`.
Modul `core/evidence_manager.py` menyediakan registrasi metadata evidence,
indeks `evidence_index.json`, path relatif, SHA-256, daftar evidence, dan
verifikasi integritas file. Jenis file yang didukung saat ini adalah screenshot
dan attachment. File harus sudah ada dan berada di dalam folder evidence proyek.
Metadata sensitif seperti password, token, cookie, credential, authorization,
dan API key disamarkan. Modul ini belum mengubah alur pembuatan screenshot
Discovery maupun Generic UAT; integrasi screenshot dilakukan setelah file berhasil dibuat.

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

## Document Manager

Document Manager menyimpan draft dokumen QA per proyek secara lokal di
`projects/<PROJECT_ID>/documentation/`. Jenis dokumen yang didukung adalah
`UAT`, `User_Guide_Web`, dan `User_Guide_CMS`.

Setiap dokumen memiliki manifest dan file JSON per versi. Versi yang telah
berstatus `APPROVED` dipertahankan; perubahan berikutnya dibuat sebagai versi
baru setelah versi aktif disetujui. Persetujuan dilakukan secara eksplisit
melalui fungsi `approve_document()` dan ditolak jika masih ada bagian yang
belum diverifikasi atau dokumen berstatus `BLOCKED`.

Document Manager pada tahap ini hanya mengelola konten JSON, metadata, status,
dan versi. Pembuatan DOCX, Print Preview Viewer, serta status dokumen final
akan ditambahkan pada tahap implementasi berikutnya. Informasi sensitif pada
key seperti password, token, cookie, dan credential disimpan sebagai
`[REDACTED]`; query dan fragment URL dihilangkan.

## Document Content Model

`core/document_content_model.py` menyediakan struktur konten dokumen yang
independen dari renderer. Model ini digunakan sebagai sumber data semantik
untuk Print Preview Viewer dan DOCX Renderer pada tahap berikutnya.

Jenis dokumen yang didukung: `UAT`, `User_Guide_Web`, dan `User_Guide_CMS`.
Setiap dokumen menggunakan section dan block terstruktur: heading, paragraph,
bullet/numbered list, table, image reference, dan page break. Pengaturan halaman
awal menggunakan A4 dengan orientasi portrait atau landscape dan margin dalam
milimeter.

Block gambar hanya menyimpan `evidence_id`, bukan path file bebas. Renderer
berikutnya harus menyelesaikan referensi tersebut melalui Evidence Manager dan
memverifikasi integritas evidence sebelum menampilkan atau menyisipkannya.
Model tidak membuat kesimpulan PASS/FAIL; status test case harus diberikan
berdasarkan hasil inspeksi dan evidence yang tersedia.

## Documentation Generator, A4 Preview, dan DOCX Renderer

Menu 7 menyediakan draft UAT, User Guide Web, dan User Guide CMS berdasarkan laporan inspeksi yang tersedia. Generator tidak mengarang langkah CMS atau hasil fungsional. UAT dan User Guide Web berstatus Needs Review sampai bagian yang belum terverifikasi diselesaikan; User Guide CMS berstatus Blocked bila laporan eksplorasi CMS belum tersedia.

A4 Print Preview menggunakan Tkinter dan bersifat read-only. DOCX Renderer menggunakan dependensi `python-docx` pada `.venv-scanner` dan hanya mengekspor versi berstatus APPROVED. Referensi gambar harus terdaftar di Evidence Manager dan hash SHA-256 diverifikasi sebelum dirender. File ekspor tidak menimpa DOCX versi yang sudah ada.

Alur: jalankan inspeksi yang relevan -> buat draft melalui menu 7 -> tinjau A4 Preview -> selesaikan bagian yang belum diverifikasi melalui proses QA -> setujui versi -> ekspor DOCX. Draft yang masih memiliki `unverified_sections` tidak dapat disetujui. Eksplorasi CMS belum diimplementasikan pada tahap ini, sehingga User Guide CMS tetap Blocked sampai sumber tersebut tersedia.

Catatan: Print Preview awal menyajikan representasi A4 berbasis halaman dan teks; kesamaan pagination/format dengan Microsoft Word belum dijamin dan harus diverifikasi secara visual pada dokumen nyata.
## Documentation Generator — struktur template

Generator membuat draft UAT, User Guide Website, dan User Guide CMS dari laporan/evidence proyek yang tersedia. Struktur UAT mengikuti bagian informasi dokumen, pendahuluan, skenario, catatan, dan persetujuan. Struktur CMS mengikuti ruang lingkup, version history, login, dashboard, serta pengelolaan menu/konten. User Guide Website memisahkan area pengunjung dan area member yang masih perlu diverifikasi.

Data yang tidak tersedia ditandai sebagai belum tersedia/Belum diuji/Needs Review. Status inspeksi DOM tidak dianggap sebagai hasil uji fungsional. CMS tanpa laporan eksplorasi tetap BLOCKED. Generator tidak menjalankan submit form, transaksi, atau perubahan data.
## Feature 01 — Request Safety & Rate Limit (2026-11-19)

Feature 01 memperkuat pengujian dan dokumentasi untuk implementasi Request Safety yang telah tersedia. Tidak ada perubahan pada kode implementasi produksi.

Implementasi yang ditinjau:
- `core/request_safety.py`: controller rolling window 60 detik dan penghentian berdasarkan jumlah HTTP 403 berturut-turut.
- `core/playwright_request_guard.py`: pengamanan request browser, pembatasan origin, dan pencegahan mengikuti redirect 3xx.
- `modules/frontend_scanner.py`: penggunaan controller pada alur homepage, image, dan link inspection.

File tambahan:
- `tests/test_request_safety_delivery.py`
- `docs/FEATURE_01_REQUEST_SAFETY.md`
- Batch script persiapan, penerapan, verifikasi, dan rollback di `batch_scripts/`.

Pengujian mencakup validasi konfigurasi, rolling window, penantian slot request, kedaluwarsa timestamp secara individual, guard request browser, controller sebelum API request link, reset hitungan 403 oleh respons non-403, penghentian saat threshold tercapai, dan pencegahan request setelah controller berhenti.

Hasil verifikasi 19 November 2026:
- Python syntax check: lulus.
- Feature 01 targeted test: 7 lulus.
- Existing Request Safety tests: 21 lulus.
- Full regression suite: 160 lulus, 1 skipped.
- Tidak ada test gagal.

Test skipped tidak dihitung sebagai test lulus. Test tambahan menggunakan fake clock dan mock Playwright; hasilnya memverifikasi perilaku unit/guard yang dicakup test, bukan throughput terhadap website publik. Pengujian threshold 403 dan redirect lintas origin sebelumnya menggunakan server lokal. Tidak ada dependency baru dan tidak ada commit/push pada sesi ini.

Status: pengujian dan dokumentasi Feature 01 selesai pada cakupan yang diverifikasi. Perubahan belum di-commit.
