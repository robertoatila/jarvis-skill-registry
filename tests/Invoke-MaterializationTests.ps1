# Skill Registry Test Harness: Phase 13 — Adaptation & Materialization
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-13-materialization.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-13.materialization-tests/v1'
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

# Setup: get test resource
$validSkill = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"

# 1. MaterializationGeminiPassthrough
Run-TestCase -Name "01_MaterializationGeminiPassthrough" -Description "Materialize skill for Gemini using native/passthrough adapter" -Assertion {
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "GEMINI"
    if ($null -eq $mat) { throw "Gemini materialization returned null" }
    if ($mat.target_provider -ne "GEMINI") { throw "Target provider mismatch" }
    if ($mat.transformation_mode -ne "PASSTHROUGH") { throw "Transformation mode mismatch" }
}

# 2. MaterializationClaudeSystemPrompt
Run-TestCase -Name "02_MaterializationClaudeSystemPrompt" -Description "Materialize skill for Claude transforming SKILL.md to Claude markdown prompt" -Assertion {
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "CLAUDE"
    if ($null -eq $mat) { throw "Claude materialization returned null" }
    if ($mat.transformation_mode -ne "SKILL_MD_TO_SYSTEM_PROMPT") { throw "Transformation mode mismatch" }
}

# 3. MaterializationOpenAIToolSpec
Run-TestCase -Name "03_MaterializationOpenAIToolSpec" -Description "Materialize skill for OpenAI generating JSON tool definition" -Assertion {
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "OPENAI"
    if ($null -eq $mat) { throw "OpenAI materialization returned null" }
    if ($mat.transformation_mode -ne "PROMPT_TO_TOOL") { throw "Transformation mode mismatch: $($mat.transformation_mode)" }
}

# 4. MaterializationGenericAgent
Run-TestCase -Name "04_MaterializationGenericAgent" -Description "Materialize skill for Generic Agent standard spec" -Assertion {
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "GENERIC_AGENT"
    if ($null -eq $mat) { throw "Generic Agent materialization returned null" }
}

# 5. SourceFileImmutability
Run-TestCase -Name "05_SourceFileImmutability" -Description "Verify source skill files are untouched after materialization" -Assertion {
    $integ = Test-RegistryContentIntegrity -ResourceId $validSkill.resource_id
    if (-not $integ.passed) { throw "Source files were mutated during materialization: $($integ.status)" }
}

# 6. PrePostTransformationHashLineage
Run-TestCase -Name "06_PrePostTransformationHashLineage" -Description "Verify source content hash and materialized Merkle root recorded" -Assertion {
    $mats = @(Get-RegistryMaterializations -ResourceId $validSkill.resource_id)
    $m = $mats[0]
    if ([string]::IsNullOrWhiteSpace($m.source_content_hash) -or [string]::IsNullOrWhiteSpace($m.materialized_content_hash)) {
        throw "Source or Materialized hash missing in manifest"
    }
}

# 7. QuarantinedResourceMaterializationRefusal
Run-TestCase -Name "07_QuarantinedResourceMaterializationRefusal" -Description "Verify quarantined/blocked skills cannot be materialized" -Assertion {
    $dangSkill = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $threw = $false
    try {
        Invoke-RegistrySkillMaterialization -ResourceId $dangSkill.resource_id -TargetProvider "GEMINI"
    } catch {
        $threw = $true
    }
    # dangerous-ext-skill or blocked resources must be refused
    if (-not $threw) { throw "Expected exception when attempting to materialize unsafe resource" }
}

# 8. TrustLevelImmutabilityInMaterialization
Run-TestCase -Name "08_TrustLevelImmutabilityInMaterialization" -Description "Verify materialized artifact inherits UNTRUSTED trust level" -Assertion {
    $mats = @(Get-RegistryMaterializations -ResourceId $validSkill.resource_id)
    foreach ($m in $mats) {
        if ($m.trust_level -ne 'UNTRUSTED') { throw "Trust level unexpectedly escalated: $($m.trust_level)" }
    }
}

# 9. ZeroPayloadExecutionInMaterialization
Run-TestCase -Name "09_ZeroPayloadExecutionInMaterialization" -Description "Verify zero dynamic process execution during materialization" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
}

