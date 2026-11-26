# AI QA Assistant — Requirements, Test Matrix & Technical Design
**Dokumen:** Living QA Playground / Frontend Component Scanner
**Tanggal:** 26 November 2026
**Status:** Draft desain berdasarkan keputusan Master Feature Inventory
**Ruang lingkup sesi:** Penetapan requirement dan desain teknis; belum ada perubahan source code.

---

## 1. Keputusan yang telah ditetapkan

| Topik | Keputusan | Implikasi |
|---|---|---|
| Accordion | Komponen terpisah, nomor 57 | Tidak digabungkan dengan Expand / Collapse (#35) |
| Sticky Elements | Cakupan pengujian Header / Responsive Header | Tidak menjadi komponen katalog terpisah |
| Recommended Extensions | Seluruh 16 extension masuk scope | Dievaluasi dan diimplementasikan bertahap, tanpa menghilangkan 57 komponen utama |

**Tujuan utama:** scanner mengenali sebanyak mungkin komponen frontend yang relevan dan menghasilkan skenario pengujian yang optimal berdasarkan bukti perilaku aktual website.

## 2. Prinsip desain

1. **Evidence first:** setiap deteksi harus menyimpan alasan dan bukti yang dapat diperiksa.
2. **No invented findings:** elemen yang tidak dapat dibuktikan tidak boleh dilaporkan sebagai komponen terdeteksi atau bug.
3. **Detection ≠ test result:** keberadaan komponen, keberhasilan interaksi, dan temuan bug adalah status yang berbeda.
4. **Confidence-aware:** deteksi memiliki tingkat keyakinan dan dapat berstatus `confirmed`, `probable`, atau `needs_review`.
5. **Progressive enhancement:** scanner tetap dapat memberi hasil parsial jika suatu teknik inspeksi tidak tersedia.
6. **Safe execution:** hanya menguji URL yang diizinkan, membatasi request, menghormati batas 403, dan tidak melewati CAPTCHA, WAF, atau mekanisme keamanan.
7. **Client isolation:** konfigurasi, log, laporan, dan evidence tiap klien terpisah.
8. **Portable and local-first:** proses inti berjalan lokal dan tidak memerlukan layanan berbayar untuk fungsi dasar.
9. **Regression retention:** pola website yang sudah direproduksi dan diverifikasi di QA Playground disimpan sebagai skenario regresi permanen.
10. **No destructive assumptions:** scanner tidak mengirim data formulir, membuat transaksi, menghapus data, atau melakukan aksi yang berdampak nyata tanpa izin dan konfigurasi eksplisit.

## 3. Katalog komponen

### 3.1 Baseline 56 komponen

Daftar baseline 56 komponen dari Master Feature Inventory tetap dipertahankan apa adanya. Accordion ditambahkan sebagai #57.

### 3.2 Komponen tambahan yang disetujui

| ID | Komponen | Batas identifikasi awal |
|---|---|---|
| 57 | Accordion | Kelompok panel/section yang dibuka-tutup melalui trigger; dibedakan dari expand/collapse generik berdasarkan pola struktur dan relasi trigger-panel |

### 3.3 Enam belas Recommended Extensions

| ID | Extension | Fokus deteksi dan pengujian |
|---|---|---|
| EXT-001 | Form & Input Controls | Input, textarea, select, checkbox, radio, button, label dan relasinya |
| EXT-002 | Form Validation States | Required, invalid, error message, valid state, disabled submit |
| EXT-003 | File Upload | File input, batas tipe/ukuran yang terlihat, state upload; tidak mengunggah file tanpa izin |
| EXT-004 | Search & Filter | Search field, filter control, hasil dan empty result |
| EXT-005 | Sorting Controls | Sort control dan perubahan urutan daftar |
| EXT-006 | Tabs | Tablist, tab, panel, selected state dan perpindahan panel |
| EXT-007 | Accordion | Tetap extension dalam daftar rekomendasi bila relevan, tetapi katalog komponen utamanya adalah #57; hindari duplikasi hitungan |
| EXT-008 | Breadcrumbs | Struktur navigasi hierarkis dan link ancestor |
| EXT-009 | Toast & Alert | Notifikasi sementara/permanen, role/status, dismiss behavior |
| EXT-010 | Skeleton Loading | Placeholder loading dan transisi menuju konten |
| EXT-011 | Empty State | Tampilan tanpa hasil/data dan pesan pendamping |
| EXT-012 | Error State | Tampilan error aplikasi/komponen; dibedakan dari HTTP error |
| EXT-013 | Video Player | Kontrol player, state playback dan aksesibilitas; tidak mengunduh media |
| EXT-014 | Lazy Loading | Loading saat mendekati viewport dan perubahan resource state |
| EXT-015 | Sticky Elements | Tetap diuji sebagai perilaku layout, terutama pada Header/Responsive Header; bukan komponen katalog terpisah |
| EXT-016 | Cookie Consent | Banner/dialog persetujuan, pilihan dan persistensi yang dapat diamati tanpa mengubah preferensi pengguna secara permanen |

**Catatan konsistensi katalog:** EXT-007 Accordion dan EXT-015 Sticky Elements tetap tercatat sebagai rekomendasi yang disetujui, tetapi implementasi harus merujuk ke komponen #57 dan cakupan Sticky Header agar tidak menghasilkan duplikasi komponen. Semua 16 extension tetap masuk scope evaluasi/pengujian.

## 4. Kebutuhan fungsional scanner

| ID | Requirement | Hasil yang diharapkan |
|---|---|---|
| FR-001 | Inspeksi halaman | Mengambil URL, title, status navigasi, viewport, dan metadata inspeksi |
| FR-002 | Inventaris DOM | Mengidentifikasi elemen semantik, atribut penting, relasi parent-child, dan kandidat komponen |
| FR-003 | Klasifikasi komponen | Memetakan kandidat ke 57 komponen dan 16 extension |
| FR-004 | Bukti deteksi | Menyimpan selector yang aman, ringkasan DOM, atribut relevan, screenshot, dan alasan klasifikasi |
| FR-005 | Confidence | Memberi tingkat keyakinan serta alasan; kandidat ambigu masuk review |
| FR-006 | Interaksi aman | Menguji klik, expand/collapse, tab, modal, navigasi, dan kontrol non-destruktif |
| FR-007 | Responsive inspection | Memeriksa layout pada viewport desktop, tablet, dan mobile yang dikonfigurasi |
| FR-008 | Accessibility checks | Memeriksa nama aksesibel, role, label, fokus keyboard, state dan struktur dasar |
| FR-009 | Negative scenarios | Menguji input kosong/tidak valid dan kondisi error hanya pada form/sandbox yang aman |
| FR-010 | Scenario generation | Memilih skenario berdasarkan komponen yang terdeteksi, risiko, dan prasyarat |
| FR-011 | Result separation | Memisahkan `detected`, `tested`, `passed`, `failed`, `blocked`, `not_applicable`, dan `needs_review` |
| FR-012 | Evidence/report | Menghasilkan laporan yang menghubungkan requirement, test case, hasil, dan evidence |
| FR-013 | Safety guard | Mematuhi allowlist origin, rate limit, batas 403, dan kebijakan redirect |
| FR-014 | Client isolation | Menyimpan seluruh hasil pada ruang data proyek/klien yang benar |
| FR-015 | Regression suite | Menyimpan skenario yang sudah diverifikasi untuk dijalankan kembali |
| FR-016 | Audit trail | Mencatat waktu, versi scanner, konfigurasi non-rahasia, dan hasil eksekusi |

## 5. Model deteksi yang disarankan

Pipeline konseptual:

1. **Page inspection** — navigasi ke halaman yang diizinkan dan merekam metadata.
2. **DOM collection** — mengumpulkan struktur dan atribut yang diperlukan, bukan seluruh data sensitif.
3. **Candidate extraction** — mencari kandidat melalui semantic HTML, ARIA, atribut, relasi DOM, pola visual/layout, dan perilaku.
4. **Component classification** — memberi satu atau lebih label kandidat beserta alasan dan confidence.
5. **Scenario planning** — memilih test case berdasarkan komponen, state, risiko, viewport, dan prasyarat.
6. **Safe execution** — menjalankan aksi yang diizinkan dan menghentikan aksi yang berisiko/destruktif.
7. **Evidence capture** — screenshot dan metadata hasil; redaksi data sensitif sebelum disimpan.
8. **Result analysis** — membandingkan actual result dengan expected result.
9. **Report and regression update** — membuat laporan; skenario baru masuk regression suite setelah diverifikasi.

### 5.1 Sinyal deteksi

- Semantic HTML: `button`, `nav`, `form`, `input`, `table`, `dialog`, `video`, dan elemen relevan lainnya.
- ARIA: `role`, `aria-label`, `aria-expanded`, `aria-selected`, `aria-controls`, `aria-live`, dan atribut state.
- Relasi: trigger-panel, label-control, tab-panel, parent-child, serta grouping.
- Atribut interaksi: `href`, `type`, `disabled`, `required`, `multiple`, `controls`, dan atribut terkait.
- Computed style/layout: position sticky/fixed, overflow, visibility, ukuran, dan breakpoint.
- Runtime behavior: perubahan DOM/state setelah aksi yang aman.
- Network metadata: status dan kegagalan request yang diamati dalam batas keamanan.

Tidak ada satu sinyal yang selalu cukup. Misalnya, elemen `div` dengan event click tidak otomatis membuktikan bahwa elemen tersebut adalah tab atau accordion.

### 5.2 Skema hasil deteksi konseptual

Setiap kandidat komponen sekurang-kurangnya menyimpan:
- `component_id`
- `component_name`
- `page_url`
- `element_reference` atau selector yang telah disanitasi
- `detection_signals`
- `confidence`
- `detection_status`
- `evidence_refs`
- `notes`
- `scanner_version`
- `detected_at`

Selector bukan identitas permanen. Laporan perlu menyimpan konteks agar perubahan DOM tidak membuat bukti lama tampak seolah-olah masih berlaku.

## 6. Strategi confidence dan status

| Status | Makna | Perlakuan |
|---|---|---|
| Confirmed | Bukti struktural/perilaku cukup kuat | Dapat menjadi input generator skenario |
| Probable | Ada beberapa sinyal, tetapi belum cukup untuk kepastian | Jalankan pemeriksaan tambahan atau tandai review |
| Needs review | Sinyal bertentangan/ambigu | Jangan membuat klaim pasti |
| Not detected | Tidak ditemukan bukti pada halaman dan kondisi yang diperiksa | Bukan bukti bahwa fitur tidak ada di seluruh website |

Confidence bukan skor kualitas website. Nilai confidence hanya menyatakan kekuatan bukti klasifikasi.

## 7. Matriks test scenario awal

Matriks berikut adalah kerangka baseline. Detail expected result harus disesuaikan dengan perilaku aktual website dan requirement klien; scanner tidak boleh mengasumsikan semua komponen harus berperilaku sama.

| Domain | Skenario inti | Variasi/negative | Evidence minimum |
|---|---|---|---|
| Navigation & Layout | Link/menu dapat diakses; navigasi sesuai tujuan | Menu tertutup, viewport sempit, link gagal | URL sebelum/sesudah, screenshot |
| Header & Sticky | Header tampil; sticky state sesuai layout | Scroll, breakpoint, overlap konten | Screenshot sebelum/sesudah scroll, computed position |
| Carousel/Slider | Next/prev/dot mengubah slide | Batas slide, keyboard, swipe, reduced motion bila relevan | Slide index/teks aktif, screenshot |
| Modal/Popup | Buka dan tutup melalui kontrol tersedia | Escape, backdrop, fokus, scroll lock | Screenshot, active element, state |
| Accordion #57 | Trigger membuka panel terkait | Tutup kembali, beberapa panel, keyboard | `aria-expanded`, panel visibility |
| Expand/Collapse #35 | Konten diperluas/diciutkan | State awal, keyboard, perubahan label | State sebelum/sesudah |
| Tabs EXT-006 | Tab berpindah ke panel yang tepat | Keyboard, selected state, panel tersembunyi | `aria-selected`, panel aktif |
| Form/Input EXT-001 | Kontrol terdeteksi dan dapat difokuskan | Required kosong, tipe input tidak sesuai | Metadata field, screenshot; nilai sensitif disamarkan |
| Validation EXT-002 | Validasi sesuai aturan yang terlihat | Kosong, format tidak valid, error clear | Pesan validasi, state field |
| File Upload EXT-003 | Kontrol upload terdeteksi | File type/size invalid hanya pada sandbox | Metadata input; jangan simpan file tanpa izin |
| Search/Filter EXT-004 | Query/filter memperbarui hasil | Query tanpa hasil, query kosong | Query tersanitasi, jumlah hasil |
| Sorting EXT-005 | Pilihan sort mengubah urutan | Dataset kosong/satu item | Urutan item sebelum/sesudah |
| Toast/Alert EXT-009 | Notifikasi muncul dan dapat dibaca | Dismiss, timeout | Role, teks tersanitasi, screenshot |
| Loading/Skeleton EXT-010 | Loading placeholder muncul lalu selesai | Timeout/error | Timing, state, screenshot |
| Empty/Error State | State tampil sesuai kondisi | Empty result, komponen gagal | Pesan, status komponen, screenshot |
| Video Player EXT-013 | Kontrol dan metadata player terdeteksi | Tidak autoplay; tidak mengunduh | Metadata kontrol dan state |
| Lazy Loading EXT-014 | Resource dimuat saat dibutuhkan | Scroll mendekati viewport | Resource state, screenshot |
| Cookie Consent EXT-016 | Pilihan consent terlihat dan operasional | Reject/accept bila tersedia; tidak mengubah permanensi tanpa izin | State dialog dan tindakan yang dipilih |
| Responsive | Komponen tetap dapat digunakan di viewport target | Overflow, overlap, clipping | Screenshot per viewport, ukuran viewport |
| Accessibility | Nama, role, label, fokus, state | Keyboard-only, missing label, focus loss | DOM snapshot terpilih, focus trace |

## 8. Optimasi pemilihan skenario

Generator skenario sebaiknya tidak menjalankan seluruh kemungkinan kombinasi secara membabi buta. Gunakan pendekatan bertingkat:

- **Tier 1 — Core smoke:** komponen utama, navigasi, error fatal, dan kontrol yang terlihat.
- **Tier 2 — Component behavior:** skenario interaksi spesifik untuk komponen yang terdeteksi.
- **Tier 3 — Responsive & accessibility:** viewport dan pemeriksaan aksesibilitas.
- **Tier 4 — Negative/security behavior:** hanya pada kondisi aman, sandbox, atau izin eksplisit.
- **Tier 5 — Regression:** seluruh skenario historis yang relevan dan masih valid.

Prioritas skenario dapat dihitung dari kombinasi dampak pengguna, frekuensi komponen, confidence deteksi, perubahan terbaru, dan biaya eksekusi. Bobot final harus ditetapkan setelah tersedia data hasil uji, bukan dikarang sekarang.

## 9. QA Playground — lima laboratorium

1. Normal Scenarios
2. Negative Test Lab
3. Accessibility Lab
4. Responsive Lab
5. Security Behavior Lab

Negative scenarios harus selalu tersedia di Negative Test Lab. Namun, skenario negatif tidak boleh merusak pengalaman normal pada homepage. Setiap reproduksi bug yang disengaja wajib diberi komentar `INTENTIONAL BUG REPRODUCTION`; kondisi negatif terencana diberi `NEGATIVE TEST`; placeholder normal diberi `NORMAL PLACEHOLDER`.

Pola website baru yang ditemukan saat pengujian nyata dapat ditambahkan ke Living QA Playground setelah:
- pola dan perilaku diamati,
- reproduksi lokal dibuat,
- expected behavior ditentukan,
- test case dan evidence diverifikasi,
- regression test lulus.

## 10. Arsitektur teknis tingkat tinggi

Komponen arsitektur yang direkomendasikan (konseptual, belum implementasi):

- **Scanner Orchestrator:** mengatur tahap inspeksi dan urutan modul.
- **Browser Session Manager:** lifecycle Playwright, context dan viewport.
- **Safety/Request Guard:** allowlist origin, rate limit, redirect policy, batas 403.
- **DOM Inspector:** metadata struktur, atribut, relasi dan kandidat.
- **Component Detector:** aturan deteksi per komponen dan extension.
- **Interaction Runner:** aksi non-destruktif dan verifikasi state.
- **Scenario Planner:** memilih skenario dari katalog dan hasil deteksi.
- **Evidence Manager:** screenshot, metadata, redaksi, referensi file.
- **Result Analyzer:** membandingkan actual/expected dan memberi status.
- **Report Generator:** laporan terstruktur dan ringkasan.
- **Regression Manager:** menyimpan dan menjalankan skenario regresi.
- **Project Data Boundary:** memastikan semua data terikat pada project/client ID.

### 10.1 Batas implementasi

Desain ini tidak mengharuskan seluruh modul dibuat sekaligus. Modul baru hanya ditambahkan ketika requirement dan test-nya jelas. Pertahankan modul scanner dan safety yang telah berfungsi. Sebelum perubahan arsitektur besar, buat backup dan jalankan regression test.

### 10.2 Data dan privasi

- Jangan merekam password, token, cookie, authorization header, atau nilai input sensitif.
- Masking dilakukan sebelum evidence/log disimpan, bukan hanya saat laporan ditampilkan.
- Jangan mengirim form, melakukan checkout, mengubah profil, atau menghapus data pada website nyata.
- Pisahkan direktori project, evidence, report, log, dan backup per klien.
- Simpan versi scanner, waktu, konfigurasi aman, dan hash evidence bila relevan.

## 11. Tahapan implementasi yang disarankan

| Tahap | Deliverable | Kriteria selesai |
|---|---|---|
| D1 | Requirements & test matrix disetujui | ID requirement dan cakupan skenario jelas |
| D2 | Component catalog machine-readable | 57 komponen + 16 extension, tanpa duplikasi semantik |
| D3 | DOM inventory & evidence schema | Kandidat dapat ditelusuri ke bukti |
| D4 | Detector baseline | Deteksi awal dan confidence diuji pada QA Playground |
| D5 | Interaction runner | Aksi aman dan verifikasi state berjalan |
| D6 | Scenario planner | Skenario dipilih berdasarkan hasil deteksi |
| D7 | Responsive/accessibility modules | Matriks viewport dan keyboard teruji |
| D8 | Negative/security lab | Skenario negatif aman dan terisolasi |
| D9 | Reporting & regression | Hasil dan evidence tersusun serta dapat diulang |

## 12. Risiko dan mitigasi

| Risiko | Mitigasi |
|---|---|
| Komponen custom tidak memakai semantic HTML | Kombinasikan sinyal DOM, ARIA, layout dan runtime behavior; tandai ambigu |
| False positive | Confidence, evidence, review state, regression test |
| False negative | Beberapa strategi deteksi dan katalog pola yang terus diperbarui |
| Interaksi berdampak nyata | Allowlist aksi, sandbox, larangan aksi destruktif default |
| Website dinamis | Tunggu state berbasis kondisi, bukan fixed sleep saja |
| Data sensitif tertangkap | Redaction sebelum persistensi |
| Banyak kombinasi skenario | Tiered execution dan risk-based selection |
| Perubahan website membuat selector usang | Simpan konteks evidence dan validasi selector sebelum replay |

## 13. Hal yang belum boleh dianggap selesai

- Deteksi otomatis 57 komponen dan seluruh extension belum diimplementasikan atau diverifikasi.
- Confidence scoring belum dikalibrasi dengan dataset hasil uji.
- Bobot prioritas skenario belum ditentukan.
- Integrasi penuh QA Playground dengan scanner belum dilakukan.
- Belum ada bukti bahwa scanner dapat mendeteksi seluruh pola komponen custom pada website nyata.

## 14. Standar Operasional Pengembangan (Wajib pada Setiap Checkpoint)

1. Satu checkpoint/batch kerja pada satu waktu.
2. Setiap chat pengembangan harus menghasilkan satu batch konkret: analisis, audit, verifikasi, perubahan kode, fitur, atau pengujian.
3. Berikan perintah PowerShell siap salin dan tunggu hasilnya sebelum melanjutkan.
4. Jangan menganggap langkah berhasil sebelum hasil diverifikasi.
5. Jika terjadi error, diagnosis dahulu sebelum mengubah kode.
6. Buat backup sebelum perubahan besar.
7. Pertahankan fitur yang telah berfungsi; jangan melakukan refactor yang tidak diperlukan.
8. Jalankan regression test yang relevan setelah perubahan.
9. Perbarui dokumentasi bila arsitektur, dependensi, konfigurasi, atau cara menjalankan berubah.
10. Jangan commit kecuali diminta secara eksplisit.
11. Jangan gunakan `git add .`, `git reset`, `git checkout`, `git clean`, atau force push.
12. Jangan memindahkan virtual environment antarperangkat.
13. Pisahkan data setiap klien dan jangan mencatat kredensial.
14. Jangan bypass CAPTCHA, Cloudflare, WAF, atau kontrol keamanan.
15. Hentikan pemindaian ketika batas 403 yang dikonfigurasi tercapai.
16. Jangan menghapus data, evidence, log, backup, atau laporan tanpa izin.
17. Setiap checkpoint wajib memuat status, bukti verifikasi, file yang berubah, risiko, dan langkah berikutnya.
18. Pertahankan visi **Living QA Playground**: pola baru yang ditemukan, direproduksi dan diverifikasi dapat menjadi skenario regresi permanen.

## 15. Checkpoint berikutnya

**Batch berikutnya yang direkomendasikan:** audit source code scanner saat ini untuk memetakan modul yang sudah ada terhadap arsitektur konseptual di dokumen ini.

Sebelum perubahan kode:
- verifikasi branch dan working tree,
- verifikasi lokasi proyek dan environment aktif,
- identifikasi modul scanner, safety guard, tests, dan struktur data,
- catat gap tanpa mengubah source,
- baru susun urutan implementasi berdasarkan kode yang benar-benar ada.

Tidak ada source code yang diubah dalam checkpoint desain ini.
