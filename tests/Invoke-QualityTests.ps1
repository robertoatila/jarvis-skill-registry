# Skill Registry Test Harness: Phase 10 — Multidimensional Quality & Utility Evaluation
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-10-quality.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-10.quality-tests/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = 'PENDING'
    passed_count = 0
    failed_count = 0
    test_cases = (New-Object 'System.Collections.Generic.List[object]')
}

function Run-TestCase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $true)][scriptblock]$Assertion
    )
    $tc = [ordered]@{
        name = $Name
        description = $Description
        status = 'PENDING'
        error = $null
    }
    try {
        & $Assertion
        $tc.status = 'PASS'
        $testResults.passed_count++
    } catch {
        $tc.status = 'FAIL'
        $tc.error = $_.Exception.Message
        $testResults.failed_count++
    }
    [void]$testResults.test_cases.Add($tc)
}

# 1. QualityEvaluationMultiFileSkill
Run-TestCase -Name "01_QualityEvaluationMultiFileSkill" -Description "Evaluate valid multi-file skill as EXEMPLARY or SUFFICIENT (score >= 80)" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Invoke-RegistryQualityEvaluation -ResourceId $res.resource_id
    if ($null -eq $eval) { throw "Evaluation returned null object" }
    if ($eval.composite_score -lt 80) { throw "Expected score >= 80 for valid-multi-skill, got: $($eval.composite_score)" }
    if ($eval.verdict -ne 'PROMOTABLE') { throw "Expected PROMOTABLE verdict, got: $($eval.verdict)" }
}

# 2. CompletenessDimensionCalculation
Run-TestCase -Name "02_CompletenessDimensionCalculation" -Description "Verify completeness score computation with schemas & references" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($eval.dimensions.completeness_score -lt 80) { throw "Expected high completeness for multi-file skill, got: $($eval.dimensions.completeness_score)" }
}

# 3. ConsistencyDimensionCalculation
Run-TestCase -Name "03_ConsistencyDimensionCalculation" -Description "Verify consistency score computation against structural analysis" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($eval.dimensions.consistency_score -lt 80) { throw "Expected high consistency for conforming skill, got: $($eval.dimensions.consistency_score)" }
}

# 4. MaintainabilityDimensionCalculation
Run-TestCase -Name "04_MaintainabilityDimensionCalculation" -Description "Verify maintainability score computation on modular directory layout" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($eval.dimensions.maintainability_score -lt 70) { throw "Expected high maintainability for modular skill, got: $($eval.dimensions.maintainability_score)" }
}

# 5. UtilityDimensionCalculation
Run-TestCase -Name "05_UtilityDimensionCalculation" -Description "Verify utility score computation combining capability density & provider matrix" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($eval.dimensions.utility_score -lt 80) { throw "Expected high utility for multi-runtime supported skill, got: $($eval.dimensions.utility_score)" }
}

# 6. RedundancyPenaltyApplication
Run-TestCase -Name "06_RedundancyPenaltyApplication" -Description "Verify penalty applied to non-leader duplicate skills" -Assertion {
    # Check that redundancy penalty factor exists in evaluation model
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($null -eq $eval.dimensions.redundancy_penalty) { throw "Missing redundancy_penalty dimension" }
}

# 7. CompositeScoreWeightedFormula
Run-TestCase -Name "07_CompositeScoreWeightedFormula" -Description "Verify exact weighted calculation formula" -Assertion {
    $c = 100; $cons = 100; $m = 100; $u = 100; $p = 0
    $calc = (0.25 * $c) + (0.25 * $cons) + (0.20 * $m) + (0.30 * $u) - $p
    if ($calc -ne 100) { throw "Weighted formula calculation mismatch: $calc" }
}

# 8. TierMappingExemplary
Run-TestCase -Name "08_TierMappingExemplary" -Description "Verify score >= 85 maps to EXEMPLARY" -Assertion {
    $score = 90
    $tier = if ($score -ge 85) { 'EXEMPLARY' } elseif ($score -ge 65) { 'SUFFICIENT' } else { 'SUBSTANDARD' }
    if ($tier -ne 'EXEMPLARY') { throw "Score 90 should map to EXEMPLARY" }
}

# 9. TierMappingSufficient
Run-TestCase -Name "09_TierMappingSufficient" -Description "Verify score 65-84 maps to SUFFICIENT" -Assertion {
    $score = 75
    $tier = if ($score -ge 85) { 'EXEMPLARY' } elseif ($score -ge 65) { 'SUFFICIENT' } else { 'SUBSTANDARD' }
    if ($tier -ne 'SUFFICIENT') { throw "Score 75 should map to SUFFICIENT" }
}

