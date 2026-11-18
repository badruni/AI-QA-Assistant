$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$AgentPath = Join-Path $Root "agent.py"

if (-not (Test-Path $AgentPath -PathType Leaf)) {
    throw "agent.py tidak ditemukan. Jalankan batch dari root proyek."
}

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$Original = [System.IO.File]::ReadAllText($AgentPath, [System.Text.Encoding]::UTF8)
$Broken = "    return active_project_iddef main():"
$Fixed = "    return active_project_id`r`n`r`ndef main():"

$Occurrences = ([regex]::Matches($Original, [regex]::Escape($Broken))).Count
if ($Occurrences -ne 1) {
    throw "Pola syntax rusak harus ditemukan tepat satu kali. Ditemukan: $Occurrences. Tidak ada perubahan dilakukan."
}

$BackupName = "before_agent_syntax_fix_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$BackupDir = Join-Path $Root "backups\$BackupName"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item $AgentPath (Join-Path $BackupDir "agent.py") -Force
Write-Host "Backup dibuat: $BackupDir"

$Updated = $Original.Replace($Broken, $Fixed)
[System.IO.File]::WriteAllText($AgentPath, $Updated, $Utf8NoBom)

Write-Host "`nMemeriksa syntax agent.py..."
$Python = Join-Path $Root ".venv-scanner\Scripts\python.exe"
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python. Perubahan sudah dibuat dan backup tersedia."
}

& $Python -m py_compile $AgentPath
if ($LASTEXITCODE -ne 0) {
    throw "Syntax check agent.py gagal. Jangan lanjutkan ke full regression."
}

Write-Host "`nMemeriksa diff..."
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check menemukan masalah. Periksa output di atas."
}

Write-Host "`nPerbaikan syntax agent.py selesai."
Write-Host "Backup: $BackupDir"
Write-Host "Syntax check: PASSED"
Write-Host "git diff --check: PASSED (jika tidak ada error di atas)"
