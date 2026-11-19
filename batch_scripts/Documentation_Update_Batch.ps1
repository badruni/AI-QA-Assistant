$ErrorActionPreference = "Stop"
Write-Host "=== FEATURE 01: DOCUMENTATION UPDATE ===" -ForegroundColor Cyan
$Root = (Get-Location).Path
$required = @(
  "docs\AI_QA_Assistant_CHECKPOINT_2026-11-17.md",
  "docs\PROJECT_SETUP_GUIDE.md",
  "tests\test_request_safety_delivery.py",
  "docs\FEATURE_01_REQUEST_SAFETY.md"
)
foreach ($f in $required) {
  if (-not (Test-Path -LiteralPath (Join-Path $Root $f) -PathType Leaf)) {
    throw "File wajib tidak ditemukan: $f. Jalankan dari root repository."
  }
}
$newCheckpoint = Join-Path $Root "docs\AI_QA_Assistant_CHECKPOINT_2026-11-19.md"
$guidePath = Join-Path $Root "docs\PROJECT_SETUP_GUIDE.md"
if (Test-Path -LiteralPath $newCheckpoint) { throw "Checkpoint tujuan sudah ada; tidak akan ditimpa." }
$guide = Get-Content -LiteralPath $guidePath -Raw
$marker = "## Feature 01 — Request Safety & Rate Limit (2026-11-19)"
if ($guide.Contains($marker)) { throw "Riwayat Feature 01 sudah ada; tidak ada file yang diubah." }