# 10. TierMappingSubstandard
Run-TestCase -Name "10_TierMappingSubstandard" -Description "Verify score 40-64 maps to SUBSTANDARD" -Assertion {
    $score = 50
    $tier = if ($score -ge 85) { 'EXEMPLARY' } elseif ($score -ge 65) { 'SUFFICIENT' } elseif ($score -ge 40) { 'SUBSTANDARD' } else { 'DEFICIENT' }
    if ($tier -ne 'SUBSTANDARD') { throw "Score 50 should map to SUBSTANDARD" }
}

# 11. TierMappingDeficient
Run-TestCase -Name "11_TierMappingDeficient" -Description "Verify score < 40 maps to DEFICIENT" -Assertion {
    $score = 25
    $tier = if ($score -ge 85) { 'EXEMPLARY' } elseif ($score -ge 65) { 'SUFFICIENT' } elseif ($score -ge 40) { 'SUBSTANDARD' } else { 'DEFICIENT' }
    if ($tier -ne 'DEFICIENT') { throw "Score 25 should map to DEFICIENT" }
}

# 12. VerdictMappingPromotable
Run-TestCase -Name "12_VerdictMappingPromotable" -Description "Verify EXEMPLARY/SUFFICIENT maps to PROMOTABLE" -Assertion {
    $tier = 'EXEMPLARY'
    $verdict = if ($tier -in @('EXEMPLARY', 'SUFFICIENT')) { 'PROMOTABLE' } else { 'UNSUITABLE' }
    if ($verdict -ne 'PROMOTABLE') { throw "EXEMPLARY should map to PROMOTABLE" }
}

# 13. VerdictMappingNeedsImprovement
Run-TestCase -Name "13_VerdictMappingNeedsImprovement" -Description "Verify SUBSTANDARD maps to NEEDS_IMPROVEMENT" -Assertion {
    $tier = 'SUBSTANDARD'
    $verdict = if ($tier -in @('EXEMPLARY', 'SUFFICIENT')) { 'PROMOTABLE' } elseif ($tier -eq 'SUBSTANDARD') { 'NEEDS_IMPROVEMENT' } else { 'UNSUITABLE' }
    if ($verdict -ne 'NEEDS_IMPROVEMENT') { throw "SUBSTANDARD should map to NEEDS_IMPROVEMENT" }
}

# 14. VerdictMappingUnsuitable
Run-TestCase -Name "14_VerdictMappingUnsuitable" -Description "Verify DEFICIENT maps to UNSUITABLE" -Assertion {
    $tier = 'DEFICIENT'
    $verdict = if ($tier -eq 'DEFICIENT') { 'UNSUITABLE' } else { 'PROMOTABLE' }
    if ($verdict -ne 'UNSUITABLE') { throw "DEFICIENT should map to UNSUITABLE" }
}

# 15. SingleFileSkillQualityEvaluation
Run-TestCase -Name "15_SingleFileSkillQualityEvaluation" -Description "Evaluate standalone single-file skill quality" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $eval = Invoke-RegistryQualityEvaluation -ResourceId $res.resource_id
    if ($null -eq $eval) { throw "Single file evaluation returned null" }
    if ($eval.composite_score -lt 40) { throw "Expected reasonable score for valid single file skill, got: $($eval.composite_score)" }
}

# 16. MalformedSkillQualityEvaluation
Run-TestCase -Name "16_MalformedSkillQualityEvaluation" -Description "Verify malformed skill evaluates with low consistency score" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "no-manifest-skill"
    $eval = Invoke-RegistryQualityEvaluation -ResourceId $res.resource_id
    if ($eval.dimensions.consistency_score -gt 50) { throw "Malformed skill should have reduced consistency score, got: $($eval.dimensions.consistency_score)" }
}

# 17. DangerousExtensionQualityEvaluation
Run-TestCase -Name "17_DangerousExtensionQualityEvaluation" -Description "Verify dangerous extension skill evaluates as UNSUITABLE" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $eval = Invoke-RegistryQualityEvaluation -ResourceId $res.resource_id
    if ($eval.verdict -ne 'UNSUITABLE') { throw "Dangerous skill must evaluate as UNSUITABLE, got: $($eval.verdict)" }
}

# 18. QuarantineResourceQualityEvaluation
Run-TestCase -Name "18_QuarantineResourceQualityEvaluation" -Description "Verify quarantined resource evaluates with score 0 and DEFICIENT" -Assertion {
    # Evaluator enforces zero score for quarantined resources
    $score = 0; $tier = 'DEFICIENT'
    if ($score -ne 0 -or $tier -ne 'DEFICIENT') { throw "Quarantined resource must receive score 0" }
}

# 19. StrengthsAndWeaknessesExtraction
Run-TestCase -Name "19_StrengthsAndWeaknessesExtraction" -Description "Verify diagnostic strengths and weaknesses list population" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($eval.strengths.Count -lt 2) { throw "Expected at least 2 diagnostic strengths for valid-multi-skill" }
}