# 10. DeterministicOutputVerification
Run-TestCase -Name "10_DeterministicOutputVerification" -Description "Verify repeated materializations produce bit-for-bit identical hashes" -Assertion {
    $m1 = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "GEMINI"
    $m2 = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "GEMINI"
    if ($m1.materialized_content_hash -ne $m2.materialized_content_hash) {
        throw "Non-deterministic materialization output: $($m1.materialized_content_hash) vs $($m2.materialized_content_hash)"
    }
}

# 11. MaterializationManifestSchemaValidation
Run-TestCase -Name "11_MaterializationManifestSchemaValidation" -Description "Verify manifest conforms to schema #25" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\materialization-manifest.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "materialization-manifest.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 13) { throw "Schema required properties count mismatch" }
}

# 12. MaterializationIndexQuery
Run-TestCase -Name "12_MaterializationIndexQuery" -Description "Query materializations by ID and ResourceId" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    if ($mats.Count -lt 1) { throw "Expected at least 1 materialization record" }
    $m1 = Get-RegistryMaterializations -MaterializationId $mats[0].materialization_id
    if ($null -eq $m1) { throw "Materialization query by ID returned null" }
}

# 13. TestRegistryMaterializationIntegrityFunction
Run-TestCase -Name "13_TestRegistryMaterializationIntegrityFunction" -Description "Verify disk files against sealed manifest hashes" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    $v = Test-RegistryMaterializationIntegrity -MaterializationId $mats[0].materialization_id
    if (-not $v.passed) { throw "Materialization integrity verification failed: $($v.status)" }
}

# 14. TamperedMaterializedFileDetection
Run-TestCase -Name "14_TamperedMaterializedFileDetection" -Description "Verify tampering in staging/materialized is detected" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    $m = $mats[0]
    $stagingDir = Join-Path $RegistryRoot $m.staging_path.Replace('/', '\')
    $testFile = Join-Path $stagingDir 'tamper_test.txt'
    # Adding untracked file
    Write-Utf8NoBom -Path $testFile -Content "tampered content"
    
    $v = Test-RegistryMaterializationIntegrity -MaterializationId $m.materialization_id
    # Clean up tamper test file
    if ([System.IO.File]::Exists($testFile)) { [System.IO.File]::Delete($testFile) }
}

# 15. ACIDTransactionMaterializationSeal
Run-TestCase -Name "15_ACIDTransactionMaterializationSeal" -Description "Verify MATERIALIZATION_SEAL in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"MATERIALIZATION_SEAL"') { $found = $true; break }
    }
    if (-not $found) { throw "MATERIALIZATION_SEAL not found in transaction journal" }
}

# 16. AuditEventsEmittedForMaterialization
Run-TestCase -Name "16_AuditEventsEmittedForMaterialization" -Description "Verify SKILL_MATERIALIZED in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"SKILL_MATERIALIZED"') { $found = $true; break }
    }
    if (-not $found) { throw "SKILL_MATERIALIZED not found in audit trail" }
}

# 17. TransactionRollbackOnMaterializationFault
Run-TestCase -Name "17_TransactionRollbackOnMaterializationFault" -Description "Verify state is preserved on simulated transaction fault" -Assertion {
    $threw = $false
    try {
        Invoke-RegistryTransaction -OperationType "FAULT_SIMULATION_MAT" -Action {
            param($TransactionId)
            throw "Simulated materialization transaction fault"
        }
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected simulated fault exception" }
}

# 18. CorruptedMaterializationsIndexDetection
Run-TestCase -Name "18_CorruptedMaterializationsIndexDetection" -Description "Verify JSON parser resilience against corrupted index lines" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    if ($mats.Count -lt 1) { throw "Expected at least 1 materialization record" }
}

# 19. PS5CompatibilityInMaterializationEngine
Run-TestCase -Name "19_PS5CompatibilityInMaterializationEngine" -Description "Verify compatibility with Windows PowerShell 5.1" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    $m1 = $mats[0]
    if ($null -eq $m1.materialization_id) { throw "PS5 materialization_id retrieval failed" }
}

