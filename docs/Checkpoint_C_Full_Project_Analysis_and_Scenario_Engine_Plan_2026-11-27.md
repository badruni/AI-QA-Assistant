# Checkpoint C — Full Project Analysis & Scenario Engine Plan

Tanggal analisis: 27 November 2026
Source snapshot: `a254990bfc622f32d1199b0453eafdcd526b594f` (`master`)
Package: `AI_QA_Assistant_Checkpoint_C_Analysis_20261127_103012.zip`

## 1. Integritas paket dan batas analisis

- ZIP berhasil dibuka dan diuji: `testzip()` = OK.
- 134 entries: 124 committed source/documentation files, 9 allowlisted reference artifacts, dan 1 package manifest.
- Tidak ditemukan `.git`, `.venv`, `.venv-scanner`, `__pycache__`, backup, log, evidence, report, atau DataRoot dalam ZIP.
- Manifest menyatakan 124 tracked files dan 9 reference artifacts; jumlah tersebut konsisten dengan isi arsip.
- Source yang dianalisis adalah snapshot commit `a254990...`, bukan working tree yang mungkin berubah setelah ZIP dibuat.
- Tidak ada source aplikasi yang diubah selama analisis ini.

## 2. Ringkasan arsitektur aktual

### Aplikasi utama
- `agent.py` menjadi entry point/menu utama.
- `core/` menyediakan project/data path, authorization, path safety, request guard, evidence, report, logging, progress, dan document management.
- `modules/frontend_scanner.py` menangani homepage, image, link inspection dan frontend QA workflow.
- `modules/generic_uat_inspection.py` menangani inspeksi UAT generik.
- `modules/qa_workflow.py` mengorkestrasi workflow QA.
- Test suite Python tersedia pada `tests/`.

### Living QA Playground
- UI utama: `local_test_site/playground/index.html`.
- Styling: `local_test_site/playground/assets/styles.css`.
- Katalog, skenario, executor, hasil dan JSON export berada bersama di `local_test_site/playground/assets/app.js`.
- Server lokal: `local_test_site/playground_server.py`, loopback-only `127.0.0.1:8000`.
- Server saat ini merupakan static-file server; belum ada custom endpoint Security Behavior untuk HTTP 401/403/500/redirect.
- Tidak ditemukan kontrak API terverifikasi antara browser Workbench dan Python scanner. Dokumen referensi juga secara eksplisit menunda integrasi tersebut.

## 3. Baseline Scenario Engine yang benar-benar ada

### Catalog
- 57 component records unik.
- Source status: 21 `implemented`, 19 `partial`, 17 `not_implemented`.
- Category: navigation 11, content 31, interaction 10, responsive 5.
- Setiap record memiliki selector candidate.
- Selector ownership index dan penanda ambiguous sudah ditambahkan pada Checkpoint B.
- Runtime detection, source expectation, dan behavior status dipisahkan.
- CMP-033 hover scan memeriksa CSS `:hover`; status behavior dan keyboard equivalent tetap `not_tested`.

### Scenario registry
- 15 fixed smoke/simulation scenarios:
  - Normal: 5
  - Negative: 3
  - Accessibility: 3
  - Responsive: 2
  - Security: 2
- Ditambah 57 DOM candidate scan scenarios, satu per komponen.
- Total registry: 72 skenario.
- `Run safe checks` menjalankan 70 skenario non-security (57 DOM scans + 13 fixed non-security).
- Security scenarios tidak termasuk Run safe checks.
- Hasil disimpan di memory browser untuk sesi aktif dan dapat diekspor sebagai JSON schema 2.0.
- Tidak ada persistence lintas reload, screenshot capture otomatis, evidence index server-side, import/export regression baseline, atau regression comparison terhadap run terdahulu.

### Batas interpretasi
- DOM candidate scan hanya menguji keberadaan selector kandidat.
- `passed` untuk component scan berarti expectation inventory cocok; bukan bukti perilaku komponen lulus.
- Accessibility dan responsive checks yang ada adalah smoke checks dasar, bukan audit menyeluruh.
- Security 403 adalah simulasi loop lokal; bukan respons HTTP 403 aktual dan bukan security assessment.

## 4. Temuan gap dan risiko prioritas

