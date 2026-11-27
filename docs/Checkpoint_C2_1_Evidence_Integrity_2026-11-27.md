# Checkpoint C2.1 — Evidence Integrity
Tanggal: 27 November 2026

## Tujuan
Memperkuat bukti eksekusi skenario yang telah ada tanpa mengubah katalog komponen atau kontrak export.

## Perubahan
- SCN-N-001 merekam selector homepage, status ditemukan, dan document.readyState.
- SCN-N-003 merekam state tab/pane sebelum klik, setelah klik, dan setelah pemulihan.
- SCN-N-004 merekam tema root, nilai localStorage, meta theme-color, serta verifikasi pemulihan.
- SCN-N-005 merekam dialog terbuka/tertutup dan fokus yang kembali ke pemicu.
- SCN-X-001 menggunakan probe non-kosong `Accordion`, mengosongkan pencarian, memulihkan probe, lalu membandingkan hasil render.
- Executor memverifikasi pemulihan search dan pane terhadap snapshot awal.
- Schema export tetap 3.0; katalog 57 komponen dan 72 skenario tidak berubah.
- SCN-X-003 tetap blocked karena browser network instrumentation belum tersedia.

## Batasan
- Evidence berupa metadata DOM/browser, bukan screenshot.
- Responsive scenarios masih hanya menguji viewport aktif.
- Security simulator tetap simulasi lokal, bukan pengujian HTTP atau penetration test.
- Status `passed` menunjukkan assertion skenario yang tercatat terpenuhi; bukan bukti menyeluruh terhadap seluruh perilaku website.

## Verifikasi
Jalankan:
`node --check local_test_site/playground/assets/app.js`
`python -m unittest tests.test_qa_playground_c2_1_evidence -v`
Kemudian jalankan full regression suite menggunakan Python scanner environment yang benar dan `AI_QA_DATA_DIR` sesuai konfigurasi lokal.

## Rollback
Gunakan `ROLLBACK_Checkpoint_C2_1.ps1` di folder backup sebelum batch ini.
## Final verification — 27 November 2026
- Static tests: 8/8 passed.
- Browser acceptance: 7/7 executed scenarios passed.
- Scenario assertion tests: 7/7 passed.
- Full Python regression suite: 312 passed, 0 failures, 3 skipped.
- One stale test assertion was corrected from `initial_visible_items` to `original_visible_items` to match the existing app.js evidence field. No app.js change was needed for this correction.
- Browser export schema: 3.0; 57 component definitions, 72 scenario definitions, 7 execution records.
- SCN-X-003 was not executed because browser network instrumentation is unavailable.
- Evidence consists of browser/DOM metadata; no screenshot evidence is claimed.
