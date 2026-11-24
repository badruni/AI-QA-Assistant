
$ErrorActionPreference = "Stop"

# Lokasi aplikasi dan data eksternal
$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataRoot = Join-Path $env:USERPROFILE "AI_QA_Assistant_Data"

# Pilih Python dari virtual environment proyek
$PythonCandidates = @(
    (Join-Path $AppRoot ".venv-scanner\Scripts\python.exe"),
    (Join-Path $AppRoot ".venv\Scripts\python.exe")
)

$PythonExe = $PythonCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

# Gunakan Python sistem jika virtual environment tidak ditemukan
if (-not $PythonExe) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if ($PythonCommand) {
        $PythonExe = $PythonCommand.Source
    }
}

if (-not $PythonExe) {
    Write-Host "ERROR: Python tidak ditemukan." -ForegroundColor Red
    Write-Host "Pastikan Python atau virtual environment sudah tersedia."
    return
}

$AgentFile = Join-Path $AppRoot "agent.py"

if (-not (Test-Path $AgentFile)) {
    Write-Host "ERROR: agent.py tidak ditemukan." -ForegroundColor Red
    return
}

# Simpan kondisi environment variable sebelumnya
$HadPreviousDataDir = Test-Path Env:AI_QA_DATA_DIR
$PreviousDataDir = $env:AI_QA_DATA_DIR
$LocationPushed = $false
$AppExitCode = 1

try {
    # Atur direktori data untuk aplikasi
    $env:AI_QA_DATA_DIR = $DataRoot

    # Pastikan direktori data tersedia
    New-Item -ItemType Directory -Path (Join-Path $DataRoot "projects") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $DataRoot "logs") -Force | Out-Null

    Write-Host ""
    Write-Host "=== AI QA ASSISTANT ==="
    Write-Host "Application : $AppRoot"
    Write-Host "Python      : $PythonExe"
    Write-Host "Data        : $DataRoot"
    Write-Host ""

    Push-Location $AppRoot
    $LocationPushed = $true

    & $PythonExe $AgentFile
    $AppExitCode = $LASTEXITCODE
}
finally {
    if ($LocationPushed) {
        Pop-Location
    }

    # Pulihkan environment variable seperti kondisi sebelumnya
    if ($HadPreviousDataDir) {
        $env:AI_QA_DATA_DIR = $PreviousDataDir
    }
    else {
        Remove-Item Env:AI_QA_DATA_DIR -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "AI QA Assistant selesai. Exit code: $AppExitCode"