### C-01 — Mapping skenario ke komponen tidak akurat (High)
Fixed scenarios menghubungkan beberapa skenario ke component ID yang tidak relevan:
- `SCN-N-002` QA Lab route -> `CMP-008` Floating Go to Top.
- `SCN-N-003` Workbench tabs -> `CMP-009` Hero Banner.
- `SCN-N-004` Theme toggle -> `CMP-004` Expandable Sidebar.
- `SCN-N-005` Gallery dialog -> `CMP-006` Bottom Navigation.
- `SCN-X-001` Empty search -> `CMP-009` Hero Banner.
- `SCN-X-002` threshold validation -> `CMP-010` Image Carousel.
- `SCN-A-002/A-003` Workbench tabs/controls -> `CMP-009` Hero Banner.
- `SCN-R-002` Workbench viewport -> `CMP-009` Hero Banner.
- Security simulation records -> `CMP-010` Image Carousel.

**Arah perbaikan:** mapping harus menunjuk komponen yang benar, extension ID yang disetujui, atau `null`/system-level jika memang bukan pengujian komponen katalog. Jangan memaksakan component_id.

### C-02 — Scenario executor tidak memiliki lifecycle contract tunggal (High)
- Executor berupa satu switch statement yang tertanam dalam `qaRunScenario`.
- Registry memiliki metadata `preconditions`, `steps`, `expected_result`, tetapi executor tidak memvalidasi preconditions secara generik.
- `qaRunScenario` tidak memiliki contract validator yang memastikan ID, lab, status, component reference, dan executor tersedia sebelum run.
- Scenario tanpa executor baru akan menjadi `blocked`, tetapi integritas registry belum diperiksa sebelum ditampilkan/dijalankan.

**Arah perbaikan:** validasi registry saat bootstrap; definisikan hasil standar dan alasan `blocked`; pastikan exception tercatat sebagai failed dengan bukti aman.

### C-03 — Beberapa checks hanya memeriksa keberadaan, bukan perilaku yang namanya dijanjikan (High)
- Theme scenario hanya memeriksa tombol ada/enabled, bukan mengubah tema dan memulihkannya.
- Gallery dialog scenario hanya memeriksa elemen dialog dan tombol close ada, bukan membuka/menutup dialog.
- QA Lab route scenario hanya memeriksa section ada, bukan menguji route/scroll.
- Navigation scenario memeriksa accessible name saja.
- Tab scenario hanya memeriksa atribut `aria-selected` ada, bukan nilai/semantik/perpindahan panel.
- Responsive check hanya memakai viewport aktif; tidak melakukan sweep desktop/tablet/mobile.
- Workbench width check tidak menguji clipping, overlap, atau konten di luar bounding box.

**Arah perbaikan:** nama skenario, langkah, expected result dan implementasi executor harus sejalan. Gunakan label smoke/structural check bila memang hanya memeriksa keberadaan.

### C-04 — Mutasi UI dan reset sesi belum simetris (High)
- Empty search scenario mengubah nilai input menjadi kosong dan tidak memulihkan nilai sebelumnya.
- Tab scenario memindahkan pane ke catalog lalu overview; bila terjadi exception di tengah, state awal tidak dijamin dipulihkan.
- Clear results mereset scenario records dan `qaResults`, tetapi tidak mereset detection/expectation state pada component records.
- Clear results dapat membuat `EV-1` digunakan kembali; ID evidence bukan identifier unik lintas sesi.
- Output simulator 403 tidak dibersihkan bersama hasil lain.

**Arah perbaikan:** tiap executor harus memiliki cleanup/finally atau state snapshot/restore; reset harus memiliki definisi yang jelas (results-only vs full session reset); evidence ID unik per session.

### C-05 — Evidence export perlu kontrak privasi dan integritas yang lebih kuat (High)
- Export mencakup `location.href` mentah, yang dapat mengandung query/hash sensitif pada lingkungan selain localhost.
- Evidence references `EV-n` adalah label internal; tidak menunjuk artefak screenshot/file yang nyata.
- Export tidak memiliki validasi schema sebelum dibuat.
- Export mengikutsertakan object catalog/scenario runtime penuh, sehingga hasil mutable dari sesi dapat tercampur dengan metadata definisi.
- Object URL langsung di-revoke setelah `a.click()`; lifecycle download perlu dibuat aman.

**Arah perbaikan:** sanitasi URL (origin/path saja, tanpa query/fragment), pisahkan definition snapshot dan execution records, schema version yang tervalidasi, session ID dan unique execution IDs, serta jelaskan bahwa evidence saat ini adalah JSON metadata kecuali screenshot benar-benar tersedia.

