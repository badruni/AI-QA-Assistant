# Checkpoint B — Component Detection Stabilization

Tanggal: 27 November 2026

## Tujuan

Menstabilkan bukti deteksi komponen pada Living QA Playground tanpa mengubah source inventory dan tanpa menyamakan deteksi dengan pengujian perilaku.

## Temuan analisis source sebelum batch

- Katalog berisi 57 record unik: 21 `implemented`, 19 `partial`, dan 17 `not_implemented`.
- Terdapat 108 entri selector kandidat dan 83 selector unik.
- Terdapat 13 selector yang digunakan bersama oleh lebih dari satu record komponen.
- Handler `Scan DOM catalog` menjalankan `qaDetectComponent` pada seluruh katalog, lalu memanggil `qaRunScenario` untuk setiap komponen. Executor skenario juga menjalankan `qaDetectComponent`, sehingga deteksi dilakukan dua kali.
- Normalisasi selector CSS hover menggunakan pola regex dengan backslash ganda sebelum `b`; pola tersebut tidak mewakili word-boundary JavaScript yang dimaksud.
- Sebelum batch ini belum tersedia test otomatis khusus untuk integritas katalog dan aturan deteksi QA Playground.

## Perubahan batch

1. Memperbaiki normalisasi selector `:hover` menggunakan word-boundary yang benar.
2. Membuat indeks kepemilikan selector berdasarkan seluruh katalog.
3. Menambahkan metadata `owners` dan `ambiguous` pada bukti selector DOM.
4. Jika seluruh selector yang cocok dipakai bersama oleh beberapa record komponen, runtime menjadi `needs_review`, bukan `detected`.
5. Jika ada bukti selector unik, deteksi tetap dapat menjadi `detected`; selector bersama tetap dicatat sebagai catatan.
6. Menghapus preliminary detection pass agar setiap component scenario menjalankan detector satu kali.
7. Menambahkan static regression tests untuk jumlah/keunikan katalog, distribusi source status, selector, hover regex, duplicate scan, dan pemisahan expectation/behavior.

## Batasan interpretasi

- `detected` tetap berarti kandidat selector ditemukan, bukan perilaku komponen lulus.
- `needs_review` berarti bukti tidak unik atau pemeriksaan tidak konklusif.
- Selector unik pun belum membuktikan interaksi, aksesibilitas, atau responsivitas berfungsi.
- Perubahan ini dapat mengubah distribusi runtime dan expectation dibandingkan Checkpoint A. Angka baru hanya boleh dicatat setelah scan browser aktual dijalankan.
- Static regression tests tidak menggantikan verifikasi browser runtime.

## Verifikasi yang harus dijalankan

1. `python -m unittest discover -s tests -p "test_qa_playground_component_detection.py" -v`
2. Jika Node.js tersedia: `node --check .\local_test_site\playground\assets\app.js`
3. Jalankan Playground dan klik `Scan DOM catalog` satu kali.
4. Periksa komponen yang sebelumnya menggunakan selector bersama, termasuk CMP-001/CMP-049, CMP-003/CMP-035, CMP-017/CMP-018/CMP-043, CMP-030/CMP-045/CMP-052/CMP-056, dan CMP-039/CMP-048.
5. Pastikan CMP-033 tetap dapat menemukan CSS hover evidence, tetapi `behavior_status` dan `keyboard_equivalent_status` tetap `not_tested`.
6. Pastikan hasil scan menghasilkan satu record per component scenario, tanpa scan pendahuluan ganda.

## Rollback

Backup source dibuat di luar repository pada:
`%USERPROFILE%\AI_QA_Assistant_Backups\before_checkpoint_b_component_stabilization_<timestamp>`

Jika verifikasi gagal, pulihkan `app.js` dari backup tersebut dan hapus hanya file test/dokumen baru yang dibuat oleh batch ini. Jangan menghapus data proyek, evidence, laporan, atau backup.

## Browser verification — 27 November 2026

### Runtime summary

| Metric | Verified result |
|---|---:|
| Component records | 57 |
| Runtime DETECTED | 22 |
| Runtime NOT DETECTED | 17 |
| Runtime NEEDS REVIEW | 18 |
| Expectation MATCH | 33 |
| Expectation MISMATCH | 0 |
| Expectation REVIEW | 24 |
| Scenario registry | 72 |
| Executed | 57 |
| Checks Passed | 33 |

### Shared-selector spot checks

| Component | Source | Runtime | Expectation | Observation |
|---|---|---|---|---|
| CMP-001 Header | IMPLEMENTED | DETECTED | MATCH | Specific navigation/top-action selectors remain available |
| CMP-003 Hamburger Menu | IMPLEMENTED | DETECTED | MATCH | Specific open/close/drawer selectors remain available |
| CMP-017 Highlights Section | IMPLEMENTED | DETECTED | MATCH | Specific highlights/list selectors remain available |
| CMP-018 Category Card | PARTIAL | NEEDS REVIEW | REVIEW | Shared highlight-card evidence is not treated as unique |
| CMP-030 Gallery Section | IMPLEMENTED | NEEDS REVIEW | REVIEW | Matching candidates are shared; manual review required |
| CMP-035 Expand / Collapse | PARTIAL | DETECTED | REVIEW | Drawer state is detected, but does not prove a reusable disclosure pattern |
| CMP-039 Modal / Popup | IMPLEMENTED | DETECTED | MATCH | Specific image-modal selectors remain available |
| CMP-043 Article Card | PARTIAL | NEEDS REVIEW | REVIEW | Shared highlight-card evidence is insufficient |
| CMP-045 Content Grid | PARTIAL | NEEDS REVIEW | REVIEW | Shared grid evidence is insufficient |
| CMP-048 Gallery Image Viewer | IMPLEMENTED | DETECTED | MATCH | Specific media-open evidence remains available |
| CMP-049 Responsive Header | IMPLEMENTED | NEEDS REVIEW | REVIEW | Matching topbar evidence is shared |
| CMP-052 Responsive Grid | IMPLEMENTED | DETECTED | MATCH | Multiple grid candidates provide evidence beyond the shared gallery selector |
| CMP-056 Responsive Gallery | IMPLEMENTED | NEEDS REVIEW | REVIEW | Only the shared gallery-grid candidate matched |

### Interpretation and limitations

- Browser verification confirms the detector's current classification output for the listed components.
- `DETECTED` and `MATCH` are inventory/detection outcomes only; they do not establish that component behavior passes.
- Responsive overflow, content fit, image crop, tap targets, modal sizing, keyboard behavior, and interaction behavior remain untested unless separately executed and evidenced.
- CMP-033 Hover Interaction remains detection-only; hover behavior and keyboard equivalent remain `NOT TESTED`.
- The 57 executed figure is the Playground dashboard's displayed count. It must not be interpreted as 57 successful behavior tests.
- Runtime distribution is expected to differ from Checkpoint A because shared-selector ambiguity is now surfaced for manual review.

## Status

Checkpoint B — Component Detection Stabilization: browser verification completed for the agreed shared-selector spot-check set. Static regression: 7/7 PASS. JavaScript syntax check: PASS. Acceptance is limited to detection stabilization; behavior testing remains outside this checkpoint.

Git commit and push: pending user approval.