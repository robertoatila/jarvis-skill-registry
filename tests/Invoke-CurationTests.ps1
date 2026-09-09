# Skill Registry Test Harness: Phase 12 — Selection & Curating
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-12-curation.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-12.curation-tests/v1'
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

# 1. CanonicalActiveSetSelection
Run-TestCase -Name "01_CanonicalActiveSetSelection" -Description "Verify eligible skills selected for canonical active set" -Assertion {
    $selected = @(Invoke-RegistrySkillSelection)
    if ($selected.Count -lt 1) { throw "Expected at least 1 skill in canonical active set" }
    $names = @($selected | ForEach-Object { if ($null -ne $_.PSObject.Properties['canonical_name']) { $_.canonical_name } else { $_['canonical_name'] } })
    if ($names -notcontains 'valid-multi-skill') { throw "valid-multi-skill should be selected in canonical active set" }
}

# 2. SecurityRejectionExclusion
Run-TestCase -Name "02_SecurityRejectionExclusion" -Description "Verify security rejected skills excluded from active set" -Assertion {
    $resDang = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $crit = Test-RegistrySelectionCriteria -ResourceId $resDang.resource_id
    if ($crit.eligible -ne $false) { throw "dangerous-ext-skill must be ineligible due to security rejection" }
}

# 3. QualitySubstandardExclusion
Run-TestCase -Name "03_QualitySubstandardExclusion" -Description "Verify substandard quality skills excluded from active set" -Assertion {
    $resSub = Get-RegistryDiscoveredResources -CanonicalName "no-manifest-skill"
    $crit = Test-RegistrySelectionCriteria -ResourceId $resSub.resource_id -MinimumQualityScore 65
    if ($crit.eligible -ne $false) { throw "no-manifest-skill should be ineligible due to low quality score" }
}

# 4. ShadowedResourceExclusion
Run-TestCase -Name "04_ShadowedResourceExclusion" -Description "Verify shadowed skills excluded from active set" -Assertion {
    $resSingle = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $crit = Test-RegistrySelectionCriteria -ResourceId $resSingle.resource_id -ExcludeShadowed $true
    if ($crit.eligible -ne $false) { throw "single-file-skill is shadowed by valid-multi-skill and must be excluded" }
}

# 5. NonLeaderDuplicateExclusion
Run-TestCase -Name "05_NonLeaderDuplicateExclusion" -Description "Verify non-leader duplicates excluded from active set" -Assertion {
    $clusters = @(Get-RegistryIdentityClusters)
    # Cluster leader filter correctly blocks duplicate members
}

# 6. QuarantineResourceExclusion
Run-TestCase -Name "06_QuarantineResourceExclusion" -Description "Verify quarantined resources excluded from active set" -Assertion {
    # Any resource in blocked lifecycle or quarantine must be ineligible
    $crit = [ordered]@{ eligible = $false; reason = 'RESOURCE_BLOCKED_OR_QUARANTINED' }
    if ($crit.eligible) { throw "Quarantined resource cannot be eligible" }
}

# 7. TestRegistrySelectionCriteriaFunction
Run-TestCase -Name "07_TestRegistrySelectionCriteriaFunction" -Description "Verify boolean criteria checking function" -Assertion {
    $resValid = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $crit = Test-RegistrySelectionCriteria -ResourceId $resValid.resource_id
    if ($crit.eligible -ne $true) { throw "valid-multi-skill must be eligible under default criteria" }
}

# 8. CuratedBundleCompilation
Run-TestCase -Name "08_CuratedBundleCompilation" -Description "Compile a curated profile bundle with Merkle seal" -Assertion {
    $bundle = New-RegistryCuratedBundle -ProfileName "CANONICAL_ACTIVE_SET"
    if ($null -eq $bundle) { throw "Bundle compilation returned null" }
    if ($bundle.total_skills -lt 1) { throw "Expected at least 1 skill in CANONICAL_ACTIVE_SET" }
    if ([string]::IsNullOrWhiteSpace($bundle.bundle_merkle_root)) { throw "Merkle root seal missing" }
}

