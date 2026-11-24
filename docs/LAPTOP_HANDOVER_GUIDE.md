# Laptop Handover Guide — AI QA Assistant

Diperbarui: 19 November 2026. Panduan ini menyiapkan salinan kerja laptop kantor untuk verifikasi instalasi bersih di laptop rumah. Paket source tidak membawa data proyek atau virtual environment. Tidak ada file yang di-commit atau di-push.

## Kondisi proyek saat handover

- Folder sumber: `<LOCAL_PATH>`.
- Branch: `master`; base commit: `8156edcef6f8ed7b28e37db2b0ee3183ea63de57` (`Integrate frontend homepage report generation`).
- Pada snapshot paket v3 sebelum pembuatan arsip: 24 tracked files modified dan 35 untracked files; tidak ada perubahan staged atau file terhapus. Ada perubahan M1–M3 yang belum di-commit. Jangan menyamakan isi snapshot handover dengan commit bersih.
- Checkpoint: `docs/AI_QA_Assistant_CHECKPOINT_2026-11-19.md`.
- Full regression setelah perubahan DOCX: 205 tes, 202 passed, 3 skipped, 0 failed. Skip adalah tes symlink yang memerlukan izin yang tidak tersedia di Windows kantor.
- Keputusan Final Acceptance saat ini: **Not Ready for Release Candidate**. Lihat `docs/RELEASE_READINESS_CHECKLIST.md`.

## Paket transfer

Paket source final berada di `handover/AI_QA_Assistant_Handover_20261119_v3.zip`. File checksum dan daftar file berada di `handover/AI_QA_Assistant_Handover_20261119_v3_SHA256.txt`. Transfer hanya setelah ukuran dan SHA-256 paket diverifikasi di laptop kantor dan cocok kembali di laptop rumah.

Snapshot menyertakan `.git` untuk mempertahankan base commit/branch dan source kerja (termasuk perubahan belum commit), serta `agent.py`, `core/`, `modules/`, `config/`, `templates/`, `local_test_site/`, `tests/`, `docs/`, `.gitignore`, dan `requirements.txt`.

Paket tidak menyertakan `.venv/`, `.venv-scanner/`, `__pycache__/`, `projects/`, `logs/`, `reports/`, `backups/`, `test-results/`, atau `batch_scripts/`. `batch_scripts/` berisi artefak dan arsip pengembangan yang tidak diperlukan untuk menjalankan aplikasi; seluruh isinya tetap di laptop kantor dan tidak diubah. Paket ini tidak membawa file lokal proyek, laporan, evidence, log, backup, credential, atau konfigurasi rahasia. `config/project_template.json` adalah template dengan URL contoh.

Jangan menghapus atau memindahkan folder yang dikecualikan dari laptop kantor. Direktori `projects/`, `logs/`, `reports/`, dan `backups/` perlu dipertahankan sebagai data kerja lokal. Evidence/report lokal juga tetap berada dalam data proyek. Laptop rumah untuk verifikasi bersih sebaiknya memakai folder proyek kosong dan fixture sintetis; jangan salin data klien ke sana tanpa persetujuan terpisah.

## Persyaratan dan dependency

- Windows 10/11 64-bit dengan PowerShell.
- Python 3.14.x 64-bit; environment kantor scanner saat audit menggunakan Python 3.14.10.
- Git untuk membuka snapshot sebagai working tree dan meneruskan pekerjaan; Git kantor: 2.56.0.windows.4.
- `requirements.txt` mendeklarasikan `playwright==1.65.1` dan `python-docx==1.2.0`; Chromium dipasang terpisah.
- `python-docx==1.2.0` diperlukan runtime hanya saat menu Export DOCX digunakan dan kini dideklarasikan dalam `requirements.txt`. Tes renderer menghasilkan DOCX yang dapat dibuka, menjaga versi lama tanpa overwrite, dan memeriksa pesan error jika library tidak tersedia. `modules/documentation_generator.py` membuat draft JSON dan tidak memerlukan python-docx. Chromium tetap dipasang terpisah.
- Python 3.15.2 pada `.venv` kantor tidak memiliki Playwright dan bukan environment yang dipakai untuk menjalankan scanner.

## Instalasi bersih di laptop rumah

1. Salin ZIP dan SHA manifest ke media transfer yang disetujui (misalnya USB terenkripsi). Jangan sertakan folder proyek, log, report, evidence, backup, atau virtual environment kantor.
2. Di laptop rumah, pastikan file transfer sudah lengkap. Dari PowerShell, hitung ulang hash:

   ```powershell
   Get-FileHash .\AI_QA_Assistant_Handover_20261119_v3.zip -Algorithm SHA256
   ```

   Cocokkan dengan nilai `PACKAGE_SHA256` di manifest. Jika berbeda, jangan ekstrak atau gunakan paket; transfer ulang dari salinan sumber.
