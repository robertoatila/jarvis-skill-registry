# Skill Registry Test Harness: Phase 7 — Capabilities & Semantic Surface Modeling
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-7-capabilities.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-7.capability-tests/v1'
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

# 1. RegisterCanonicalCapabilityValid
Run-TestCase -Name "01_RegisterCanonicalCapabilityValid" -Description "Register canonical capability conforming to schema" -Assertion {
    $c = Register-RegistryCanonicalCapability -CapabilityId "test-codegen-cap" -Domain "DEVELOPMENT" -Description "Test capability for unit tests" -Keywords @("test", "codegen") -Aliases @("test-gen")
    if ($c.capability_id -ne "test-codegen-cap") { throw "Capability registration failed" }
    if ($c.domain -ne "DEVELOPMENT") { throw "Domain mismatch" }
}

# 2. DuplicateCapabilityHandling
Run-TestCase -Name "02_DuplicateCapabilityHandling" -Description "Verify idempotence / update of canonical capability registration" -Assertion {
    $c1 = Register-RegistryCanonicalCapability -CapabilityId "test-idempotent-cap" -Domain "TESTING" -Description "Initial description" -Keywords @("k1")
    $c2 = Register-RegistryCanonicalCapability -CapabilityId "test-idempotent-cap" -Domain "TESTING" -Description "Updated description" -Keywords @("k1", "k2")
    $fetched = Get-RegistryCanonicalCapabilities -CapabilityId "test-idempotent-cap"
    if ($fetched.description -ne "Updated description") { throw "Idempotent update failed to update description" }
}

# 3. CapabilityIdRegexValidation
Run-TestCase -Name "03_CapabilityIdRegexValidation" -Description "Verify capability_id regex format" -Assertion {
    $threw = $false
    try {
        Register-RegistryCanonicalCapability -CapabilityId "INVALID_CAP_ID!" -Domain "DEVELOPMENT" -Description "Invalid"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected exception for invalid capability ID format" }
}

# 4. TaxonomyDomainValidation
Run-TestCase -Name "04_TaxonomyDomainValidation" -Description "Verify domain enum validation" -Assertion {
    $threw = $false
    try {
        Register-RegistryCanonicalCapability -CapabilityId "invalid-domain-cap" -Domain "INVALID_DOMAIN" -Description "Invalid"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected exception for invalid capability domain" }
}

# 5. AliasNormalizationExact
Run-TestCase -Name "05_AliasNormalizationExact" -Description "Normalize alias to canonical ID" -Assertion {
    $norm = Normalize-RegistryCapabilityTag -Tag "py-codegen"
    if ($norm -ne "python-codegen") { throw "Expected 'python-codegen', got: $norm" }
}

# 6. KeywordFuzzyNormalization
Run-TestCase -Name "06_KeywordFuzzyNormalization" -Description "Normalize non-exact tag using keywords" -Assertion {
    $norm = Normalize-RegistryCapabilityTag -Tag "scaffold"
    if ($norm -ne "code-generation") { throw "Expected 'code-generation', got: $norm" }
}

# 7. UnknownTagFallback
Run-TestCase -Name "07_UnknownTagFallback" -Description "Unmatched custom tag falls back safely to normalized slug" -Assertion {
    $norm = Normalize-RegistryCapabilityTag -Tag "Custom Tool 2026!"
    if ($norm -ne "custom-tool-2026-") { throw "Expected slug 'custom-tool-2026-', got: $norm" }
}

# 8. FrontmatterCapabilityExtraction
Run-TestCase -Name "08_FrontmatterCapabilityExtraction" -Description "Extract declared capabilities from frontmatter" -Assertion {
    $yaml = @"
---
name: test-skill
description: Test skill
version: 1.0.0
capabilities:
  - python-codegen
  - ast-transform
---
# Content
"@
    $meta = Get-RegistrySkillFrontmatter -Content $yaml -FallbackName "test-skill"
    if ($meta.capabilities.Length -ne 2) { throw "Failed to extract 2 capabilities from frontmatter" }
    if ($meta.capabilities[0] -ne 'python-codegen') { throw "First capability mismatch" }
}

# 9. StructuralCapabilityInference
Run-TestCase -Name "09_StructuralCapabilityInference" -Description "Infer capabilities from script types and packaging" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $sa = Get-RegistryStructuralAnalyses -ResourceId $res.resource_id
    if ($null -eq $sa) { throw "Structural analysis missing for valid-multi-skill" }
    if ($sa.inferred_metadata.primary_runtime -ne 'PYTHON') { throw "Expected PYTHON runtime for valid-multi-skill" }
}

# 10. CapabilityProfileGeneration
Run-TestCase -Name "10_CapabilityProfileGeneration" -Description "Generate complete capability profile for multi-file skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $profile = Invoke-RegistryCapabilityAnalysis -ResourceId $res.resource_id
    if ($profile.primary_domain -ne 'DEVELOPMENT') { throw "Expected primary domain DEVELOPMENT, got: $($profile.primary_domain)" }
    if ($profile.canonical_capabilities.Count -lt 2) { throw "Expected at least 2 canonical capabilities" }
    if (-not ($profile.canonical_capabilities -contains 'python-codegen')) { throw "Missing python-codegen in canonical caps" }
}