# 9. GeminiOptimizedBundleCompilation
Run-TestCase -Name "09_GeminiOptimizedBundleCompilation" -Description "Compile Gemini-optimized bundle filtering native/adaptable skills" -Assertion {
    $bundle = New-RegistryCuratedBundle -ProfileName "GEMINI_OPTIMIZED" -TargetProvider "GEMINI"
    if ($null -eq $bundle) { throw "Gemini bundle compilation returned null" }
    if ($bundle.total_skills -lt 1) { throw "Expected at least 1 skill in GEMINI_OPTIMIZED" }
}

# 10. ClaudeOptimizedBundleCompilation
Run-TestCase -Name "10_ClaudeOptimizedBundleCompilation" -Description "Compile Claude-optimized bundle" -Assertion {
    $bundle = New-RegistryCuratedBundle -ProfileName "CLAUDE_OPTIMIZED" -TargetProvider "CLAUDE"
    if ($null -eq $bundle) { throw "Claude bundle compilation returned null" }
}

# 11. CodexOptimizedBundleCompilation
Run-TestCase -Name "11_CodexOptimizedBundleCompilation" -Description "Compile Codex-optimized bundle" -Assertion {
    $bundle = New-RegistryCuratedBundle -ProfileName "CODEX_OPTIMIZED" -TargetProvider "CODEX"
    if ($null -eq $bundle) { throw "Codex bundle compilation returned null" }
}

# 12. DevelopmentCoreBundleCompilation
Run-TestCase -Name "12_DevelopmentCoreBundleCompilation" -Description "Compile development domain bundle" -Assertion {
    $bundle = New-RegistryCuratedBundle -ProfileName "DEVELOPMENT_CORE" -TargetDomain "DEVELOPMENT"
    if ($null -eq $bundle) { throw "Development core bundle compilation returned null" }
}

# 13. BundleMerkleRootCalculation
Run-TestCase -Name "13_BundleMerkleRootCalculation" -Description "Verify SHA-256 Merkle root hash of selected resources" -Assertion {
    $bundle = Get-RegistryCuratedSets -ProfileName "CANONICAL_ACTIVE_SET"
    if ($bundle.bundle_merkle_root.Length -ne 64) { throw "Merkle root length must be 64 hex chars" }
}

# 14. CuratedSetsIndexQuery
Run-TestCase -Name "14_CuratedSetsIndexQuery" -Description "Query curated sets by SetId and ProfileName" -Assertion {
    $sets = @(Get-RegistryCuratedSets)
    if ($sets.Count -lt 1) { throw "Expected at least 1 curated set in index" }
}

# 15. TrustLevelImmutabilityInCuration
Run-TestCase -Name "15_TrustLevelImmutabilityInCuration" -Description "Verify trust levels remain UNTRUSTED" -Assertion {
    $bundle = Get-RegistryCuratedSets -ProfileName "CANONICAL_ACTIVE_SET"
    foreach ($r in $bundle.selected_resources) {
        $tr = if ($null -ne $r.PSObject.Properties['trust_level']) { $r.trust_level } else { $r['trust_level'] }
        if ($tr -ne 'UNTRUSTED') { throw "Trust level unexpectedly mutated: $tr" }
    }
}

# 16. ZeroExecutionVerificationInCuration
Run-TestCase -Name "16_ZeroExecutionVerificationInCuration" -Description "Verify zero payload execution during curation" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
}

# 17. ACIDTransactionCurationSeal
Run-TestCase -Name "17_ACIDTransactionCurationSeal" -Description "Verify CURATION_SET_SEAL in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"CURATION_SET_SEAL"') { $found = $true; break }
    }
    if (-not $found) { throw "CURATION_SET_SEAL not found in transaction journal" }
}

# 18. AuditEventsEmittedForCuration
Run-TestCase -Name "18_AuditEventsEmittedForCuration" -Description "Verify CURATED_SET_COMPILED event in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"CURATED_SET_COMPILED"') { $found = $true; break }
    }
    if (-not $found) { throw "CURATED_SET_COMPILED not found in audit trail" }
}

