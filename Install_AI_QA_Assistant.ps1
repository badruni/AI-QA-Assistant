[CmdletBinding()]
param(
    [string]$DataRoot = (Join-Path $env:USERPROFILE "AI_QA_Assistant_Data"),
    [switch]$RunRegression
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor DarkCyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor DarkCyan
}

function Invoke-CheckedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )

    Write-Host "`n$Description" -ForegroundColor Cyan
    & $Executable @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$Description gagal. Exit code: $LASTEXITCODE"
    }
}

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RequirementsFile = Join-Path $AppRoot "requirements.txt"
$AgentFile = Join-Path $AppRoot "agent.py"
$VenvRoot = Join-Path $AppRoot ".venv-scanner"
$PythonExe = Join-Path $VenvRoot "Scripts\python.exe"

try {
    Write-Section "AI QA ASSISTANT - INSTALLER"

    foreach ($RequiredFile in @($RequirementsFile, $AgentFile)) {
        if (-not (Test-Path -LiteralPath $RequiredFile)) {
            throw "File wajib tidak ditemukan: $RequiredFile"
        }
    }

    if (-not [System.IO.Path]::IsPathRooted($DataRoot)) {
        throw "DataRoot harus berupa absolute path."
    }

    $DataRoot = [System.IO.Path]::GetFullPath($DataRoot)

    Write-Host "Application : $AppRoot"
    Write-Host "Data        : $DataRoot"
    Write-Host "Environment : $VenvRoot"

    Write-Section "1. MEMERIKSA PYTHON"

    $PythonLauncher = Get-Command py -ErrorAction SilentlyContinue

    if (-not $PythonLauncher) {
        throw "Python Launcher 'py' tidak ditemukan. Instal Python 3.14 64-bit terlebih dahulu."
    }

    $SystemPythonInfo = & py -3.14 -c "import sys,struct; print(f'{sys.version_info.major}.{sys.version_info.minor}|{struct.calcsize(chr(80)) * 8}')"

    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.14 tidak ditemukan."
    }

    if ($SystemPythonInfo.Trim() -ne "3.14|64") {
        throw "Python sistem harus Python 3.14 64-bit. Ditemukan: $SystemPythonInfo"
    }

    Write-Host "Python sistem: $SystemPythonInfo"

    Write-Section "2. MEMERIKSA VIRTUAL ENVIRONMENT"

    if (Test-Path -LiteralPath $VenvRoot) {
        if (-not (Test-Path -LiteralPath $PythonExe)) {
            throw "Folder .venv-scanner sudah ada tetapi python.exe tidak ditemukan. Environment tidak akan ditimpa."
        }

        $ExistingPythonInfo = & $PythonExe -c "import sys,struct; print(f'{sys.version_info.major}.{sys.version_info.minor}|{struct.calcsize(chr(80)) * 8}')"

        if ($LASTEXITCODE -ne 0) {
            throw "Virtual environment yang sudah ada tidak dapat dijalankan."
        }

        if ($ExistingPythonInfo.Trim() -ne "3.14|64") {
            throw "Virtual environment yang sudah ada bukan Python 3.14 64-bit. Tidak akan ditimpa. Ditemukan: $ExistingPythonInfo"
        }

        Write-Host "Virtual environment yang ada akan digunakan: $ExistingPythonInfo" -ForegroundColor Green
    }
    else {
        Invoke-CheckedProcess -Executable "py" -Arguments @("-3.14", "-m", "venv", $VenvRoot) -Description "Membuat virtual environment"

        if (-not (Test-Path -LiteralPath $PythonExe)) {
            throw "Virtual environment gagal dibuat."
        }
    }

    Write-Section "3. MEMASANG DEPENDENSI"

    Invoke-CheckedProcess -Executable $PythonExe -Arguments @("-m", "pip", "install", "-r", $RequirementsFile) -Description "Memasang requirements.txt"

    Write-Section "4. MEMASTIKAN CHROMIUM TERSEDIA"

    Invoke-CheckedProcess -Executable $PythonExe -Arguments @("-m", "playwright", "install", "chromium") -Description "Memastikan Chromium Playwright tersedia"

    Write-Section "5. MENYIAPKAN DATA EKSTERNAL"

    foreach ($Directory in @(
        $DataRoot,
        (Join-Path $DataRoot "projects"),
        (Join-Path $DataRoot "logs")
    )) {
        if (-not (Test-Path -LiteralPath $Directory)) {
            New-Item -ItemType Directory -Path $Directory | Out-Null
            Write-Host "Dibuat: $Directory"
        }
        else {
            Write-Host "Dipertahankan: $Directory"
        }
    }

    Write-Section "6. SMOKE TEST IMPORT"

    Invoke-CheckedProcess -Executable $PythonExe -Arguments @(
        "-c",
        "import tkinter; import docx; import playwright; print('TKINTER: OK'); print('PYTHON-DOCX: OK'); print('PLAYWRIGHT: OK')"
    ) -Description "Memeriksa import dependensi"

    Write-Section "7. MEMERIKSA FILE APLIKASI"

    foreach ($RelativePath in @(
        "agent.py",
        "core\data_paths.py",
        "modules",
        "tests",
        "config\project_template.json",
        "run_ai_qa_assistant.ps1"
    )) {
        $FullPath = Join-Path $AppRoot $RelativePath

        if (-not (Test-Path -LiteralPath $FullPath)) {
            throw "Komponen aplikasi tidak ditemukan: $RelativePath"
        }

        Write-Host "OK: $RelativePath"
    }

    if ($RunRegression) {
        Write-Section "8. FULL REGRESSION TEST"

        Invoke-CheckedProcess -Executable $PythonExe -Arguments @(
            "-m", "unittest", "discover", "-s", "tests", "-v"
        ) -Description "Menjalankan regression test"
    }

    Write-Section "INSTALASI BERHASIL"

    Write-Host "Application : $AppRoot"
    Write-Host "Python      : $PythonExe"
    Write-Host "Data        : $DataRoot"
    Write-Host "Chromium    : Installed/verified"
    Write-Host "Regression  : $(if ($RunRegression) { 'Executed' } else { 'Not requested' })" -ForegroundColor Green
    $global:AIQAInstallerExitCode = 0
    return
}
catch {
    Write-Host ""
    Write-Host "[INSTALLATION FAILED] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Data dan environment yang sudah ada tidak dihapus." -ForegroundColor Yellow
    $global:AIQAInstallerExitCode = 1
    return
}