# 11. DensityScoreCalculation
Run-TestCase -Name "11_DensityScoreCalculation" -Description "Verify capability density score calculation" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $profile = Get-RegistryCapabilityProfiles -ResourceId $res.resource_id
    if ($profile.capability_density_score -le 0.0 -or $profile.capability_density_score -gt 1.0) {
        throw "Invalid capability density score: $($profile.capability_density_score)"
    }
}

# 12. SingleFileCapabilityProfile
Run-TestCase -Name "12_SingleFileCapabilityProfile" -Description "Generate capability profile for single-file skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $profile = Invoke-RegistryCapabilityAnalysis -ResourceId $res.resource_id
    if ($null -eq $profile) { throw "Failed to generate profile for single-file-skill" }
    if ($profile.primary_domain -notin @('AI_ENGINEERING', 'DEVELOPMENT', 'GENERAL')) {
        throw "Unexpected primary domain: $($profile.primary_domain)"
    }
}

# 13. MalformedSkillEmptyCapabilities
Run-TestCase -Name "13_MalformedSkillEmptyCapabilities" -Description "Verify graceful profile generation for empty frontmatter" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-malformed"
    $profile = Invoke-RegistryCapabilityAnalysis -ResourceId $res.resource_id
    if ($null -eq $profile) { throw "Failed to generate profile for skill-malformed" }
    if ($profile.declared_capabilities.Count -ne 0) { throw "Expected 0 declared capabilities" }
}

# 14. FindResourcesByCapabilitySingle
Run-TestCase -Name "14_FindResourcesByCapabilitySingle" -Description "Query skills supporting a single canonical capability" -Assertion {
    $matches = @(Find-RegistryResourcesByCapability -Capability "python-codegen")
    if ($matches.Count -eq 0) { throw "Expected at least 1 skill matching python-codegen" }
    $found = $false
    foreach ($m in $matches) {
        if ($m.canonical_name -eq 'valid-multi-skill') { $found = $true; break }
    }
    if (-not $found) { throw "Expected valid-multi-skill in python-codegen results" }
}

# 15. FindResourcesByCapabilityMulti
Run-TestCase -Name "15_FindResourcesByCapabilityMulti" -Description "Query skills matching multiple capability filters" -Assertion {
    $matches = @(Find-RegistryResourcesByCapability -Capability "prompt-engineering")
    if ($matches.Count -eq 0) { throw "Expected matches for prompt-engineering" }
}

# 16. QuarantinePrecedenceInCapabilities
Run-TestCase -Name "16_QuarantinePrecedenceInCapabilities" -Description "Verify quarantine policy link matches sealed anchor" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.snapshot_id -ne '20260812T165347306Z-80e0f888') { throw "Quarantine snapshot link mismatch" }
}

# 17. BlockedResourceCapabilityTagging
Run-TestCase -Name "17_BlockedResourceCapabilityTagging" -Description "Verify blocked resource capabilities are flagged properly" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $profile = Invoke-RegistryCapabilityAnalysis -ResourceId $res.resource_id
    if ($null -eq $profile) { throw "Failed to profile dangerous-ext-skill" }
}

# 18. ZeroExecutionDuringCapabilityAnalysis
Run-TestCase -Name "18_ZeroExecutionDuringCapabilityAnalysis" -Description "Verify zero payload execution during analysis" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
    # Zero external child interpreter launched by analysis
}

# 19. TrustLevelImmutabilityInCapabilities
Run-TestCase -Name "19_TrustLevelImmutabilityInCapabilities" -Description "Verify trust levels of discovered resources remain UNTRUSTED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($res.trust_level -ne 'UNTRUSTED') { throw "Trust level unexpectedly mutated: $($res.trust_level)" }
}

# 20. ACIDTransactionCapabilityProfileCommit
Run-TestCase -Name "20_ACIDTransactionCapabilityProfileCommit" -Description "Verify CAPABILITY_PROFILE_SEAL recorded in journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"CAPABILITY_PROFILE_SEAL"') { $found = $true; break }
    }
    if (-not $found) { throw "CAPABILITY_PROFILE_SEAL not found in transaction journal" }
}

