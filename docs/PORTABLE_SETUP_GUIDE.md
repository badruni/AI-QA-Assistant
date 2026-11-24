# Portable Setup and Recovery Guide

## Supported local setup

- Windows 10/11 64-bit with PowerShell (the commands below are Windows-specific).
- Python 3.14.x 64-bit is the verified scanner runtime for this repository.
- `requirements.txt` pins Playwright 1.65.1 and python-docx 1.2.0. Chromium is installed separately by Playwright.
- Network access is needed only to install Python packages and the browser. Do not use client credentials for setup or tests.

Create a fresh virtual environment on each computer. Never copy `.venv` or `.venv-scanner` between computers or operating systems.

```powershell
py -3.14 -m venv .venv-scanner
.\.venv-scanner\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
python --version
python -m playwright --version
python -m unittest discover -s tests
python agent.py
```

If PowerShell blocks activation, use the environment interpreter directly, for example `\.venv-scanner\Scripts\python.exe agent.py`. Do not weaken machine-wide execution policy for this application.

## First run and project data

Run `agent.py`, create a project with an authorized HTTP(S) website, and select it as the active project. Project data is stored under `projects/<project_id>/`: configuration, logs, reports, documentation, evidence, and the project's authorization record. Do not put passwords, tokens, cookies, or authorization headers in project config. Before running any scanner menu (4, 5, 6, or 10), use menu 11 to create an authorization tied to the configured target URL. The record requires the authorizing person, an ISO 8601 expiry including timezone, and the `frontend` plus `read_only` scopes. Creation requires typing `YA` to confirm explicit permission. Menu 11 can also view or revoke the current authorization. The Unified QA Workflow is read-only; it does not log in, submit forms, solve challenges, or bypass WAF/Cloudflare. Use it only with explicit authorization. Restricted access stops the relevant workflow stages.

The unified report is saved as a new JSON file under that project's `reports/`. Evidence files and their SHA-256 index are under `evidence/`. Evidence IDs in a report are emitted only when registration and hash verification succeeded. URL query strings and fragments are removed from report/evidence metadata; `response_preview` is always redacted.

The unified report records evidence collection separately from the QA
inspection result:

- `evidence_status`: `not_required` when no screenshots are expected,
  `verified` when all expected evidence is verified, or `failed` when
  any expected evidence is not verified.
- `expected_evidence`: number of screenshots expected from workflow stages.
- `verified_evidence`: number of evidence items successfully verified.

The QA `result.status` remains the inspection result and is not replaced by
the evidence status. Therefore, a QA inspection can pass while evidence
verification fails. Evidence failure still causes the workflow's terminal
processing status to fail.


### Optional external data directory

By default, project data is stored in the application's `projects/` directory and system logs are stored in `logs/`.

To keep these data folders separate from the application source, set `AI_QA_DATA_DIR` before starting the application. The value must be an absolute path.

PowerShell example:

```powershell
$env:AI_QA_DATA_DIR = 'D:\AI_QA_Assistant_Data'
python agent.py
```