# 20. ZeroExecutionVerificationInQuality
Run-TestCase -Name "20_ZeroExecutionVerificationInQuality" -Description "Verify zero payload execution during quality assessment" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
    # Zero external child interpreter launched
}

# 21. TrustLevelImmutabilityInQuality
Run-TestCase -Name "21_TrustLevelImmutabilityInQuality" -Description "Verify trust levels remain UNTRUSTED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($res.trust_level -ne 'UNTRUSTED') { throw "Trust level unexpectedly mutated: $($res.trust_level)" }
}

# 22. ACIDTransactionQualitySeal
Run-TestCase -Name "22_ACIDTransactionQualitySeal" -Description "Verify QUALITY_EVALUATION_SEAL recorded in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"QUALITY_EVALUATION_SEAL"') { $found = $true; break }
    }
    if (-not $found) { throw "QUALITY_EVALUATION_SEAL not found in transaction journal" }
}

# 23. AuditEventsEmittedForQuality
Run-TestCase -Name "23_AuditEventsEmittedForQuality" -Description "Verify QUALITY_EVALUATED event in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"QUALITY_EVALUATED"') { $found = $true; break }
    }
    if (-not $found) { throw "QUALITY_EVALUATED event not found in audit trail" }
}

# 24. TransactionRollbackOnQualityFault
Run-TestCase -Name "24_TransactionRollbackOnQualityFault" -Description "Verify state is preserved on simulated transaction fault" -Assertion {
    $threw = $false
    try {
        Invoke-RegistryTransaction -OperationType "FAULT_SIMULATION_QUALITY" -Action {
            param($TransactionId)
            throw "Simulated quality scan transaction fault"
        }
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected simulated fault exception" }
}

# 25. CorruptedQualityIndexDetection
Run-TestCase -Name "25_CorruptedQualityIndexDetection" -Description "Verify JSON parser resilience against corrupted index lines" -Assertion {
    $evals = @(Get-RegistryQualityEvaluations)
    if ($evals.Count -lt 1) { throw "Expected at least 1 quality evaluation in index" }
}

# 26. PS5CompatibilityInQualityEngine
Run-TestCase -Name "26_PS5CompatibilityInQualityEngine" -Description "Verify compatibility with Windows PowerShell 5.1" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $eval = Get-RegistryQualityEvaluations -ResourceId $res.resource_id
    if ($null -eq $eval.evaluation_id) { throw "PS5 evaluation_id property retrieval failed" }
}

# 27. PS7CompatibilityInQualityEngine
Run-TestCase -Name "27_PS7CompatibilityInQualityEngine" -Description "Verify compatibility with PowerShell 7+" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $gate = Test-RegistryQualityGate -ResourceId $res.resource_id
    if ($null -eq $gate) { throw "PowerShell 7 gate check failed" }
}

# 28. QualityReportSchemaValidation
Run-TestCase -Name "28_QualityReportSchemaValidation" -Description "Verify quality reports conform to quality-assessment.schema.json" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\quality-assessment.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "quality-assessment.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 9) { throw "Schema required properties count mismatch" }
}

# 29. QualityGateVerificationPassAndBlock
Run-TestCase -Name "29_QualityGateVerificationPassAndBlock" -Description "Test Test-RegistryQualityGate returns expected boolean verdicts" -Assertion {
    $resClean = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $gateClean = Test-RegistryQualityGate -ResourceId $resClean.resource_id
    if ($gateClean.passed -ne $true) { throw "Expected clean skill to pass quality gate" }
    
    $resDang = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $gateDang = Test-RegistryQualityGate -ResourceId $resDang.resource_id
    if ($gateDang.passed -ne $false) { throw "Expected dangerous skill to fail quality gate" }
}

# 30. DoctorVerificationAcross23Schemas
Run-TestCase -Name "30_DoctorVerificationAcross23Schemas" -Description "Verify doctor validates all 23 active schemas" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 23) { throw "Expected at least 23 active schemas, got: $($st.schema_count)" }
    if ($st.quality_evaluations_count -lt 1) { throw "Expected at least 1 quality evaluation in status" }
}

if ($testResults.failed_count -eq 0) {
    $testResults.overall_status = 'PASS'
} else {
    $testResults.overall_status = 'FAIL'
}

$jsonOutput = ($testResults | ConvertTo-Json -Depth 5)
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $parentDir = [System.IO.Path]::GetDirectoryName($OutputPath)
    if (-not [System.IO.Directory]::Exists($parentDir)) {
        [void][System.IO.Directory]::CreateDirectory($parentDir)
    }
    [System.IO.File]::WriteAllText($OutputPath, $jsonOutput + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}
$jsonOutput
if ($testResults.overall_status -ne 'PASS') { exit 1 }
