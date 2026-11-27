# Checkpoint B - Finalize browser verification and documentation
$ErrorActionPreference = "Stop"

$Root = "C:\Users\RBZ-NB-0004\Projects\AI-QA-Assistant"
if ((Get-Location).Path.TrimEnd('\') -ne $Root.TrimEnd('\')) {
    throw "Jalankan dari folder repository: $Root"
}

$Doc = Join-Path $Root "docs\Checkpoint_B_Component_Detection_Stabilization_2026-11-27.md"
$Test = Join-Path $Root "tests\test_qa_playground_component_detection.py"

if (-not (Test-Path -LiteralPath $Doc)) { throw "Dokumentasi Checkpoint B tidak ditemukan: $Doc" }
if (-not (Test-Path -LiteralPath $Test)) { throw "Regression test Checkpoint B tidak ditemukan: $Test" }

$Text = [System.IO.File]::ReadAllText($Doc)
$Marker = "## Status`r`n`r`nImplementasi batch: menunggu verifikasi pengguna."
if (-not $Text.Contains($Marker)) {
    $Marker = "## Status`n`nImplementasi batch: menunggu verifikasi pengguna."
}
if (-not $Text.Contains($Marker)) {
    throw "Dokumen tidak memiliki marker status yang diharapkan. Tidak ada perubahan dilakukan."
}

$BackupRoot = Join-Path $env:USERPROFILE "AI_QA_Assistant_Backups"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $BackupRoot "before_checkpoint_b_documentation_finalize_$Stamp"
New-Item -ItemType Directory -Path $Backup -Force | Out-Null
Copy-Item -LiteralPath $Doc -Destination (Join-Path $Backup (Split-Path $Doc -Leaf))

$Results = @'
## Browser verification — 27 November 2026

### Runtime summary

| Metric | Verified result |
|---|---:|
| Component records | 57 |
| Runtime DETECTED | 22 |
| Runtime NOT DETECTED | 17 |
| Runtime NEEDS REVIEW | 18 |
| Expectation MATCH | 33 |
| Expectation MISMATCH | 0 |
| Expectation REVIEW | 24 |
| Scenario registry | 72 |
| Executed | 57 |
| Checks Passed | 33 |

### Shared-selector spot checks

| Component | Source | Runtime | Expectation | Observation |
|---|---|---|---|---|
| CMP-001 Header | IMPLEMENTED | DETECTED | MATCH | Specific navigation/top-action selectors remain available |
| CMP-003 Hamburger Menu | IMPLEMENTED | DETECTED | MATCH | Specific open/close/drawer selectors remain available |
| CMP-017 Highlights Section | IMPLEMENTED | DETECTED | MATCH | Specific highlights/list selectors remain available |
| CMP-018 Category Card | PARTIAL | NEEDS REVIEW | REVIEW | Shared highlight-card evidence is not treated as unique |
| CMP-030 Gallery Section | IMPLEMENTED | NEEDS REVIEW | REVIEW | Matching candidates are shared; manual review required |
| CMP-035 Expand / Collapse | PARTIAL | DETECTED | REVIEW | Drawer state is detected, but does not prove a reusable disclosure pattern |
| CMP-039 Modal / Popup | IMPLEMENTED | DETECTED | MATCH | Specific image-modal selectors remain available |
| CMP-043 Article Card | PARTIAL | NEEDS REVIEW | REVIEW | Shared highlight-card evidence is insufficient |
| CMP-045 Content Grid | PARTIAL | NEEDS REVIEW | REVIEW | Shared grid evidence is insufficient |
| CMP-048 Gallery Image Viewer | IMPLEMENTED | DETECTED | MATCH | Specific media-open evidence remains available |
| CMP-049 Responsive Header | IMPLEMENTED | NEEDS REVIEW | REVIEW | Matching topbar evidence is shared |
| CMP-052 Responsive Grid | IMPLEMENTED | DETECTED | MATCH | Multiple grid candidates provide evidence beyond the shared gallery selector |
| CMP-056 Responsive Gallery | IMPLEMENTED | NEEDS REVIEW | REVIEW | Only the shared gallery-grid candidate matched |

### Interpretation and limitations

- Browser verification confirms the detector's current classification output for the listed components.
- `DETECTED` and `MATCH` are inventory/detection outcomes only; they do not establish that component behavior passes.
- Responsive overflow, content fit, image crop, tap targets, modal sizing, keyboard behavior, and interaction behavior remain untested unless separately executed and evidenced.
- CMP-033 Hover Interaction remains detection-only; hover behavior and keyboard equivalent remain `NOT TESTED`.
- The 57 executed figure is the Playground dashboard's displayed count. It must not be interpreted as 57 successful behavior tests.
- Runtime distribution is expected to differ from Checkpoint A because shared-selector ambiguity is now surfaced for manual review.

## Status

Checkpoint B — Component Detection Stabilization: browser verification completed for the agreed shared-selector spot-check set. Static regression: 7/7 PASS. JavaScript syntax check: PASS. Acceptance is limited to detection stabilization; behavior testing remains outside this checkpoint.

Git commit and push: pending user approval.
'@

$NewText = $Text.Replace($Marker, $Results.TrimEnd())
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Doc, $NewText, $Utf8NoBom)

try {
    Write-Host "`n========== CHECKPOINT B TARGETED REGRESSION ==========" -ForegroundColor Cyan
    python -m unittest discover -s tests -p "test_qa_playground_component_detection.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Targeted Checkpoint B regression failed." }

    Write-Host "`n========== FULL PROJECT UNIT TEST SUITE ==========" -ForegroundColor Cyan
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Full project unit test suite failed." }

    Write-Host "`n========== DOCUMENTATION VERIFICATION ==========" -ForegroundColor Cyan
    Select-String -Path $Doc -Pattern "Runtime DETECTED|CMP-052 Responsive Grid|CMP-056 Responsive Gallery|Checkpoint B — Component Detection Stabilization"
    Write-Host "`nDocumentation finalized. Backup: $Backup" -ForegroundColor Green
    Write-Host "Tests passed. Git commit/push has NOT been performed." -ForegroundColor Green
}
catch {
    Write-Host "`nFinalization verification failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Dokumentasi sudah diubah; backup tersedia di: $Backup" -ForegroundColor Yellow
    Write-Host "Jangan commit/push sebelum kegagalan ditinjau." -ForegroundColor Yellow
    throw
}
