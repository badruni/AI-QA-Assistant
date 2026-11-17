#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
$Files = @('agent.py','modules\generic_uat_inspection.py','tests\test_generic_uat_inspection.py','docs\PROJECT_SETUP_GUIDE.md','docs\PORTABLE_SETUP_GUIDE.md')
foreach ($f in $Files) { if (-not (Test-Path (Join-Path $Root $f))) { throw "File tidak ditemukan: $f. Jalankan dari root proyek." } }
$Python = Join-Path $Root '.venv-scanner\Scripts\python.exe'
if (-not (Test-Path $Python)) { throw "Python scanner tidak ditemukan: $Python" }
$BackupName = 'before_generic_uat_review_fixes_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$Backup = Join-Path $Root "backups\$BackupName"
New-Item -ItemType Directory -Path $Backup -Force | Out-Null
foreach ($f in $Files) {
  $dst = Join-Path $Backup $f
  New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
  Copy-Item (Join-Path $Root $f) $dst
}
Write-Host "Backup dibuat: $Backup" -ForegroundColor Green

$Patch = @'
from pathlib import Path

def patch(file, old, new, label):
    p = Path(file)
    s = p.read_text(encoding="utf-8-sig")
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f"{file}: pola {label!r} ditemukan {n} kali; patch dibatalkan.")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

patch("agent.py",
"""        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if not discovery.pages:
""",
"""        print("Discovery status:", discovery.status.value)
        print("Halaman ditemukan:", len(discovery.pages))

        if discovery.status == ResultStatus.ACCESS_RESTRICTED:
            print("\\nGeneric UAT dihentikan karena Website Discovery mendeteksi pembatasan akses.")
            log_warning(
                "Generic UAT Inspection",
                "Tahap dilewati karena Website Discovery berstatus Access Restricted."
            )
            return active_project_id

        if not discovery.pages:
""", "agent restricted guard")

patch("modules/generic_uat_inspection.py",
"""    if discovery_result.project_id != config.project_id:
        raise ValueError("Project ID hasil Discovery tidak sesuai konfigurasi.")

    discovered_pages = [
""",
"""    if discovery_result.project_id != config.project_id:
        raise ValueError("Project ID hasil Discovery tidak sesuai konfigurasi.")

    if discovery_result.status == ResultStatus.ACCESS_RESTRICTED:
        reason = (
            discovery_result.stopped_reason
            or "Website Discovery berstatus Access Restricted."
        )
        return GenericUATResult(
            project_id=config.project_id,
            status=ResultStatus.ACCESS_RESTRICTED,
            pages=(),
            findings=(),
            completed=False,
            stopped_reason=reason,
            message=(
                "Generic UAT tidak dijalankan karena Website Discovery "
                "mengalami pembatasan akses."
            ),
        )

    discovered_pages = [
""", "module restricted guard")

patch("modules/generic_uat_inspection.py",
"""            const text = (el.innerText || '').trim();
            return !!(aria || title || labelledBy || text);
""",
"""            const text = (el.innerText || '').trim();
            const imageAlt = [...el.querySelectorAll('img')]
                .some(img => (img.getAttribute('alt') || '').trim());
            return !!(aria || title || labelledBy || text || imageAlt);
""", "image alt accessible name")

patch("modules/generic_uat_inspection.py",
"""        const inputs = all(
            'input:not([type="hidden"]), textarea, select, [contenteditable="true"]'
        ).filter(visible);
""",
"""        const inputs = all(
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="image"]), textarea, select, [contenteditable="true"]'
        ).filter(visible);
""", "exclude button-like inputs")

patch("modules/generic_uat_inspection.py",
"""                return !((el.value || el.getAttribute('aria-label') ||
                    el.getAttribute('title') || '').trim());
""",
"""                return !((el.getAttribute('value') ||
                    el.getAttribute('aria-label') ||
                    el.getAttribute('title') || '').trim());
""", "do not read live input value")

patch("tests/test_generic_uat_inspection.py",
"""    def _discovery(self, path, status=ResultStatus.PASSED):
""",
"""    def _discovery(
        self,
        path,
        status=ResultStatus.PASSED,
        discovery_status=ResultStatus.PASSED,
        stopped_reason="",
    ):
""", "discovery helper")