With this setting, project data is stored in `D:\AI_QA_Assistant_Data\projects\` and system logs in `D:\AI_QA_Assistant_Data\logs\`. The project template remains inside the application's `config/` directory.

The `$env:` setting applies to the current PowerShell session. If it is not set, the application uses the legacy data locations inside the application directory. Do not change the data location while the application is running.

This foundation centralizes the `projects/` and `logs/` paths. Client-specific namespace isolation (`client_id`) and migration of existing client data are later tasks and are not yet implemented.

## Backup

Close the application before backing up. Copy the source separately from project data, and keep the destination new and uniquely named. Preserve `projects/`, `logs/`, `evidence/`, reports, and existing backups. Do not include virtual environments in a portable source archive. Encrypt backups that contain client data and restrict access according to client requirements.

Example to a new destination (change the path; ensure it does not already exist):

```powershell
$backup = 'D:\QA-Backups\AI-QA-Assistant-2026-11-19'
if (Test-Path -LiteralPath $backup) { throw 'Backup destination already exists; choose a new name.' }
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item -LiteralPath '.\projects' -Destination $backup -Recurse
Copy-Item -LiteralPath '.\config' -Destination $backup -Recurse
```

Store source code through the approved repository or a separate source archive. Never overwrite an existing backup.

## Restore and verify

Restore into a new, empty staging directory; do not restore over a live project folder. Verify expected project IDs, report counts, evidence index entries, and SHA-256 status in Evidence Viewer. Compare the restored evidence/report inventory with the backup before selecting or using the restored project. The M4 staging restore drill verified the current application and external project/log data using SHA-256. This was not a production rollback, disaster-recovery simulation, or restore test using real client production data.

## Update and rollback

1. Close the application and create a fresh, non-overwriting backup of source and project data.
2. Obtain the update from the approved repository/archive. Do not replace `projects/`, `logs/`, `reports/`, `evidence/`, or `backups/` with a source update.
3. Review changes and run the documented tests in the fresh local Python 3.14 environment.
4. If update verification fails, close the app and use a separate new staging copy of the previous source version. Keep current project data untouched. Compare inventories and validate evidence hashes before directing the application to the recovered source/data. Do not delete or move the failed version until an operator has confirmed recovery.

A synthetic backup/restore and source rollback staging drill passed in temporary directories. In addition, the M4 full backup and restore staging drill completed on 24 November 2026:

- Application: 2,486 files, all SHA-256 matched.
- External projects: 57 files, all SHA-256 matched.
- External logs: 11 files, all SHA-256 matched.
- Total: 2,554 files verified, with zero missing, extra, or mismatched files.
- Restored application smoke test: imports succeeded and Project Manager found 5 valid projects.
- Full regression on restored application: 280 tests, 3 skipped, 0 failed; exit code 0.

The test log is stored in the restore test directory under `restore_logs/FULL_REGRESSION_TEST.txt`. The full backup includes a manifest and manifest checksum. This drill used a separate staging copy and did not overwrite the active application or source data. It does not establish production rollback or disaster-recovery readiness. Real client production recovery remains unverified.

Some regression tests emitted `Screenshot evidence registration failed; inspection continues.` while still passing. This warning is recorded and should not be interpreted as proof that every screenshot was registered successfully.

## Troubleshooting

- `ModuleNotFoundError: playwright`: activate `.venv-scanner` or call its Python executable.
- Browser executable missing: run `python -m playwright install chromium` in the same environment.
- DOCX export requires `python-docx==1.2.0`; install all declared packages with `python -m pip install -r requirements.txt`. If export still reports a missing library, verify the active interpreter and package with `python -m pip show python-docx`.
- Browser launch or timeout: confirm Chromium install, local permissions, and the target's authorized availability. Do not evade a challenge.
- `Access Restricted`: stop; review the recorded HTTP/WAF/Cloudflare indicator and ask the site owner for an approved access path. The tool does not bypass protection.
- Evidence missing or hash mismatch: treat evidence as unverified; do not claim it as report evidence. Preserve the file/index and investigate from a copy.
- Report write failure: the inspection may still be shown, but no persisted report should be claimed. Preserve prior reports and inspect local disk permissions/free space.

## Security and limitations

The scanner follows same-origin navigation policy, request rate limits, and consecutive-403 stop threshold. Redirect destinations are not followed. The tool is not an authentication tester and does not execute state-changing actions. Sensitive-data filtering is defense in depth; never submit or enter real credentials. External Cloudflare/WAF behavior and production backup recovery have not been verified in this local-only readiness milestone.


## Update M3.2 — 24 November 2026
Launcher menyimpan kondisi AI_QA_DATA_DIR sebelum aplikasi berjalan dan mengembalikannya setelah aplikasi selesai. Jika variabel sebelumnya belum tersedia, launcher menghapusnya kembali. Pengaturan ini tidak mengubah environment variable Windows secara permanen.

### Menjalankan aplikasi dengan data eksternal

Pada perangkat yang telah dikonfigurasi, gunakan launcher dari folder utama aplikasi:

```powershell
.\run_ai_qa_assistant.ps1
```

Launcher mengatur `AI_QA_DATA_DIR` ke:

`%USERPROFILE%\AI_QA_Assistant_Data`

Launcher memilih Python dari `.venv-scanner`, kemudian `.venv`, atau Python sistem jika keduanya tidak tersedia. Untuk instalasi baru, buat virtual environment lokal dan instal dependensi terlebih dahulu.

Environment variable hanya diatur untuk proses launcher dan aplikasi yang dijalankannya. Menjalankan `python agent.py` secara langsung tanpa mengatur `AI_QA_DATA_DIR` tetap menggunakan lokasi legacy.

### Status migrasi pada perangkat pengembangan

Folder `projects/` dan `logs/` telah disalin ke direktori data eksternal dan diverifikasi menggunakan SHA-256. Data sumber lama tidak dihapus.

Hasil verifikasi:
- Projects: 57 file, 0 missing, 0 extra, 0 mismatch.
- Logs: 10 file, 0 missing, 0 extra, 0 mismatch.
- Regression: 280 tests, 3 skipped, 0 failed.
- Launcher: berhasil menjalankan aplikasi dan membaca 5 proyek terdaftar.

Lokasi aktual perangkat pengembangan:

`<USER_HOME>\AI_QA_Assistant_Data`

Lokasi aktual tersebut merupakan konfigurasi perangkat ini, bukan lokasi wajib untuk laptop lain. Setiap perangkat dapat menggunakan direktori data sendiri.

### Batasan

Migrasi ini baru mencakup `projects/` dan `logs/`. Namespace `client_id`, isolasi multi-klien, dan pemindahan kategori data lain belum selesai. Lakukan backup sebelum perubahan besar dan jangan menghapus data sumber lama sebelum seluruh proses pemulihan diverifikasi.
