# Checkpoint B - Component Detection Stabilization
# Generated from source-package analysis on 2026-11-27.
# Run from the AI-QA-Assistant repository root in PowerShell.

$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$AppPath = Join-Path $ProjectRoot "local_test_site\playground\assets\app.js"
$TestPath = Join-Path $ProjectRoot "tests\test_qa_playground_component_detection.py"
$DocPath = Join-Path $ProjectRoot "docs\Checkpoint_B_Component_Detection_Stabilization_2026-11-27.md"
foreach ($path in @($AppPath, (Split-Path $TestPath -Parent), (Split-Path $DocPath -Parent))) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Prasyarat tidak ditemukan: $path" }
}

$BackupRoot = Join-Path $env:USERPROFILE "AI_QA_Assistant_Backups"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupPath = Join-Path $BackupRoot "before_checkpoint_b_component_stabilization_$Stamp"
New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

$AppBackup = Join-Path $BackupPath "app.js"
Copy-Item -LiteralPath $AppPath -Destination $AppBackup

$TestExisted = Test-Path -LiteralPath $TestPath
$DocExisted = Test-Path -LiteralPath $DocPath
if ($TestExisted) { Copy-Item -LiteralPath $TestPath -Destination (Join-Path $BackupPath "test_qa_playground_component_detection.py") }
if ($DocExisted) { Copy-Item -LiteralPath $DocPath -Destination (Join-Path $BackupPath "Checkpoint_B_Component_Detection_Stabilization_2026-11-27.md") }

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Replace-ExactlyOnce {
    param(
        [string]$Text,
        [string]$Old,
        [string]$New,
        [string]$Description
    )
    $count = ([regex]::Matches($Text, [regex]::Escape($Old))).Count
    if ($count -ne 1) {
        throw "Patch dibatalkan: '$Description' ditemukan $count kali; diharapkan tepat satu."
    }
    return $Text.Replace($Old, $New)
}

$AppOriginal = [System.IO.File]::ReadAllText($AppPath)
$AppUpdated = $AppOriginal