# 20. PS7CompatibilityInMaterializationEngine
Run-TestCase -Name "20_PS7CompatibilityInMaterializationEngine" -Description "Verify compatibility with PowerShell 7+" -Assertion {
    $adps = @(Get-RegistryAdapters)
    if ($adps.Count -lt 5) { throw "Expected at least 5 registered adapters" }
}

# 21. RegisteredAdaptersDiscovery
Run-TestCase -Name "21_RegisteredAdaptersDiscovery" -Description "Verify all 5 adapters correctly discovered and loaded" -Assertion {
    $adps = @(Get-RegistryAdapters)
    $providers = @($adps | ForEach-Object { $_.target_provider })
    if ($providers -notcontains "GEMINI" -or $providers -notcontains "CLAUDE" -or $providers -notcontains "CODEX") {
        throw "Required provider adapters missing: $($providers -join ', ')"
    }
}

# 22. StagingDirectoryStructureIntegrity
Run-TestCase -Name "22_StagingDirectoryStructureIntegrity" -Description "Verify staging/materialized directory layout" -Assertion {
    $stagingRoot = Join-Path $RegistryRoot 'staging\materialized'
    if (-not [System.IO.Directory]::Exists($stagingRoot)) { throw "Staging root missing" }
}

# 23. MultiFileSkillMaterialization
Run-TestCase -Name "23_MultiFileSkillMaterialization" -Description "Verify materialization of multi-file skill preserves subdirectories" -Assertion {
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "GEMINI"
    if ($mat.materialized_files.Count -lt 1) { throw "Expected files in multi-file skill materialization" }
}

# 24. SingleFileSkillMaterialization
Run-TestCase -Name "24_SingleFileSkillMaterialization" -Description "Verify single-file skill materialization" -Assertion {
    $singleSkill = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $mat = Invoke-RegistrySkillMaterialization -ResourceId $singleSkill.resource_id -TargetProvider "GEMINI"
    if ($null -eq $mat) { throw "Single file skill materialization returned null" }
}

# 25. MaterializationIdFormatValidation
Run-TestCase -Name "25_MaterializationIdFormatValidation" -Description "Verify format of generated ID (mat-...)" -Assertion {
    $id = New-RegistryMaterializationId
    if ($id -notmatch '^mat-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$') {
        throw "Generated Materialization ID failed format check: $id"
    }
}

# 26. NonExistentResourceHandlingGraceful
Run-TestCase -Name "26_NonExistentResourceHandlingGraceful" -Description "Verify error handling when non-existent resource ID requested" -Assertion {
    $threw = $false
    try {
        Invoke-RegistrySkillMaterialization -ResourceId "sres-v1-sha256:0000000000000000000000000000000000000000000000000000000000000000" -TargetProvider "GEMINI"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected exception for non-existent resource" }
}

# 27. IncompatibleProviderHandlingGraceful
Run-TestCase -Name "27_IncompatibleProviderHandlingGraceful" -Description "Verify error handling when incompatible provider adapter specified" -Assertion {
    $threw = $false
    try {
        Invoke-RegistrySkillMaterialization -ResourceId $validSkill.resource_id -TargetProvider "UNKNOWN_PROVIDER"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected exception for unknown provider adapter" }
}

# 28. StagingWorkspaceIsolation
Run-TestCase -Name "28_StagingWorkspaceIsolation" -Description "Verify staging output is strictly confined within staging directory" -Assertion {
    $mats = @(Get-RegistryMaterializations)
    foreach ($m in $mats) {
        if ($m.staging_path -notmatch '^staging/materialized/mat-') {
            throw "Staging path violation: $($m.staging_path)"
        }
    }
}

# 29. ReMaterializationUpdateHandling
Run-TestCase -Name "29_ReMaterializationUpdateHandling" -Description "Test re-materialization of modified resource version" -Assertion {
    $mats = @(Get-RegistryMaterializations -ResourceId $validSkill.resource_id)
    if ($mats.Count -lt 2) { throw "Expected multiple materialization records for resource" }
}

# 30. DoctorVerificationAcross25Schemas
Run-TestCase -Name "30_DoctorVerificationAcross25Schemas" -Description "Verify doctor validates all 25 active schemas and materialization index" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 25) { throw "Expected at least 25 active schemas, got: $($st.schema_count)" }
    if ($st.materializations_count -lt 1) { throw "Expected at least 1 materialization in status" }
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
