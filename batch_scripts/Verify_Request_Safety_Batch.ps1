[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path
$TestFile = Join-Path $ProjectRoot "tests\test_request_safety_delivery.py"
$Python = Join-Path $ProjectRoot ".venv-scanner\Scripts\python.exe"

if (-not (Test-Path $TestFile)) { throw "Test tambahan belum dibuat. Jalankan Apply terlebih dahulu." }
if (-not (Test-Path $Python)) { throw "Python scanner tidak ditemukan: $Python" }

Write-Host "=== PYTHON SYNTAX CHECK ===" -ForegroundColor Cyan
& $Python -m py_compile $TestFile
if ($LASTEXITCODE -ne 0) { throw "Syntax check gagal." }

Write-Host "`n=== FEATURE 01 TARGETED TEST ===" -ForegroundColor Cyan
& $Python -m unittest tests.test_request_safety_delivery -v
if ($LASTEXITCODE -ne 0) { throw "Test Feature 01 gagal." }

Write-Host "`n=== EXISTING REQUEST SAFETY TESTS ===" -ForegroundColor Cyan
& $Python -m unittest tests.test_request_safety tests.test_playwright_request_guard -v
if ($LASTEXITCODE -ne 0) { throw "Test existing request safety/guard gagal." }

Write-Host "`n=== FULL REGRESSION SUITE ===" -ForegroundColor Cyan
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Full regression suite gagal." }

Write-Host "`nVERIFICATION COMMANDS COMPLETED." -ForegroundColor Green