try {
    # 1. Correct CSS :hover selector normalization.
    $AppUpdated = Replace-ExactlyOnce `
        $AppUpdated `
        'const base=raw.replace(/:hover\\b/g,"").trim();' `
        'const base=raw.replace(/:hover\b/g,"").trim();' `
        "CSS hover word-boundary normalization"

    # 2. Build selector ownership metadata once, so selectors reused by multiple
    # component records are not treated as unique evidence.
    $OwnerAnchor = @'
];
 const qaScenarios = [
'@
    $OwnerReplacement = @'
];
 const qaSelectorOwners=new Map();
 qaComponents.forEach(component=>{
   (component.selector_candidates||[]).forEach(selector=>{
     const owners=qaSelectorOwners.get(selector)||[];
     if(!owners.includes(component.id))owners.push(component.id);
     qaSelectorOwners.set(selector,owners);
   });
 });
 const qaScenarios = [
'@
    $AppUpdated = Replace-ExactlyOnce $AppUpdated $OwnerAnchor $OwnerReplacement "selector owner index"

    # 3. Attach selector ownership and ambiguity to each DOM match.
    $MatchOld = 'if(found.length)matches.push({selector,count:found.length,signal:"dom_selector"});'
    $MatchNew = @'
if(found.length){
           const owners=qaSelectorOwners.get(selector)||[];
           matches.push({selector,count:found.length,signal:"dom_selector",owners,ambiguous:owners.length>1});
         }
'@
    $AppUpdated = Replace-ExactlyOnce $AppUpdated $MatchOld $MatchNew "DOM match ownership metadata"

    # 4. Treat exclusively shared-selector evidence as needs_review, not a
    # confident detection. Preserve specific partial/static classifications.
    $ClassificationOld = '    let runtimeStatus;'
    $ClassificationNew = @'
    const hasUnambiguousMatch=matches.some(match=>!match.ambiguous);
    if(matches.some(match=>match.ambiguous)){
      notes.push("Sebagian selector digunakan oleh lebih dari satu record komponen; bukti tersebut tidak dianggap unik.");
    }
    if(matches.length&&!hasUnambiguousMatch){
      classification="ambiguous_candidate";
      notes.push("Seluruh kandidat yang cocok dipakai bersama oleh beberapa komponen; perlu review manual sebelum dianggap terdeteksi.");
    }
    let runtimeStatus;
'@
    $AppUpdated = Replace-ExactlyOnce $AppUpdated $ClassificationOld $ClassificationNew "ambiguous candidate evaluation"

    $RuntimeOld = @'
    if(invalid.length)runtimeStatus="needs_review";
    else if(component.id==="CMP-033"&&!hoverInspectable&&!matches.some(m=>m.signal==="css_hover_rule"))runtimeStatus="needs_review";
    else if(matches.length)runtimeStatus="detected";
'@
    $RuntimeNew = @'
     if(invalid.length)runtimeStatus="needs_review";
     else if(component.id==="CMP-033"&&!hoverInspectable&&!matches.some(m=>m.signal==="css_hover_rule"))runtimeStatus="needs_review";
     else if(matches.length&&!hasUnambiguousMatch)runtimeStatus="needs_review";
     else if(matches.length)runtimeStatus="detected";
'@
    $AppUpdated = Replace-ExactlyOnce $AppUpdated $RuntimeOld $RuntimeNew "ambiguous runtime status"

    # 5. Remove the preliminary detection pass. qaRunScenario already performs
    # detection and evaluation, so the previous handler scanned every component twice.
    $DuplicateScanOld = '   qaComponents.forEach(qaDetectComponent);qaRenderCatalog(document.getElementById("qaCatalogSearch").value);'
    $DuplicateScanNew = '    qaRenderCatalog(document.getElementById("qaCatalogSearch").value);'
    $AppUpdated = Replace-ExactlyOnce $AppUpdated $DuplicateScanOld $DuplicateScanNew "duplicate catalog scan removal"

    $TestContent = @'
import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_JS = PROJECT_ROOT / "local_test_site" / "playground" / "assets" / "app.js"


class PlaygroundComponentDetectionStabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_JS.read_text(encoding="utf-8")
        match = re.search(
            r"const qaComponents\s*=\s*(\[.*?\]);\s*\n\s*const qaSelectorOwners",
            cls.source,
            re.S,
        )
        if not match:
            raise AssertionError("Component catalog block was not found.")
        cls.components = json.loads(match.group(1))

    def test_catalog_has_57_unique_component_records(self):
        self.assertEqual(len(self.components), 57)
        ids = [component["id"] for component in self.components]
        self.assertEqual(len(ids), len(set(ids)))

    def test_source_inventory_distribution_is_preserved(self):
        statuses = [component["source_status"] for component in self.components]
        self.assertEqual(statuses.count("implemented"), 21)
        self.assertEqual(statuses.count("partial"), 19)
        self.assertEqual(statuses.count("not_implemented"), 17)

    def test_every_component_has_nonempty_selector_candidates(self):
        for component in self.components:
            candidates = component.get("selector_candidates", [])
            self.assertTrue(candidates, component["id"])
            self.assertTrue(all(isinstance(item, str) and item.strip() for item in candidates),
                            component["id"])

    def test_shared_selector_ownership_is_recorded(self):
        self.assertIn("const qaSelectorOwners=new Map()", self.source)
        self.assertIn("ambiguous:owners.length>1", self.source)
        self.assertIn("matches.length&&!hasUnambiguousMatch", self.source)

    def test_hover_selector_normalization_uses_word_boundary(self):
        self.assertIn(r'raw.replace(/:hover\b/g,"").trim()', self.source)
        self.assertNotIn(r'raw.replace(/:hover\\b/g,"").trim()', self.source)

    def test_catalog_button_does_not_run_detection_twice(self):
        self.assertNotIn(
            "qaComponents.forEach(qaDetectComponent);qaRenderCatalog",
            self.source,
        )
        self.assertIn(
            'qaRunScenario(qaScenarios.find(s=>s.component_scan&&s.component_id===c.id))',
            self.source,
        )

    def test_expectation_and_behavior_remain_separate(self):
        self.assertIn('component.behavior_status=component.behavior_status||"not_tested"', self.source)
        self.assertIn('behavior_status:component.behavior_status||"not_tested"', self.source)
        self.assertIn("expectation_status", self.source)


if __name__ == "__main__":
    unittest.main()
'@

    $DocContent = @'
# Checkpoint B — Component Detection Stabilization

Tanggal: 27 November 2026

## Tujuan

Menstabilkan bukti deteksi komponen pada Living QA Playground tanpa mengubah source inventory dan tanpa menyamakan deteksi dengan pengujian perilaku.

## Temuan analisis source sebelum batch

- Katalog berisi 57 record unik: 21 `implemented`, 19 `partial`, dan 17 `not_implemented`.
- Terdapat 108 entri selector kandidat dan 83 selector unik.
- Terdapat 13 selector yang digunakan bersama oleh lebih dari satu record komponen.
- Handler `Scan DOM catalog` menjalankan `qaDetectComponent` pada seluruh katalog, lalu memanggil `qaRunScenario` untuk setiap komponen. Executor skenario juga menjalankan `qaDetectComponent`, sehingga deteksi dilakukan dua kali.
- Normalisasi selector CSS hover menggunakan pola regex dengan backslash ganda sebelum `b`; pola tersebut tidak mewakili word-boundary JavaScript yang dimaksud.
- Sebelum batch ini belum tersedia test otomatis khusus untuk integritas katalog dan aturan deteksi QA Playground.

## Perubahan batch

1. Memperbaiki normalisasi selector `:hover` menggunakan word-boundary yang benar.
2. Membuat indeks kepemilikan selector berdasarkan seluruh katalog.
3. Menambahkan metadata `owners` dan `ambiguous` pada bukti selector DOM.
4. Jika seluruh selector yang cocok dipakai bersama oleh beberapa record komponen, runtime menjadi `needs_review`, bukan `detected`.
5. Jika ada bukti selector unik, deteksi tetap dapat menjadi `detected`; selector bersama tetap dicatat sebagai catatan.
6. Menghapus preliminary detection pass agar setiap component scenario menjalankan detector satu kali.
7. Menambahkan static regression tests untuk jumlah/keunikan katalog, distribusi source status, selector, hover regex, duplicate scan, dan pemisahan expectation/behavior.

## Batasan interpretasi

- `detected` tetap berarti kandidat selector ditemukan, bukan perilaku komponen lulus.
- `needs_review` berarti bukti tidak unik atau pemeriksaan tidak konklusif.
- Selector unik pun belum membuktikan interaksi, aksesibilitas, atau responsivitas berfungsi.
- Perubahan ini dapat mengubah distribusi runtime dan expectation dibandingkan Checkpoint A. Angka baru hanya boleh dicatat setelah scan browser aktual dijalankan.
- Static regression tests tidak menggantikan verifikasi browser runtime.

## Verifikasi yang harus dijalankan

1. `python -m unittest discover -s tests -p "test_qa_playground_component_detection.py" -v`
2. Jika Node.js tersedia: `node --check .\local_test_site\playground\assets\app.js`
3. Jalankan Playground dan klik `Scan DOM catalog` satu kali.
4. Periksa komponen yang sebelumnya menggunakan selector bersama, termasuk CMP-001/CMP-049, CMP-003/CMP-035, CMP-017/CMP-018/CMP-043, CMP-030/CMP-045/CMP-052/CMP-056, dan CMP-039/CMP-048.
5. Pastikan CMP-033 tetap dapat menemukan CSS hover evidence, tetapi `behavior_status` dan `keyboard_equivalent_status` tetap `not_tested`.
6. Pastikan hasil scan menghasilkan satu record per component scenario, tanpa scan pendahuluan ganda.

## Rollback

Backup source dibuat di luar repository pada:
`%USERPROFILE%\AI_QA_Assistant_Backups\before_checkpoint_b_component_stabilization_<timestamp>`

Jika verifikasi gagal, pulihkan `app.js` dari backup tersebut dan hapus hanya file test/dokumen baru yang dibuat oleh batch ini. Jangan menghapus data proyek, evidence, laporan, atau backup.

## Status

Implementasi batch: menunggu verifikasi pengguna.
'@

    [System.IO.File]::WriteAllText($AppPath, $AppUpdated, $Utf8NoBom)
    [System.IO.File]::WriteAllText($TestPath, $TestContent, $Utf8NoBom)
    [System.IO.File]::WriteAllText($DocPath, $DocContent, $Utf8NoBom)

    Write-Host "`n========== STATIC VERIFICATION ==========" -ForegroundColor Cyan
    python -m unittest discover -s tests -p "test_qa_playground_component_detection.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Static regression tests gagal." }

    $Node = Get-Command node -ErrorAction SilentlyContinue
    if ($Node) {
        node --check ".\local_test_site\playground\assets\app.js"
        if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax check gagal." }
        Write-Host "Node.js syntax check: PASS" -ForegroundColor Green
    }
    else {
        Write-Host "Node.js tidak ditemukan; syntax check dilewati. Jalankan browser verification." -ForegroundColor Yellow
    }

    Write-Host "`n========== BATCH RESULT ==========" -ForegroundColor Green
    Write-Host "Backup : $BackupPath"
    Write-Host "Updated: local_test_site\playground\assets\app.js"
    Write-Host "Added  : tests\test_qa_playground_component_detection.py"
    Write-Host "Added  : docs\Checkpoint_B_Component_Detection_Stabilization_2026-11-27.md"
    Write-Host "Status : STATIC VERIFICATION PASSED. Browser verification is still required."
}
catch {
    Write-Host "`nBatch gagal: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Memulihkan file source dari backup..." -ForegroundColor Yellow
    Copy-Item -LiteralPath $AppBackup -Destination $AppPath -Force
    if (-not $TestExisted -and (Test-Path -LiteralPath $TestPath)) { Remove-Item -LiteralPath $TestPath -Force }
    if (-not $DocExisted -and (Test-Path -LiteralPath $DocPath)) { Remove-Item -LiteralPath $DocPath -Force }
    throw
}