### C-06 — Regression runner belum menjadi regression management (High)
- Tidak ada baseline run yang disimpan dan dibandingkan.
- Tidak ada import/restore regression suite.
- Tidak ada perbedaan antara first run dan regression run.
- Results hanya hidup selama page session.
- Tidak ada persisted run history atau regression delta.
- Clear session menghapus seluruh execution history dari memory.

**Arah perbaikan:** untuk checkpoint ini bangun session-safe run manifest dan JSON export/import yang tervalidasi, tetapi jangan membuat server database atau penyimpanan lintas klien tanpa desain terpisah. Regression comparison antar-run dapat memakai file JSON yang dipilih secara eksplisit pada browser lokal, jika user menyetujui file import. Jika tidak, tandai persistence/comparison sebagai tahap berikutnya.

### C-07 — Security simulation label berpotensi disalahartikan (Medium)
- Loop 403 menghitung integer lokal; tidak ada HTTP request atau respons 403.
- UI menuliskan “simulated 403”, tetapi ringkasan/hasil harus terus menekankan `simulation_only`.
- Tidak boleh disambungkan ke endpoint eksternal atau digunakan sebagai pengganti scanner request guard.

**Arah perbaikan:** pertahankan sebagai simulasi lokal; bukti mencatat `simulation_only: true`, `network_requests: 0`, configured threshold dan count.

### C-08 — Katalog dan registry tertanam dalam app.js (Medium)
- `app.js` sekitar 67 KB, termasuk komponen, scenario definitions, detector, evaluator, renderers, executor, result handling, export dan event wiring.
- Tidak ada JSON schema atau validator mandiri untuk katalog/registry.
- Perubahan data dan executor bercampur dalam satu file.

**Arah perbaikan:** pada batch C, lakukan pemisahan logis lewat fungsi/helper internal dan validasi schema ringan tanpa menambah dependency. Pemecahan file eksternal dapat ditunda bila menambah kompleksitas packaging/server.

### C-09 — Automated regression untuk Scenario Engine sangat terbatas (High)
- Test khusus Checkpoint B berisi 7 static tests untuk katalog dan detector.
- Belum ada test khusus untuk 15 fixed scenarios, registry total 72, mapping component IDs, executor contract, cleanup, reset, export schema, privacy sanitization, atau security simulation invariants.
- `node --check` hanya menguji sintaks, bukan perilaku.
- Full Python suite 287 tests (3 skipped) telah dijalankan pengguna dengan `.venv-scanner` dan DataRoot pada 27-Nov; ini membuktikan regresi Python saat itu, bukan browser Scenario Engine.

**Arah perbaikan:** tambah unit/static tests untuk invariants registry dan engine; browser verification tetap diperlukan untuk perilaku DOM dan interaksi.

## 5. Artefak referensi: validitas dan konflik versi

- Sembilan artefak referensi berhasil dibaca.
- Semua ZIP referensi lolos pemeriksaan integritas.
- ZIP D2–D7 dan Workbench Fix berisi frontend yang berbeda dari source commit `a254990`; keduanya lebih lama/berbeda dan tidak boleh dipasang ulang secara langsung.
- Dua script `Full_Component_Catalog_Scenario_Engine...ps1` menimpa tiga file frontend dan dokumen dengan payload base64. Payload-nya berbeda dari source commit saat ini. Script ini hanya referensi historis, bukan installer yang aman untuk dijalankan terhadap source terkini.
- Perbedaan file tidak berarti artefak historis salah; hanya berarti commit Git terbaru menjadi sumber kebenaran dan ZIP/PS1 lama tidak boleh menimpa source terkini.
- ZIP D1 dan QA Playground source awal berguna untuk sejarah perubahan, bukan untuk restore tanpa diff dan persetujuan.

## 6. Rekomendasi scope Checkpoint C

**Nama:** Scenario Engine Integrity, Execution Lifecycle & Evidence Contract.

### Batch C1 — Registry integrity and scenario contract
1. Validasi 57 komponen dan 72 skenario: ID unik, field wajib, lab valid, component reference valid atau explicitly null/system-level, executor coverage.
2. Perbaiki mapping scenario-component yang salah.
3. Tambahkan test untuk registry count, uniqueness, lab counts, mapping dan coverage.
4. Definisikan status standar: `not_run`, `passed`, `failed`, `blocked`, `needs_review`, `not_applicable`; jangan menyamakan expectation match dengan behavior pass.
5. Pisahkan DOM inventory scan result dari behavioral scenario result pada data model dan ringkasan.