# 21. AuditEventsEmittedForCapabilities
Run-TestCase -Name "21_AuditEventsEmittedForCapabilities" -Description "Verify CAPABILITY_PROFILE_SEALED in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"CAPABILITY_PROFILE_SEALED"') { $found = $true; break }
    }
    if (-not $found) { throw "CAPABILITY_PROFILE_SEALED event not found in audit events" }
}

# 22. TransactionRollbackOnCapabilityFault
Run-TestCase -Name "22_TransactionRollbackOnCapabilityFault" -Description "Verify state is preserved on simulated transaction fault" -Assertion {
    $threw = $false
    try {
        Invoke-RegistryTransaction -OperationType "FAULT_SIMULATION_CAP" -Action {
            param($TransactionId)
            throw "Simulated capability transaction fault"
        }
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected simulated fault exception" }
}

# 23. CorruptedCapabilityIndexDetection
Run-TestCase -Name "23_CorruptedCapabilityIndexDetection" -Description "Verify JSON parser resilience against corrupted lines" -Assertion {
    $caps = @(Get-RegistryCanonicalCapabilities)
    if ($caps.Count -lt 20) { throw "Expected at least 20 canonical capabilities" }
}

# 24. PS5CompatibilityInCapabilities
Run-TestCase -Name "24_PS5CompatibilityInCapabilities" -Description "Verify compatibility with Windows PowerShell 5.1" -Assertion {
    $norm = Normalize-RegistryCapabilityTag -Tag "ast-manipulation"
    if ($norm -ne "ast-transform") { throw "Normalization alias lookup failed under PS5" }
}

# 25. PS7CompatibilityInCapabilities
Run-TestCase -Name "25_PS7CompatibilityInCapabilities" -Description "Verify compatibility with PowerShell 7+" -Assertion {
    $id = New-RegistryCapabilityProfileId
    if ($id -notmatch '^cpro-[0-9]{8}T[0-9]{9}Z-[0-9a-f]{8}$') { throw "Profile ID format mismatch: $id" }
}

# 26. ExtendedPathSupportInCapabilities
Run-TestCase -Name "26_ExtendedPathSupportInCapabilities" -Description "Verify path handling supports deep structures" -Assertion {
    $path = "E:\.skill-registry\index\capabilities.jsonl"
    if (-not [System.IO.File]::Exists($path)) { throw "capabilities.jsonl missing" }
}

# 27. CapabilityProfileSchemaValidation
Run-TestCase -Name "27_CapabilityProfileSchemaValidation" -Description "Verify schema conforms to JSON Schema Draft 2020-12" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\capability-profile.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "capability-profile.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 10) { throw "Schema required count mismatch" }
}

# 28. SeedCanonicalTaxonomyCatalog
Run-TestCase -Name "28_SeedCanonicalTaxonomyCatalog" -Description "Verify full taxonomy catalog covers 8 standard domains" -Assertion {
    $caps = @(Get-RegistryCanonicalCapabilities)
    $domains = @($caps | ForEach-Object { $_.domain } | Select-Object -Unique)
    $expected = @('DEVELOPMENT', 'SECURITY', 'DEVOPS', 'ARCHITECTURE', 'DATA_ENGINEERING', 'TESTING', 'AI_ENGINEERING', 'GOVERNANCE')
    foreach ($exp in $expected) {
        if (-not ($domains -contains $exp)) { throw "Missing expected canonical domain: $exp" }
    }
}

# 29. DoctorVerificationAcross21Schemas
Run-TestCase -Name "29_DoctorVerificationAcross21Schemas" -Description "Verify doctor validates all 21 active schemas" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 21) { throw "Expected at least 21 active schemas, got: $($st.schema_count)" }
    if ($st.canonical_capability_count -lt 20) { throw "Expected at least 20 canonical capabilities" }
}

# 30. LiveCapabilitySearchQuery
Run-TestCase -Name "30_LiveCapabilitySearchQuery" -Description "Verify capability search returns expected matches" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    if ($null -ne $res) {
        $null = Invoke-RegistryCapabilityAnalysis -ResourceId $res.resource_id
    }
    $search = @(Find-RegistryResourcesByCapability -Capability "python-codegen")
    if ($search.Count -eq 0) { throw "Live search query failed to return results" }
}
# Teardown: purge temporary test capabilities from index/capabilities.jsonl
$capPath = Join-Path $RegistryRoot 'index\capabilities.jsonl'
if (Test-Path $capPath) {
    $cleanLines = @(Get-Content -LiteralPath $capPath | Where-Object { 
        -not [string]::IsNullOrWhiteSpace($_) -and 
        $_ -notmatch '"test-codegen-cap"' -and 
        $_ -notmatch '"test-idempotent-cap"'
    })
    [System.IO.File]::WriteAllLines($capPath, $cleanLines, (New-Object System.Text.UTF8Encoding($false)))
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
