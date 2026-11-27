# Checkpoint C2 — Scenario Assertions & Evidence

Tanggal: 2026-11-27

## Tujuan
Memperbaiki skenario behavioral yang sebelumnya dapat berstatus `passed` tanpa interaksi atau evidence yang cukup. Perubahan ini mempertahankan Checkpoint C schema 3.0 dan tidak menambah dependency.

## Perubahan
- SCN-N-003 melakukan klik tab Catalog dan memeriksa `aria-selected` serta pane aktif.
- SCN-N-004 melakukan klik theme toggle, memeriksa perubahan tema, lalu memulihkan tema dan nilai `localStorage` awal.
- SCN-N-005 membuka dialog melalui pemicu gambar dan menutupnya melalui tombol close.
- SCN-X-001 mengirim input event untuk pencarian kosong dan merekam jumlah item sebelum/sesudah. Nilai input awal dipulihkan oleh lifecycle UI Checkpoint C.
- SCN-X-003 menjadi `blocked`, bukan `passed`, karena executor tidak menginstrumentasi seluruh kanal network browser.
- SCN-R-001 dan SCN-R-002 menyimpan evidence ukuran aktual dan secara eksplisit membatasi klaim pada viewport saat ini.
- Metadata skenario menjelaskan langkah dan expected result yang benar-benar diperiksa.

## Batasan
- Responsive checks tidak menguji semua breakpoint; hanya viewport aktif.
- SCN-X-003 belum membuktikan tidak adanya network request. Perlu instrumentasi khusus pada tahap berikutnya.
- Dialog test menggunakan media opener pertama yang tersedia di halaman.
- Theme test memulihkan state tema/localStorage, tetapi jika terjadi exception di tengah interaksi, pemeriksaan manual tetap diperlukan.

## Verifikasi
Batch menjalankan Node syntax check bila Node tersedia dan targeted Python unittest bila `.venv-scanner` tersedia. Hasil harus dilihat pada output PowerShell pengguna; script tidak melakukan commit/push.
## Final verification update — 27 November 2026
- Scenario assertion tests: 7/7 passed.
- Browser acceptance: 7/7 executed scenarios passed.
- Full Python regression suite after the C2.1 assertion-test correction: 312 passed, 0 failures, 3 skipped.
- SCN-X-003 remains unexecuted; it must not be interpreted as a passed network/security test.