3. Ekstrak ke folder baru yang belum ada, misalnya `<LOCAL_PATH>`. Jangan menimpa checkout atau data yang telah ada.
4. Pastikan Python 3.14.x dan Git tersedia:

   ```powershell
   py -3.14 --version
   git --version
   ```

5. Dari root ekstraksi, buat environment baru (jangan salin `.venv` kantor):

   ```powershell
   py -3.14 -m venv .venv-scanner
   .\.venv-scanner\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   python --version
   python -m playwright --version
   ```

   Jika aktivasi PowerShell diblokir, jangan ubah execution policy. Jalankan executable langsung: `\.venv-scanner\Scripts\python.exe -m pip install -r requirements.txt` dan seterusnya.
6. Jalankan regression lokal sebelum aplikasi:

   ```powershell
   .\.venv-scanner\Scripts\python.exe -m unittest discover -s tests
   ```

   Bandingkan hasil dan skip dengan checkpoint. Tes symlink dapat tetap skip jika izin OS tidak ada. Jangan mengubah kebijakan Windows untuk memaksakannya.
7. Jalankan `\.venv-scanner\Scripts\python.exe agent.py`. Jangan pilih atau scan website nyata sebagai smoke test. Verifikasi menu dan buat proyek sintetis/local bila perlu; jangan akses website eksternal tanpa izin.
8. Verifikasi DOCX export lewat tes `tests.test_docx_renderer`; tes menghasilkan dokumen fixture yang valid di direktori sementara dan tidak memakai data proyek nyata.

## Struktur yang dipertahankan

Source untuk instalasi: `agent.py`, `core/`, `modules/`, `config/project_template.json`, `templates/`, `local_test_site/`, `tests/`, `docs/`, `.gitignore`, `requirements.txt`, dan `.git` di dalam snapshot.

Data yang tetap aman di laptop kantor: seluruh `projects/` termasuk konfigurasi, documentation, reports dan evidence; root `logs/`, `reports/`, `backups/`, `test-results/`, serta artefak `batch_scripts/`. Virtual environment dan cache juga tetap lokal dan dibuat ulang hanya bila diperlukan. Jangan memasukkan rahasia ke paket atau memindahkan data proyek hanya untuk tes instalasi.

## Pemeriksaan hasil transfer

- `Get-FileHash` paket di rumah sama dengan `PACKAGE_SHA256` dari manifest.
- Ekstraksi memiliki file source, konfigurasi template, docs, dan tests; tidak memiliki folder data proyek atau venv.
- Jalankan `git status --short --branch`. Branch dan base commit harus sesuai manifest; perubahan belum commit akan tampak sebagai modified/untracked.
- Interpreter menunjuk ke `.venv-scanner`; Playwright 1.65.1 dan Chromium dapat diluncurkan oleh Playwright.
- Full regression selesai tanpa failed test. Jelaskan setiap skip; hasil instalasi baru tidak boleh disamakan dengan hasil dari kantor.
- Aplikasi dapat start dan menampilkan menu tanpa memilih website eksternal.
- DOCX export dijalankan dengan `python-docx==1.2.0` yang dipasang dari requirements; verifikasi instalasi bersih laptop rumah tetap belum dilakukan.

## Melanjutkan pekerjaan Codex

Buka folder ekstraksi sebagai workspace Codex baru di laptop rumah. Minta Codex membaca panduan ini, checkpoint terbaru, dan status Git sebelum perubahan. Sampaikan bahwa snapshot berasal dari branch `master` pada base commit di atas dengan perubahan M1–M3 yang belum commit. Pertahankan semua perubahan dan file untracked. Jangan commit/push tanpa persetujuan. Lanjutkan gap acceptance (tes symlink di host berizin dan clean install ini) tanpa website eksternal atau data klien.

## Rollback bila verifikasi gagal

Jangan hapus folder hasil ekstraksi atau menimpa backup. Biarkan snapshot gagal tetap utuh untuk diagnosis. Buat folder baru untuk ekstraksi ulang dari ZIP yang hash-nya cocok. Jika ingin kembali ke source pada base commit, gunakan checkout/clone baru di folder terpisah; jangan `git reset`, `git clean`, atau menghapus snapshot. Data proyek kantor tetap berada di sumber dan tidak terpengaruh. Jika ada folder kerja/data rumah yang perlu dipertahankan, buat salinan terpisah sebelum tindakan rollback apa pun.

## Handover checksum

Checksum paket dan SHA-256 setiap file di dalam paket dicatat di `handover/AI_QA_Assistant_Handover_20261119_v3_SHA256.txt`. Manifest dibuat setelah ZIP selesai, sehingga file manifest tidak berada di dalam ZIP. Paket v3 dianggap tersedia setelah keberadaan ZIP, jumlah file, checksum paket, seluruh SHA-256 file, dan pemeriksaan isi ZIP diverifikasi. Paket v1 dan v2 tetap tersimpan, tetapi gunakan hanya paket v3.
