# Checkpoint C — Scenario Engine Integrity, Lifecycle & Evidence Contract

Tanggal: 27 November 2026

## Scope
Checkpoint C1–C4: registry integrity, execution lifecycle, evidence/export contract, browser acceptance and documentation. Regression interchange is export-only in this checkpoint; JSON import and cross-run comparison are deferred.

## C1 — Registry integrity
- Validasi 57 component records dan 72 scenario records saat bootstrap.
- Fixed scenario mappings menggunakan component ID hanya jika relasinya benar; scenario tingkat halaman/Workbench/security menggunakan `component_id: null`.
- Component DOM scan tetap satu skenario per komponen.
- Inventory scan dibedakan dari behavioral scenario melalui `result_kind`.
- Registry validation memeriksa ID unik, lab valid, component reference, dan coverage DOM scan.

## C2 — Execution lifecycle
- Setiap execution memiliki `session_id` dan `execution_id` unik.
- Executor menangkap dan memulihkan nilai search serta pane Workbench sebelum menyelesaikan result record.
- Clear Results mereset scenario records, runtime detection/expectation fields, result records, dan simulator output.
- Status `passed` pada component scan tetap berarti inventory expectation match, bukan bukti perilaku komponen lulus.
- UI state restoration adalah best-effort untuk kontrol yang dimutasi executor; aksi destruktif tidak dijalankan.

## C3 — Evidence/export
- JSON export menggunakan schema version `3.0`.
- Definisi catalog/scenario dipisahkan dari execution result snapshots.
- URL diekspor sebagai origin + pathname; query string dan fragment tidak disertakan.
- Security simulator mengekspor `simulation_only: true` dan `network_requests: 0`.
- Export divalidasi sebelum download.
- Object URL dicabut setelah jeda singkat agar browser memiliki kesempatan memulai download.
- Evidence pada checkpoint ini berupa metadata JSON; tidak ada klaim screenshot evidence otomatis.
- Tidak ada import, persistence server-side, cloud sync, atau database baru.

## C4 — Verification
- Jalankan targeted static tests `tests/test_qa_playground_scenario_engine.py`.
- Jalankan `node --check local_test_site/playground/assets/app.js` jika Node tersedia.
- Browser acceptance tetap wajib: 57 catalog entries, 72 scenario entries, 70 safe checks, state restore, reset, JSON export, dan fungsi homepage.
- Full Python regression suite dijalankan menggunakan `.venv-scanner` dan `AI_QA_DATA_DIR` sesuai setup laptop; jangan menggunakan Python global yang tidak memiliki dependensi proyek.

## Limitations
- Belum ada behavior test menyeluruh untuk 57 komponen.
- Accessibility/responsive checks masih smoke-level.
- Security behavior tetap simulasi lokal, bukan HTTP 403 atau penetration test.
- Belum ada Python scanner integration, screenshot capture, JSON import, regression comparison, atau server persistence.

## Final verification update — 27 November 2026
- Full Python regression suite: 312 tests passed, 0 failures, 3 skipped.
- C2.1 static evidence tests: 8/8 passed.
- Scenario assertion tests: 7/7 passed.
- Browser acceptance: 7/7 executed scenarios passed.
- Browser acceptance export: schema 3.0, 57 component definitions, 72 scenario definitions, 7 execution records.
- Browser acceptance is a targeted subset; it does not establish that all 72 scenarios were executed.
- SCN-X-003 was intentionally not executed because browser network instrumentation is not available.
