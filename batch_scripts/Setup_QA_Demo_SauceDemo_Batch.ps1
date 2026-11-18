[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "=== AI QA Assistant: QA Demo Project Setup ===" -ForegroundColor Cyan

$ProjectRoot = (Get-Location).Path
$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"
$ProjectId = "QA-DEMO-001"
$ProjectDir = Join-Path $ProjectRoot "projects\$ProjectId"

if (-not (Test-Path (Join-Path $ProjectRoot "core\project_manager.py"))) {
    throw "core\project_manager.py tidak ditemukan. Jalankan script dari root proyek."
}
if (-not (Test-Path $Python)) {
    throw "Python scanner tidak ditemukan: $Python"
}
if (Test-Path $ProjectDir) {
    throw "Proyek $ProjectId sudah ada. Tidak ada file yang diubah. Periksa proyek tersebut terlebih dahulu."
}

$PythonScript = @'
import json
import sys
from pathlib import Path

# Tambahkan root proyek ke Python import path.
project_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(project_root))

from core.project_manager import create_project, get_project

project_id = "QA-DEMO-001"
project_name = "QA Demo - SauceDemo"
base_url = "https://www.saucedemo.com/"
cms_url = ""

project_dir = create_project(
    project_id=project_id,
    project_name=project_name,
    base_url=base_url,
    cms_url=cms_url,
)

config = get_project(project_id)

expected_dirs = [
    "logs",
    "documentation",
    "reports",
    "evidence/screenshots",
    "evidence/attachments",
]

missing = [name for name in expected_dirs if not (project_dir / name).is_dir()]
if missing:
    raise SystemExit("Verifikasi gagal. Folder tidak ditemukan: " + ", ".join(missing))

if config.get("base_url") != base_url:
    raise SystemExit("Verifikasi gagal: base_url tidak sesuai.")
if config.get("cms_url") != "":
    raise SystemExit("Verifikasi gagal: cms_url seharusnya kosong.")
if config.get("project_id") != project_id:
    raise SystemExit("Verifikasi gagal: project_id tidak sesuai.")

print("STATUS: OK")
print("Project ID :", config["project_id"])
print("Nama       :", config["project_name"])
print("Frontend   :", config["base_url"])
print("CMS        :", "(tidak dikonfigurasi)")
print("Folder     :", project_dir)
print("Scan config:", json.dumps(config.get("scan", {}), ensure_ascii=False))
print("Direktori standar:", ", ".join(expected_dirs))
'@

$TempScript = Join-Path $env:TEMP ("setup_qa_demo_" + [guid]::NewGuid().ToString("N") + ".py")
try {
    [System.IO.File]::WriteAllText(
        $TempScript,
        $PythonScript,
        [System.Text.UTF8Encoding]::new($false)
    )

    Write-Host "Membuat proyek baru: $ProjectId" -ForegroundColor Cyan
    & $Python $TempScript $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Pembuatan atau verifikasi proyek gagal. Periksa output Python di atas."
    }

    Write-Host "`n=== SETUP SELESAI: MENUNGGU VERIFIKASI PENGGUNA ===" -ForegroundColor Green
    Write-Host "Proyek dibuat di: $ProjectDir"
    Write-Host "Tidak ada proyek lain yang diubah."
    Write-Host "Belum ada website yang diakses."
}
finally {
    if (Test-Path $TempScript) {
        Remove-Item $TempScript -Force
    }
}