$backup = Join-Path $Root ("backups\feature_01_documentation_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item (Join-Path $Root "docs\AI_QA_Assistant_CHECKPOINT_2026-11-17.md") (Join-Path $backup "AI_QA_Assistant_CHECKPOINT_2026-11-17.md")
Copy-Item $guidePath (Join-Path $backup "PROJECT_SETUP_GUIDE.md")

$checkpoint = @'
# AI QA Assistant — Checkpoint Pengembangan

Tanggal: 19 November 2026
Perangkat: Laptop rumah
Repository: `C:\Users\ASUS\Projects\AI-QA-Assistant`
Branch yang dilaporkan: `master`

## 1. Aturan melanjutkan pengembangan

- Kerjakan satu checkpoint pada satu waktu.
- Gunakan PowerShell dan perintah siap salin.
- Tunggu hasil perintah sebelum melanjutkan dan verifikasi setiap langkah.
- Diagnosis error sebelum mengubah kode.
- Backup sebelum perubahan besar.
- Pertahankan kode dan fitur yang berfungsi.
- Perbarui dokumentasi saat ada perubahan arsitektur, dependensi, atau cara menjalankan aplikasi.
- Jangan commit atau push tanpa persetujuan eksplisit.
- Jangan menghapus data proyek, laporan, evidence, log, atau backup.
- Setiap laptop membuat virtual environment sendiri; jangan menyalinnya antarperangkat.

## 2. Status repository pada 19 November 2026

Repository: `https://github.com/badruni/AI-QA-Assistant`
Branch: `master`
Pemeriksaan terakhir: `git status --short`.
Tidak ada file tracked yang dilaporkan modified atau deleted. Ada file untracked dari pengembangan dan pengujian lokal; belum ada commit atau push pada sesi Feature 01.

File untracked pada pemeriksaan terakhir:
- `batch_scripts/.request_safety_delivery_state.json`
- `batch_scripts/Apply_Request_Safety_Batch.ps1`
- `batch_scripts/Prepare_Local_403_Threshold_Test_Batch.ps1`
- `batch_scripts/Prepare_Local_Redirect_Scanner_Test_Batch.ps1`
- `batch_scripts/Prepare_Local_Redirect_Test_Batch.ps1`
- `batch_scripts/Prepare_Request_Safety_Batch.ps1`
- `batch_scripts/Restore_Local_Redirect_Test_Config_Batch.ps1`
- `batch_scripts/Rollback_Request_Safety_Batch.ps1`
- `batch_scripts/Verify_Request_Safety_Batch.ps1`
- `docs/FEATURE_01_REQUEST_SAFETY.md`
- `local_test_site/403_threshold_test_server.py`
- `local_test_site/redirect_test_server.py`
- `tests/test_request_safety_delivery.py`

Pertahankan file-file tersebut. Jangan menjalankan `git clean`, `git reset --hard`, atau penghapusan massal.

## 3. Lingkungan laptop rumah

- Project path: `C:\Users\ASUS\Projects\AI-QA-Assistant`
- Python scanner yang digunakan pada sesi ini: Python 3.14 melalui `.venv-scanner`.
- Playwright: 1.65.1.
- Chromium telah digunakan pada pengujian scanner lokal sebelumnya.
- Verifikasi Feature 01 dijalankan melalui `.venv-scanner\Scripts\python.exe`.

Verifikasi ulang versi Python, paket, dan browser sebelum upgrade atau perubahan environment. Jangan menyalin `.venv` atau `.venv-scanner` dari laptop kantor. Ikuti `docs/PORTABLE_SETUP_GUIDE.md` setelah mencocokkannya dengan source code terkini.

## 4. Feature 01 — Request Safety & Rate Limit

Implementasi yang ditinjau sebelum Feature 01 tersedia pada:
- `core/request_safety.py`
- `core/playwright_request_guard.py`
- `modules/frontend_scanner.py`

Perilaku yang ditinjau mencakup rolling window 60 detik, batas request per menit, menunggu slot request, guard untuk request browser, penggunaan controller sebelum API request link, reset hitungan 403 oleh respons non-403, penghentian saat threshold 403 tercapai, dan pencegahan request setelah controller berhenti.

Feature 01 pada sesi ini berfokus pada pengujian tambahan dan dokumentasi. Kode implementasi produksi tidak diubah.

File tambahan:
- `tests/test_request_safety_delivery.py`
- `docs/FEATURE_01_REQUEST_SAFETY.md`

Hasil verifikasi yang dilaporkan:
- Python syntax check: lulus.
- Feature 01 targeted tests: 7 lulus.
- Existing Request Safety tests: 21 lulus.
- Full regression suite: 160 lulus, 1 skipped.
- Tidak ada test gagal.

Test skipped tidak dihitung sebagai test lulus. Pengujian tambahan menggunakan fake clock dan mock Playwright untuk perilaku unit/guard; ini bukan pengukuran throughput terhadap website publik. Pengujian redirect lintas origin dan threshold 403 sebelumnya dilakukan dengan server lokal. Tidak ada dependency baru pada Feature 01.

## 5. Data lokal dan keamanan

- Folder `projects\` berisi data lokal dan tidak otomatis tersimpan di Git.
- Jangan memindahkan data klien ke perangkat pribadi tanpa izin.
- Jangan menghapus atau menimpa project, reports, evidence, logs, maupun backups.
- Jangan menyimpan password, token, cookie, API key, atau kredensial mentah di log.
- Jangan bypass CAPTCHA, Cloudflare, WAF, atau mekanisme keamanan website.
- Hentikan pemindaian saat batas 403 yang dikonfigurasi tercapai.
- Jangan mengarang temuan, hasil test, atau evidence.

## 6. Riwayat checkpoint

Checkpoint historis tetap dipertahankan:
- `docs/AI_QA_Assistant_CHECKPOINT_2026-11-17.md`

Checkpoint 19 November ini merupakan catatan perkembangan berikutnya, bukan pengganti checkpoint 17 November. Riwayat fitur juga dicatat di `docs/PROJECT_SETUP_GUIDE.md`.

## 7. Langkah berikutnya

1. Tinjau pembaruan dokumentasi Feature 01 dan status Git.
2. Tentukan bersama apakah file batch, test, dan dokumentasi Feature 01 akan di-commit sebagai satu perubahan.
3. Jangan commit atau push sebelum ada persetujuan eksplisit.
4. Setelah Feature 01 ditutup, tentukan satu fitur berikutnya, ruang lingkup, dan kriteria penerimaannya.

## 8. Catatan status

Checkpoint ini dibuat berdasarkan hasil yang dilaporkan pada sesi 19 November 2026. Status Git, versi Python, dan kondisi perangkat harus diverifikasi ulang sebelum sinkronisasi atau perubahan environment.
'@

$history = @'

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
'@

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($newCheckpoint, $checkpoint.Trim() + [Environment]::NewLine, $utf8)
[System.IO.File]::WriteAllText($guidePath, $guide.TrimEnd() + $history + [Environment]::NewLine, $utf8)

Write-Host ""
Write-Host "Dokumentasi berhasil diperbarui." -ForegroundColor Green
Write-Host "Checkpoint baru: docs\AI_QA_Assistant_CHECKPOINT_2026-11-19.md"
Write-Host "Checkpoint lama tetap dipertahankan: docs\AI_QA_Assistant_CHECKPOINT_2026-11-17.md"
Write-Host "Project setup guide diperbarui: docs\PROJECT_SETUP_GUIDE.md"
Write-Host "Backup: $backup"
Write-Host "Tidak ada kode produksi atau data proyek yang diubah."
