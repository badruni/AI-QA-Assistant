$ErrorActionPreference = 'Stop'

# Jalankan dari root repository AI-QA-Assistant.
$RequiredFiles = @(
    '.\agent.py',
    '.\core\evidence_viewer.py',
    '.\tests\test_evidence_viewer.py',
    '.\docs\PROJECT_SETUP_GUIDE.md',
    '.\docs\PORTABLE_SETUP_GUIDE.md'
)
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $File. Jalankan dari root repository."
    }
}
$Python = '.\.venv-scanner\Scripts\python.exe'
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupDir = ".\backups\before_evidence_viewer_windows_open_$Stamp"
$BackupFiles = @(
    '.\agent.py',
    '.\docs\PROJECT_SETUP_GUIDE.md',
    '.\docs\PORTABLE_SETUP_GUIDE.md'
)
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
foreach ($File in $BackupFiles) {
    $Destination = Join-Path $BackupDir $File.Substring(2)
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item $File $Destination
}
Write-Host "Backup dibuat: $BackupDir" -ForegroundColor Green

$PatchScript = @'
from pathlib import Path

agent_path = Path("agent.py")
agent = agent_path.read_text(encoding="utf-8")

# Add subprocess import without changing unrelated imports.
if "import subprocess\n" not in agent:
    if agent.count("import os\n") != 1:
        raise SystemExit("Import os tidak ditemukan secara unik; patch dibatalkan.")
    agent = agent.replace("import os\n", "import os\nimport subprocess\n", 1)

helper = '''def open_screenshot_file(screenshot_path):
    """Open a screenshot with the Windows default app, falling back to Explorer."""
    start_file = getattr(os, "startfile", None)
    if start_file is None:
        raise OSError("Membuka file otomatis hanya didukung pada Windows.")
    try:
        start_file(str(screenshot_path))
    except OSError as exc:
        # Windows modern can have a working AppX default association even when
        # os.startfile raises WinError 1155. Explorer honors that association.
        if getattr(exc, "winerror", None) != 1155:
            raise
        subprocess.Popen(["explorer.exe", str(screenshot_path)])


'''
if "def open_screenshot_file(" not in agent:
    if agent.count("def run_evidence_viewer(active_project_id):") != 1:
        raise SystemExit("Fungsi run_evidence_viewer tidak ditemukan secara unik.")
    agent = agent.replace(
        "def run_evidence_viewer(active_project_id):",
        helper + "def run_evidence_viewer(active_project_id):",
        1,
    )

old = '''            start_file = getattr(os, "startfile", None)
            if start_file is None:
                print("Membuka file otomatis hanya didukung pada Windows.")
                continue
            start_file(str(screenshot_path))
            print("Screenshot dibuka:", screenshot_path)
'''
new = '''            try:
                open_screenshot_file(screenshot_path)
            except OSError as exc:
                print(f"Gagal membuka screenshot: {exc}")
                continue
            print("Permintaan membuka screenshot dikirim ke Windows:", screenshot_path)
'''
if agent.count(old) != 1:
    raise SystemExit("Blok pembukaan screenshot tidak ditemukan secara unik.")
agent = agent.replace(old, new, 1)
agent_path.write_text(agent, encoding="utf-8", newline="")

# Add focused tests for default-app and Explorer fallback behavior.
test_path = Path("tests/test_evidence_viewer_open.py")
if test_path.exists():
    raise SystemExit("tests/test_evidence_viewer_open.py sudah ada; tidak akan ditimpa.")
test_source = '''import unittest
from pathlib import Path
from unittest.mock import patch

import agent


class EvidenceViewerOpenTests(unittest.TestCase):
    def test_uses_windows_default_association_first(self):
        screenshot = Path("C:/evidence/home.png")
        with (
            patch.object(agent.os, "startfile", create=True) as start_file,
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            agent.open_screenshot_file(screenshot)
        start_file.assert_called_once_with(str(screenshot))
        popen.assert_not_called()

    def test_uses_explorer_when_startfile_raises_winerror_1155(self):
        screenshot = Path("C:/evidence/home.png")
        error = OSError("No application is associated with the specified file")
        error.winerror = 1155
        with (
            patch.object(agent.os, "startfile", create=True, side_effect=error),
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            agent.open_screenshot_file(screenshot)
        popen.assert_called_once_with(["explorer.exe", str(screenshot)])

    def test_does_not_fallback_for_other_os_errors(self):
        screenshot = Path("C:/evidence/home.png")
        error = OSError("Access is denied")
        error.winerror = 5
        with (
            patch.object(agent.os, "startfile", create=True, side_effect=error),
            patch.object(agent.subprocess, "Popen") as popen,
        ):
            with self.assertRaises(OSError) as raised:
                agent.open_screenshot_file(screenshot)
        self.assertIs(raised.exception, error)
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
'''
test_path.write_text(test_source, encoding="utf-8", newline="")

# Document the Windows Explorer fallback in both setup guides.
doc_note = '''\n\n### Membuka screenshot pada Windows\n\nEvidence Viewer mencoba membuka screenshot melalui asosiasi aplikasi default Windows.\nJika pemanggilan langsung menghasilkan WinError 1155, aplikasi meneruskan permintaan\nmelalui Windows Explorer agar asosiasi aplikasi modern (misalnya Paint 3D) tetap\ndigunakan. Aplikasi tidak memaksa Paint klasik dan tidak mengubah asosiasi file Windows.\n'''
for name in ("docs/PROJECT_SETUP_GUIDE.md", "docs/PORTABLE_SETUP_GUIDE.md"):
    path = Path(name)
    content = path.read_text(encoding="utf-8")
    marker = "### Membuka screenshot pada Windows"
    if marker not in content:
        if "## Evidence Viewer" not in content:
            raise SystemExit(f"Bagian Evidence Viewer tidak ditemukan di {name}.")
        content = content.rstrip() + doc_note
        path.write_text(content, encoding="utf-8", newline="")

print("Fallback Windows Explorer dan test pembukaan screenshot berhasil diterapkan.")
'@

Write-Host "`n=== APPLY PATCH ==="
$PatchScript | & $Python -
if ($LASTEXITCODE -ne 0) {
    throw "Patch gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== RUN FOCUSED TESTS ==="
& $Python -m unittest tests.test_evidence_viewer_open tests.test_evidence_viewer tests.test_agent_menu_and_restriction -v
if ($LASTEXITCODE -ne 0) {
    throw "Focused tests gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== COMPILE CHECK ==="
& $Python -m compileall -q agent.py tests\test_evidence_viewer_open.py
if ($LASTEXITCODE -ne 0) {
    throw "Compile check gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== DIFF CHECK ==="
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== PATCH SUMMARY ===" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "Perubahan: os.startfile tetap menjadi prioritas; WinError 1155 menggunakan explorer.exe."
Write-Host "Test baru: tests\test_evidence_viewer_open.py (3 skenario)."
Write-Host "Full test suite dan live UI verification belum dijalankan."