patch("tests/test_generic_uat_inspection.py",
"""            status=ResultStatus.PASSED,
            pages=(discovered,),
            max_pages=20,
            completed=True,
            stopped_reason="",
""",
"""            status=discovery_status,
            pages=(discovered,),
            max_pages=20,
            completed=discovery_status == ResultStatus.PASSED,
            stopped_reason=stopped_reason,
""", "discovery result status")

patch("tests/test_generic_uat_inspection.py",
"""    def test_rejects_discovery_from_another_project(self):
""",
"""    def test_does_not_inspect_pages_when_discovery_was_access_restricted(self):
        result = inspect_generic_uat(
            self.config,
            self._discovery(
                "/review",
                discovery_status=ResultStatus.ACCESS_RESTRICTED,
                stopped_reason="Batas HTTP 403 tercapai.",
            ),
        )
        self.assertEqual(result.status, ResultStatus.ACCESS_RESTRICTED)
        self.assertFalse(result.completed)
        self.assertEqual(result.pages, ())
        self.assertEqual(result.findings, ())
        self.assertIn("403", result.stopped_reason)
        self.assertEqual(self.hits, {})

    def test_rejects_discovery_from_another_project(self):
""", "restricted discovery test")

patch("tests/test_generic_uat_inspection.py",
"""                        "<img src='/pixel' alt='Small logo'>"
                        "<form><label for='email'>Email</label>"
                        "<input id='email' type='email'></form>"
""",
"""                        "<img src='/pixel' alt='Small logo'>"
                        "<a href='/clean'><img src='/pixel' alt='Linked logo'></a>"
                        "<form><label for='email'>Email</label>"
                        "<input id='email' type='email'>"
                        "<input type='button' value='Cancel'>"
                        "<input type='submit' value='Send'></form>"
""", "fixture accessible image and button inputs")

patch("tests/test_generic_uat_inspection.py",
"""        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.findings, ())

    def test_403_stops_inspection(self):
""",
"""        self.assertEqual(result.status, ResultStatus.PASSED)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.pages[0].component_summary["inputs_without_label"], 0)
        self.assertEqual(result.pages[0].component_summary["links_without_name"], 0)

    def test_403_stops_inspection(self):
""", "heuristic assertions")

patch("docs/PROJECT_SETUP_GUIDE.md",
"""- Tahap ini belum membuktikan alur bisnis atau perilaku interaktif.
""",
"""- Tahap ini belum membuktikan alur bisnis atau perilaku interaktif.
- Jika Website Discovery berstatus `Access Restricted`, Generic UAT tidak dijalankan.
- Accessible name tautan memperhitungkan teks alternatif gambar di dalam tautan.
- Input bertipe button, submit, reset, dan image tidak dihitung sebagai field yang membutuhkan label.
- Pemeriksaan accessible name/label merupakan heuristik awal, bukan implementasi penuh perhitungan nama aksesibel WCAG.
""", "project guide")

patch("docs/PORTABLE_SETUP_GUIDE.md",
"""dan perlu validasi lanjutan sebelum disebut bug.
""",
"""dan perlu validasi lanjutan sebelum disebut bug. Jika Website Discovery berstatus
`Access Restricted`, tahap Generic UAT dilewati. Heuristik accessible name/label
bersifat awal dan bukan implementasi penuh perhitungan nama aksesibel WCAG.
""", "portable guide")

print("Seluruh patch berhasil diterapkan.")
'@

$Patch | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Patch gagal. Backup tersedia: $Backup" }

Write-Host "`n=== COMPILE CHECK ===" -ForegroundColor Cyan
& $Python -m py_compile .\agent.py .\modules\generic_uat_inspection.py .\tests\test_generic_uat_inspection.py
if ($LASTEXITCODE -ne 0) { throw "Compile gagal. Backup: $Backup" }
Write-Host "`n=== FOCUSED TESTS ===" -ForegroundColor Cyan
& $Python -m unittest tests.test_generic_uat_inspection -v
if ($LASTEXITCODE -ne 0) { throw "Focused tests gagal. Jangan commit. Backup: $Backup" }
Write-Host "`n=== DIFF CHECK ===" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check gagal. Backup: $Backup" }
Write-Host "`n=== GIT STATUS ===" -ForegroundColor Cyan
git status -sb
Write-Host "`n=== CHANGE SUMMARY ===" -ForegroundColor Cyan
git diff --stat
Write-Host "`nSelesai. Backup: $Backup" -ForegroundColor Green
Write-Host "Belum ada commit atau push."
