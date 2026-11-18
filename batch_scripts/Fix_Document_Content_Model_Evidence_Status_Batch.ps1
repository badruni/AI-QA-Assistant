#requires -Version 5.1
<#
AI QA Assistant - Document Content Model evidence-status fix
Run from repository root:
  .\batch_scripts\Fix_Document_Content_Model_Evidence_Status_Batch.ps1
#>
$ErrorActionPreference = "Stop"

$Required = @(
    ".\core\document_content_model.py",
    ".\tests\test_document_content_model.py"
)
foreach ($Path in $Required) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "File wajib tidak ditemukan: $Path"
    }
}

$Python = ".\.venv-scanner\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python scanner tidak ditemukan: $Python"
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = ".\backups\before_content_model_evidence_status_fix_$Stamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Copy-Item ".\core\document_content_model.py" (Join-Path $BackupDir "document_content_model.py")
Copy-Item ".\tests\test_document_content_model.py" (Join-Path $BackupDir "test_document_content_model.py")

$ModulePath = (Resolve-Path ".\core\document_content_model.py").Path
$ModuleText = [System.IO.File]::ReadAllText($ModulePath, [System.Text.Encoding]::UTF8)

$OldFunction = @'
    if not isinstance(evidence_ids, list):
        raise ValueError("evidence_ids harus berupa list.")
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not _ID_PATTERN.fullmatch(evidence_id):
            raise ValueError("Evidence ID tidak valid.")
    return {
'@

$NewFunction = @'
    if not isinstance(evidence_ids, list):
        raise ValueError("evidence_ids harus berupa list.")
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not _ID_PATTERN.fullmatch(evidence_id):
            raise ValueError("Evidence ID tidak valid.")
    if status in ("Passed", "Failed") and not evidence_ids:
        raise ValueError(
            "Status Passed atau Failed wajib memiliki minimal satu evidence_id."
        )
    return {
'@

if (-not $ModuleText.Contains($OldFunction)) {
    throw "Bagian fungsi yang akan diperbaiki tidak ditemukan. Tidak ada perubahan dilakukan."
}
$ModuleText = $ModuleText.Replace($OldFunction, $NewFunction)
[System.IO.File]::WriteAllText(
    $ModulePath, $ModuleText, (New-Object System.Text.UTF8Encoding($false))
)

$TestPath = (Resolve-Path ".\tests\test_document_content_model.py").Path
$TestText = [System.IO.File]::ReadAllText($TestPath, [System.Text.Encoding]::UTF8)

$OldTest = @'
    def test_test_case_status_is_not_inferred(self):
        case = model.make_test_case_block(
            "TC-001", "Login", "User masuk", "Belum dicoba",
            "Needs Review", ["EV-001"],
        )
        self.assertEqual(case["status"], "Needs Review")
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-002", "Login", "User masuk", "Tombol ditemukan",
                "Passed",
            )
'@

$NewTest = @'
    def test_test_case_status_is_not_inferred_and_pass_fail_require_evidence(self):
        case = model.make_test_case_block(
            "TC-001", "Login", "User masuk", "Belum dicoba",
            "Needs Review",
        )
        self.assertEqual(case["status"], "Needs Review")
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-002", "Login", "User masuk", "Tombol ditemukan",
                "Passed",
            )
        with self.assertRaises(ValueError):
            model.make_test_case_block(
                "TC-003", "Login", "User masuk", "Login gagal",
                "Failed",
            )

    def test_passed_and_failed_status_accept_evidence_reference(self):
        passed = model.make_test_case_block(
            "TC-004", "Login", "User masuk", "Login berhasil diamati",
            "Passed", ["EV-001"],
        )
        failed = model.make_test_case_block(
            "TC-005", "Login", "User masuk", "Pesan error diamati",
            "Failed", ["EV-002"],
        )
        self.assertEqual(passed["status"], "Passed")
        self.assertEqual(failed["status"], "Failed")
'@

if (-not $TestText.Contains($OldTest)) {
    throw "Test yang akan diperbarui tidak ditemukan. File module sudah diperbaiki; test tidak diubah."
}
$TestText = $TestText.Replace($OldTest, $NewTest)
[System.IO.File]::WriteAllText(
    $TestPath, $TestText, (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "`n========== FOCUSED TESTS ==========" -ForegroundColor Cyan
& $Python -m unittest tests.test_document_content_model -v
if ($LASTEXITCODE -ne 0) {
    throw "Focused tests gagal. Backup: $BackupDir"
}

Write-Host "`n========== SYNTAX CHECK ==========" -ForegroundColor Cyan
& $Python -m py_compile .\core\document_content_model.py .\tests\test_document_content_model.py
if ($LASTEXITCODE -ne 0) {
    throw "Syntax check gagal. Backup: $BackupDir"
}

Write-Host "`n========== DIFF CHECK ==========" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check menemukan masalah. Backup: $BackupDir"
}

Write-Host "`n========== FIX COMPLETED ==========" -ForegroundColor Green
Write-Host "Focused tests, syntax check, dan diff check berhasil."
Write-Host "Backup: $BackupDir"