### Batch C2 — Safe execution lifecycle
1. Validasi input skenario sebelum executor berjalan.
2. Tambahkan state snapshot/cleanup untuk input, tab/pane, theme dan fixture state.
3. Pastikan cleanup berjalan walau executor gagal.
4. Tambahkan full reset yang mengembalikan component detection/expectation state, scenario state, output simulator dan result list ke baseline.
5. Gunakan session ID + execution ID unik, bukan EV counter yang dapat berulang.
6. `Run safe checks` harus menampilkan rencana jumlah skenario, mengecualikan security secara eksplisit, dan melaporkan blocked/fail counts.

### Batch C3 — Evidence/export and regression interchange
1. Definisikan JSON export schema versi baru dan validasi payload sebelum download.
2. Pisahkan catalog/scenario definitions dari immutable execution result snapshots.
3. Sanitasi URL; jangan ekspor query string, fragment, credential atau sensitive input.
4. Tandai metadata-only evidence secara eksplisit; jangan mengklaim screenshot jika tidak ada.
5. Perbaiki download lifecycle.
6. Tambahkan export integrity tests dan, bila disetujui, import JSON baseline yang hanya membaca file pilihan pengguna dan memvalidasi sebelum digunakan. Tidak ada upload/network transfer.
7. Tidak membuat persistence server-side atau data klien baru dalam checkpoint ini.

### Batch C4 — Browser acceptance & docs
1. Verifikasi semua 72 records tampil dan 70 safe checks dijalankan sesuai klasifikasi.
2. Uji setidaknya satu skenario dari tiap lab; pastikan Security tetap simulasi lokal.
3. Uji state restore ketika skenario sukses dan ketika sengaja menghasilkan error fixture.
4. Uji export JSON dan inspeksi isi hasil.
5. Uji homepage, carousel, theme, drawer, gallery modal dan route QA Lab tetap berjalan.
6. Perbarui dokumen Scenario Engine, test matrix dan checkpoint.
7. Jalankan test Python targeted dan full suite memakai `.venv-scanner` + `AI_QA_DATA_DIR`; jalankan `node --check` jika Node tersedia.

## 7. Tidak termasuk Checkpoint C (kecuali diputuskan terpisah)
- Implementasi interaksi untuk semua 57 komponen.
- Implementasi semua 16 extensions.
- CMS CRUD/authentication workflow.
- Custom HTTP Security Behavior endpoints atau penetration testing.
- Python Playwright scanner integration/API.
- Screenshot capture automation dan pixel diff.
- Multi-client database, cloud sync, server persistence.
- Menambah dependency baru.

Pekerjaan tersebut memerlukan checkpoint/desain tersendiri agar batch C tetap terukur dan aman.

## 8. Acceptance criteria yang diusulkan

- [ ] Registry 57 komponen + 72 skenario lolos validasi tanpa ID duplikat atau referensi komponen salah.
- [ ] Seluruh skenario memiliki executor atau status `blocked`/`not_applicable` yang eksplisit.
- [ ] Tidak ada skenario smoke yang mengklaim interaksi jika hanya memeriksa keberadaan elemen.
- [ ] UI state dikembalikan setelah tiap scenario run, termasuk ketika executor gagal.
- [ ] Full reset mengembalikan seluruh status ke baseline.
- [ ] `Run safe checks` mengecualikan security dan menampilkan hasil per status.
- [ ] Execution IDs unik; evidence references tidak bertabrakan setelah reset.
- [ ] Export JSON tervalidasi dan tidak memuat query/hash URL atau nilai sensitif.
- [ ] Security simulator menandai simulation-only dan zero network requests.
- [ ] Existing Playground functionality tidak regresi.
- [ ] Test baru dan full regression suite lulus.
- [ ] Dokumentasi dan rollback script tersedia.

## 9. Keputusan scope yang perlu dikonfirmasi

Rekomendasi saya adalah menyetujui scope **C1–C4** di atas sebagai satu delivery Checkpoint C, dengan dua batas:
1. Checkpoint C memperbaiki integrity, execution lifecycle, evidence/export, dan regression interchange; bukan membangun interaksi lengkap untuk semua komponen.
2. JSON baseline import (untuk membandingkan run) boleh dimasukkan hanya jika pengguna menghendaki; default aman adalah export-only pada C, lalu import/compare sebagai C berikutnya.

Setelah scope dikonfirmasi, langkah berikutnya adalah membuat satu script PowerShell batch yang mem-backup file target, menerapkan semua perubahan terkelompok, membuat/menambah tests dan docs, memvalidasi diff, lalu menjalankan test yang dapat dijalankan otomatis. Tidak ada commit/push kecuali diminta.
