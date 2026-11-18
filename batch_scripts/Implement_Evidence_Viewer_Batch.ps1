$ErrorActionPreference = 'Stop'

# Jalankan dari root repository AI-QA-Assistant.
$RequiredFiles = @(
    '.\agent.py',
    '.\core\evidence_manager.py',
    '.\tests\test_agent_menu_and_restriction.py',
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
$BackupDir = ".\backups\before_evidence_viewer_$Stamp"
$BackupFiles = @(
    '.\agent.py',
    '.\tests\test_agent_menu_and_restriction.py',
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

# Create read-only evidence viewer helpers.
viewer_path = Path("core/evidence_viewer.py")
if viewer_path.exists():
    raise SystemExit("core/evidence_viewer.py sudah ada; tidak akan ditimpa.")
viewer_source = '''"""Read-only helpers for browsing project evidence."""
from pathlib import Path

from core.evidence_manager import list_evidence
from core.project_manager import PROJECTS_DIR


def list_project_evidence(project_id):
    """Return registered evidence for one validated project."""
    return tuple(list_evidence(project_id))


def get_evidence_details(project_id, evidence_id):
    """Return one evidence record or raise KeyError."""
    for record in list_project_evidence(project_id):
        if record.get("evidence_id") == evidence_id:
            return record
    raise KeyError("Evidence ID tidak ditemukan.")


def resolve_evidence_path(project_id, evidence_id):
    """Resolve an indexed file path and enforce project evidence containment."""
    record = get_evidence_details(project_id, evidence_id)
    evidence_dir = (PROJECTS_DIR / project_id / "evidence").resolve()
    candidate_input = evidence_dir / Path(record.get("file_path", ""))
    if candidate_input.is_symlink():
        raise ValueError("Symlink tidak diizinkan sebagai evidence.")
    candidate = candidate_input.resolve()
    try:
        candidate.relative_to(evidence_dir)
    except ValueError:
        raise ValueError("Path evidence berada di luar folder proyek.") from None
    if not candidate.is_file():
        raise FileNotFoundError("File evidence tidak ditemukan.")
    return candidate
'''
viewer_path.write_text(viewer_source, encoding="utf-8", newline="")

# Update agent imports.
agent_path = Path("agent.py")
agent = agent_path.read_text(encoding="utf-8")
old = "import json\nfrom pathlib import Path\n"
new = "import json\nimport os\nfrom pathlib import Path\n"
if agent.count(old) != 1:
    raise SystemExit("Pola import agent.py tidak sesuai.")
agent = agent.replace(old, new, 1)
anchor = "from core.report_manager import save_inspection_report\n"
imports = (
    anchor
    + "from core.evidence_manager import verify_evidence\n"
    + "from core.evidence_viewer import (\n"
    + "    list_project_evidence,\n"
    + "    get_evidence_details,\n"
    + "    resolve_evidence_path,\n"
    + ")\n"
)
if agent.count(anchor) != 1:
    raise SystemExit("Import report_manager tidak ditemukan secara unik.")
agent = agent.replace(anchor, imports, 1)

old = '    print("7. Keluar")\n'
new = '    print("8. Evidence Viewer")\n    print("9. Keluar")\n'
if agent.count(old) != 1:
    raise SystemExit("Label menu keluar tidak ditemukan secara unik.")
agent = agent.replace(old, new, 1)

viewer_function = '''def run_evidence_viewer(active_project_id):
    """Interactive, read-only evidence viewer for the active project."""
    print("\\n================================")
    print("          EVIDENCE VIEWER")
    print("================================")

    if not active_project_id:
        print("\\nBelum ada proyek aktif.")
        print("Silakan pilih proyek yang evidence-nya ingin dilihat.")
        active_project_id = select_active_project()
        if not active_project_id:
            print("\\nEvidence Viewer tidak dijalankan.")
            return None

    while True:
        print("\\n--- EVIDENCE VIEWER ---")
        print("Project ID:", active_project_id)
        print("1. Daftar evidence")
        print("2. Detail evidence")
        print("3. Buka screenshot")
        print("4. Verifikasi integritas evidence")
        print("5. Kembali ke menu utama")
        choice = input("\\nPilih menu: ").strip()

        if choice == "1":
            records = list_project_evidence(active_project_id)
            if not records:
                print("\\nBelum ada evidence terdaftar untuk proyek ini.")
                continue
            print("\\nDAFTAR EVIDENCE")
            for index, record in enumerate(records, start=1):
                print(
                    f"{index}. [{record.get('evidence_type', '-')}] "
                    f"{record.get('title') or '(tanpa judul)'}"
                )
                print("   ID     :", record.get("evidence_id", "-"))
                print("   Source :", record.get("source", "-"))
                print("   File   :", record.get("file_path", "-"))

        elif choice == "2":
            evidence_id = input("Evidence ID: ").strip()
            record = get_evidence_details(active_project_id, evidence_id)
            print("\\nDETAIL EVIDENCE")
            for field in (
                "evidence_id", "project_id", "evidence_type", "source",
                "title", "page_url", "file_path", "file_size", "sha256",
                "created_at", "related_finding_ids", "metadata",
            ):
                print(f"{field:20}: {record.get(field)}")

        elif choice == "3":
            evidence_id = input("Evidence ID screenshot: ").strip()
            record = get_evidence_details(active_project_id, evidence_id)
            if record.get("evidence_type") != "screenshot":
                print("Evidence yang dipilih bukan screenshot.")
                continue
            screenshot_path = resolve_evidence_path(active_project_id, evidence_id)
            start_file = getattr(os, "startfile", None)
            if start_file is None:
                print("Membuka file otomatis hanya didukung pada Windows.")
                continue
            start_file(str(screenshot_path))
            print("Screenshot dibuka:", screenshot_path)

        elif choice == "4":
            evidence_id = input("Evidence ID yang diverifikasi: ").strip()
            if verify_evidence(active_project_id, evidence_id):
                print("Hasil verifikasi: VALID (SHA-256 cocok).")
            else:
                print("Hasil verifikasi: TIDAK VALID (file hilang atau hash berbeda).")

        elif choice == "5":
            break
        else:
            print("Pilihan tidak valid.")

    return active_project_id


'''
if agent.count("def main():") != 1:
    raise SystemExit("Lokasi fungsi main tidak ditemukan.")
agent = agent.replace("def main():", viewer_function + "def main():", 1)

old_exit = '''            elif choice == "7":
                log_info(
                    "Menutup aplikasi",
                    "Pengguna menutup AI QA Assistant secara normal."
                )
                print("AI QA Assistant ditutup.")
                break
'''
new_exit = '''            elif choice == "8":
                active_project_id = run_evidence_viewer(active_project_id)

            elif choice == "9":
                log_info(
                    "Menutup aplikasi",
                    "Pengguna menutup AI QA Assistant secara normal."
                )
                print("AI QA Assistant ditutup.")
                break
'''
if agent.count(old_exit) != 1:
    raise SystemExit("Handler keluar menu utama tidak ditemukan.")
agent = agent.replace(old_exit, new_exit, 1)
agent_path.write_text(agent, encoding="utf-8", newline="")

# Update existing menu assertion.
menu_path = Path("tests/test_agent_menu_and_restriction.py")
menu = menu_path.read_text(encoding="utf-8")
old = '''        self.assertIn("6. Jalankan Authentication Discovery", menu)
        self.assertIn("7. Keluar", menu)
        self.assertNotIn("6. Keluar", menu)
'''
new = '''        self.assertIn("6. Jalankan Authentication Discovery", menu)
        self.assertIn("8. Evidence Viewer", menu)
        self.assertIn("9. Keluar", menu)
        self.assertNotIn("7. Keluar", menu)
'''
if menu.count(old) != 1:
    raise SystemExit("Assertion menu lama tidak ditemukan.")
menu_path.write_text(menu.replace(old, new, 1), encoding="utf-8", newline="")

# Add focused tests.
test_path = Path("tests/test_evidence_viewer.py")
if test_path.exists():
    raise SystemExit("tests/test_evidence_viewer.py sudah ada; tidak akan ditimpa.")
test_source = '''import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import evidence_viewer


class EvidenceViewerTests(unittest.TestCase):
    def test_list_project_evidence_returns_manager_records(self):
        expected = ({"evidence_id": "EV-1"},)
        with patch.object(evidence_viewer, "list_evidence", return_value=expected):
            self.assertEqual(evidence_viewer.list_project_evidence("PROJECT_A"), expected)

    def test_get_evidence_details_returns_matching_record(self):
        records = (
            {"evidence_id": "EV-1", "title": "Homepage"},
            {"evidence_id": "EV-2", "title": "Login"},
        )
        with patch.object(evidence_viewer, "list_evidence", return_value=records):
            self.assertEqual(
                evidence_viewer.get_evidence_details("PROJECT_A", "EV-2"),
                records[1],
            )

    def test_get_evidence_details_rejects_unknown_id(self):
        with patch.object(evidence_viewer, "list_evidence", return_value=()):
            with self.assertRaises(KeyError):
                evidence_viewer.get_evidence_details("PROJECT_A", "EV-MISSING")

    def test_resolve_evidence_path_stays_inside_project_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "PROJECT_A"
            screenshots = project_dir / "evidence" / "screenshots"
            screenshots.mkdir(parents=True)
            (project_dir / "project_config.json").write_text(
                json.dumps({"project_id": "PROJECT_A", "project_name": "Test", "base_url": "https://example.test/"}),
                encoding="utf-8",
            )
            screenshot = screenshots / "home.png"
            screenshot.write_bytes(b"image fixture")
            record = {"evidence_id": "EV-1", "file_path": "screenshots/home.png"}
            with (
                patch.object(evidence_viewer, "PROJECTS_DIR", root),
                patch.object(evidence_viewer, "list_evidence", return_value=(record,)),
            ):
                self.assertEqual(
                    evidence_viewer.resolve_evidence_path("PROJECT_A", "EV-1"),
                    screenshot.resolve(),
                )

    def test_resolve_evidence_path_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "PROJECT_A"
            evidence_dir = project_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            (project_dir / "project_config.json").write_text(
                json.dumps({"project_id": "PROJECT_A", "project_name": "Test", "base_url": "https://example.test/"}),
                encoding="utf-8",
            )
            (project_dir / "outside.png").write_bytes(b"outside")
            record = {"evidence_id": "EV-1", "file_path": "../outside.png"}
            with (
                patch.object(evidence_viewer, "PROJECTS_DIR", root),
                patch.object(evidence_viewer, "list_evidence", return_value=(record,)),
            ):
                with self.assertRaises(ValueError):
                    evidence_viewer.resolve_evidence_path("PROJECT_A", "EV-1")


if __name__ == "__main__":
    unittest.main()
'''
test_path.write_text(test_source, encoding="utf-8", newline="")

# Append documentation.
section = '''

## Evidence Viewer

Evidence Viewer dapat dibuka dari menu utama aplikasi. Viewer bekerja pada proyek
aktif; jika belum ada proyek aktif, pengguna diminta memilih proyek terlebih dahulu.
Fitur meliputi daftar evidence, detail metadata, membuka screenshot menggunakan
aplikasi bawaan Windows, dan verifikasi integritas SHA-256.

Viewer hanya membaca indeks dan file evidence. Viewer tidak menghapus, memindahkan,
atau mengubah evidence. Path file divalidasi agar tetap berada di dalam folder
evidence proyek. Attachment ditampilkan sebagai metadata dan tidak dibuka otomatis.
'''
for name in ("docs/PROJECT_SETUP_GUIDE.md", "docs/PORTABLE_SETUP_GUIDE.md"):
    path = Path(name)
    content = path.read_text(encoding="utf-8")
    if "## Evidence Viewer" in content:
        raise SystemExit(f"Bagian Evidence Viewer sudah ada: {name}")
    path.write_text(content.rstrip() + section, encoding="utf-8", newline="")

print("Evidence Viewer, integrasi menu, test, dan dokumentasi berhasil diterapkan.")
'@

Write-Host "`n=== APPLY PATCH ==="
$PatchScript | & $Python -
if ($LASTEXITCODE -ne 0) {
    throw "Patch gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== RUN FOCUSED TESTS ==="
& $Python -m unittest tests.test_evidence_viewer tests.test_agent_menu_and_restriction -v
if ($LASTEXITCODE -ne 0) {
    throw "Focused tests gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== COMPILE CHECK ==="
& $Python -m compileall -q core\evidence_viewer.py agent.py tests\test_evidence_viewer.py tests\test_agent_menu_and_restriction.py
if ($LASTEXITCODE -ne 0) {
    throw "Compile check gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== DIFF CHECK ==="
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check gagal. Backup tersedia di: $BackupDir"
}

Write-Host "`n=== IMPLEMENTATION SUMMARY ===" -ForegroundColor Green
Write-Host "Backup: $BackupDir"
Write-Host "Modul baru: core\evidence_viewer.py"
Write-Host "Test baru: tests\test_evidence_viewer.py"
Write-Host "Menu baru: 8. Evidence Viewer; 9. Keluar"
Write-Host "Focused tests, compile check, dan diff check selesai."
Write-Host "Full test suite dan live UI verification belum dijalankan."