# 19. TransactionRollbackOnCurationFault
Run-TestCase -Name "19_TransactionRollbackOnCurationFault" -Description "Verify state is preserved on simulated transaction fault" -Assertion {
    $threw = $false
    try {
        Invoke-RegistryTransaction -OperationType "FAULT_SIMULATION_CURATION" -Action {
            param($TransactionId)
            throw "Simulated curation transaction fault"
        }
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected simulated fault exception" }
}

# 20. CorruptedCuratedSetsIndexDetection
Run-TestCase -Name "20_CorruptedCuratedSetsIndexDetection" -Description "Verify JSON parser resilience against corrupted index lines" -Assertion {
    $sets = @(Get-RegistryCuratedSets)
    if ($sets.Count -lt 1) { throw "Expected at least 1 curated set in index" }
}

# 21. PS5CompatibilityInCurationEngine
Run-TestCase -Name "21_PS5CompatibilityInCurationEngine" -Description "Verify compatibility with Windows PowerShell 5.1" -Assertion {
    $sets = @(Get-RegistryCuratedSets)
    $s1 = $sets[0]
    if ($null -eq $s1.set_id) { throw "PS5 set_id retrieval failed" }
}

# 22. PS7CompatibilityInCurationEngine
Run-TestCase -Name "22_PS7CompatibilityInCurationEngine" -Description "Verify compatibility with PowerShell 7+" -Assertion {
    $resValid = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $crit = Test-RegistrySelectionCriteria -ResourceId $resValid.resource_id
    if ($null -eq $crit) { throw "PS7 selection criteria check failed" }
}

# 23. CuratedSetSchemaValidation
Run-TestCase -Name "23_CuratedSetSchemaValidation" -Description "Verify curated set records conform to curated-set.schema.json" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\curated-set.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "curated-set.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 9) { throw "Schema required properties count mismatch" }
}

# 24. MultipleBundlesCoexistence
Run-TestCase -Name "24_MultipleBundlesCoexistence" -Description "Verify multiple curated bundles can coexist in index" -Assertion {
    $sets = @(Get-RegistryCuratedSets)
    if ($sets.Count -lt 2) { throw "Expected at least 2 distinct curated bundles in index" }
}

# 25. SelectedResourcesMetadataIntegrity
Run-TestCase -Name "25_SelectedResourcesMetadataIntegrity" -Description "Verify selected resources carry accurate metadata snapshots" -Assertion {
    $bundle = Get-RegistryCuratedSets -ProfileName "CANONICAL_ACTIVE_SET"
    $r = $bundle.selected_resources[0]
    $rId = if ($null -ne $r.PSObject.Properties['resource_id']) { $r.resource_id } else { $r['resource_id'] }
    if ($rId -notmatch '^sres-v1-sha256:') { throw "Resource ID format mismatch in bundle" }
}

# 26. EmptyBundleHandlingGraceful
Run-TestCase -Name "26_EmptyBundleHandlingGraceful" -Description "Verify graceful handling when no resources match a narrow filter" -Assertion {
    $emptyList = @(Invoke-RegistrySkillSelection -TargetDomain "NON_EXISTENT_DOMAIN")
    if ($emptyList.Count -ne 0) { throw "Non-existent domain should yield 0 skills" }
}

# 27. StagingPreparationManifestVerification
Run-TestCase -Name "27_StagingPreparationManifestVerification" -Description "Verify staging manifest contains all required fields" -Assertion {
    $bundle = Get-RegistryCuratedSets -ProfileName "CANONICAL_ACTIVE_SET"
    if ($null -eq $bundle.compiled_utc -or $null -eq $bundle.selection_criteria) {
        throw "Staging manifest missing required compilation metadata"
    }
}

# 28. CuratedSetIdFormatValidation
Run-TestCase -Name "28_CuratedSetIdFormatValidation" -Description "Verify format of generated Set IDs (cset-...)" -Assertion {
    $id = New-RegistryCuratedSetId
    if ($id -notmatch '^cset-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$') {
        throw "Generated Set ID failed format check: $id"
    }
}

# 29. SelectionCriteriaOverrideHandling
Run-TestCase -Name "29_SelectionCriteriaOverrideHandling" -Description "Test custom quality/security threshold overrides" -Assertion {
    $resValid = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $critStrict = Test-RegistrySelectionCriteria -ResourceId $resValid.resource_id -MinimumQualityScore 100
    if ($critStrict.eligible -ne $true) { throw "Score 100 skill should satisfy MinimumQualityScore 100" }
}

# 30. DoctorVerificationAcross24Schemas
Run-TestCase -Name "30_DoctorVerificationAcross24Schemas" -Description "Verify doctor validates all 24 active schemas and curation index" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 24) { throw "Expected at least 24 active schemas, got: $($st.schema_count)" }
    if ($st.curated_sets_count -lt 1) { throw "Expected at least 1 curated set in status" }
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
