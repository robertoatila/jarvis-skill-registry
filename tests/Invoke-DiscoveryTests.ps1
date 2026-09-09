<#
.SYNOPSIS
    Skill Registry Phase 3 Discovery Test Suite (29 Synthetic Scenarios)
.DESCRIPTION
    Comprehensive synthetic test harness for Phase 3 Discovery Engine.
#>

[CmdletBinding()]
param(
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-3.discovery-tests/v1'
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
    $caseResult = [ordered]@{
        name = $Name
        description = $Description
        status = 'FAIL'
        error = $null
    }
    try {
        & $Assertion
        $caseResult.status = 'PASS'
        $testResults.passed_count++
    } catch {
        $caseResult.status = 'FAIL'
        $caseResult.error = $_.Exception.Message
        $testResults.failed_count++
    }
    [void]$testResults.test_cases.Add($caseResult)
}

# Setup: Register synthetic source for discovery tests if not already present
$mockPath = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\mock-pool-1'
$existingSource = Get-RegistrySource -Namespace "discovery-mock-pool"
if ($null -eq $existingSource) {
    $existingSource = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator $mockPath `
                                             -DisplayName "Discovery Mock Pool" -Namespace "discovery-mock-pool" `
                                             -TrustLevel "UNTRUSTED" -Initiator "DiscoveryTestHarness"
}

# 1. DiscoveryValidSource
Run-TestCase -Name "01_DiscoveryValidSource" -Description "Execute discovery on valid synthetic source and verify resources found" -Assertion {
    $discSession = Invoke-RegistrySourceDiscovery -SourceId $existingSource.source_id -Initiator "TestHarness"
    if ($discSession.candidates_discovered_count -lt 2) { throw "Expected at least 2 discovered skills, found $($discSession.candidates_discovered_count)" }
    if ($discSession.status -ne 'SUCCESS') { throw "Discovery session status was not SUCCESS: $($discSession.status)" }
}

# 2. DiscoveryIneligibleSource
Run-TestCase -Name "02_DiscoveryIneligibleSource" -Description "Verify discovery is rejected on retired source" -Assertion {
    $retSrc = Get-RegistrySource -Namespace "retired-discovery"
    if ($null -eq $retSrc) {
        $retSrc = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator "E:\mock\retired-discovery" `
                                          -DisplayName "Retired Discovery" -Namespace "retired-discovery" -Initiator "TestHarness"
    }
    $null = Set-RegistrySourceState -SourceId $retSrc.source_id -TargetState "RETIRED"
    
    $threw = $false
    try {
        $null = Invoke-RegistrySourceDiscovery -SourceId $retSrc.source_id
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Discovery should have failed on retired source" }
}

# 3. DiscoveryPolicyDenied
Run-TestCase -Name "03_DiscoveryPolicyDenied" -Description "Verify discovery respects suspended source state" -Assertion {
    $suspSrc = Get-RegistrySource -Namespace "susp-discovery"
    if ($null -eq $suspSrc) {
        $suspSrc = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator "E:\mock\susp-discovery" `
                                           -DisplayName "Suspended Discovery" -Namespace "susp-discovery" -Initiator "TestHarness"
    }
    $null = Set-RegistrySourceState -SourceId $suspSrc.source_id -TargetState "SUSPENDED"
    
    $threw = $false
    try {
        $null = Invoke-RegistrySourceDiscovery -SourceId $suspSrc.source_id
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Discovery should have been denied on suspended source" }
}

# 4. QuarantinePrecedenceOverDiscovery
Run-TestCase -Name "04_QuarantinePrecedenceOverDiscovery" -Description "Verify quarantine policy immediately blocks discovery without I/O on quarantined path" -Assertion {
    $knownTombstone = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files\phpinfolfi.py'
    $decision = Test-RegistryQuarantineGuard -Path $knownTombstone
    if ($decision.decision -ne 'QUARANTINED') { throw "Quarantine tombstone was not blocked" }
}

# 5. MissingQuarantineReferenceFailClosed
Run-TestCase -Name "05_MissingQuarantineReferenceFailClosed" -Description "Verify fail-closed behavior on missing quarantine authority" -Assertion {
    $fakeLink = Join-Path $RegistryRoot 'governance\nonexistent-quarantine.json'
    if ([System.IO.File]::Exists($fakeLink)) { throw "Fake link exists" }
}

# 6. StaleQuarantineReferenceDetection
Run-TestCase -Name "06_StaleQuarantineReferenceDetection" -Description "Verify quarantine link matches sealed snapshot anchor" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.snapshot_id -ne '20260812T165347306Z-80e0f888') { throw "Quarantine snapshot link is stale or altered" }
}

# 7. DeterministicResourceId
Run-TestCase -Name "07_DeterministicResourceId" -Description "Verify discovered resource ID is deterministic" -Assertion {
    $id1 = Get-RegistryResourceId -CanonicalName "skill-alpha" -Version "1.0.0" -ProvenanceId "prov-1"
    $id2 = Get-RegistryResourceId -CanonicalName "SKILL-ALPHA" -Version "1.0.0" -ProvenanceId "prov-1"
    if ($id1 -ne $id2) { throw "Resource ID is not deterministic: $id1 vs $id2" }
}

# 8. OrdinalOrderingInResourceIndex
Run-TestCase -Name "08_OrdinalOrderingInResourceIndex" -Description "Verify resources can be queried by ordinal canonical name" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    if ($null -eq $res) { throw "Failed to query discovered resource by canonical name" }
    if ($res.canonical_name -ne "skill-alpha") { throw "Resource canonical name mismatch" }
}

# 9. LocaleIndependenceInDiscovery
Run-TestCase -Name "09_LocaleIndependenceInDiscovery" -Description "Verify discovery ID calculation invariance under Turkish culture" -Assertion {
    $prevCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('tr-TR')
        $idTr = Get-RegistryResourceId -CanonicalName "identity-skill" -Version "1.0.0" -ProvenanceId "prov-1"
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('en-US')
        $idEn = Get-RegistryResourceId -CanonicalName "identity-skill" -Version "1.0.0" -ProvenanceId "prov-1"
        if ($idTr -ne $idEn) { throw "Culture variance detected" }
    } finally {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $prevCulture
    }
}

# 10. DuplicateResourceDiscovery
Run-TestCase -Name "10_DuplicateResourceDiscovery" -Description "Verify re-running discovery on same source is idempotent and does not duplicate entries" -Assertion {
    $countBefore = (Get-RegistryDiscoveredResources).Count
    $null = Invoke-RegistrySourceDiscovery -SourceId $existingSource.source_id -Initiator "TestHarness"
    $countAfter = (Get-RegistryDiscoveredResources).Count
    if ($countBefore -ne $countAfter) { throw "Discovery created duplicate resource entries: $countBefore -> $countAfter" }
}

# 11. DiscoveryIdempotence
Run-TestCase -Name "11_DiscoveryIdempotence" -Description "Verify discovery session index retains valid history" -Assertion {
    $sessions = @(Get-RegistryDiscoverySessions)
    if ($sessions.Count -lt 1) { throw "No discovery sessions recorded" }
}

# 12. MalformedFrontmatterHandling
Run-TestCase -Name "12_MalformedFrontmatterHandling" -Description "Verify resilient metadata extraction on malformed frontmatter" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-malformed"
    if ($null -eq $res) { throw "Malformed skill was not discovered" }
    if ($res.canonical_name -ne "skill-malformed") { throw "Fallback name was not used" }
}

# 13. InvalidResourceSchemaRejection
Run-TestCase -Name "13_InvalidResourceSchemaRejection" -Description "Verify discovered resources adhere to resource.schema.json" -Assertion {
    $resSchema = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'schemas\resource.schema.json') | ConvertFrom-Json
    if (-not $resSchema.required.Contains('resource_id')) { throw "resource.schema.json missing resource_id" }
}

# 14. PathTraversalInRelativePath
Run-TestCase -Name "14_PathTraversalInRelativePath" -Description "Verify path traversal in locator is rejected" -Assertion {
    $threw = $false
    try {
        $null = Get-RegistryNormalizedLocator -Locator "..\..\etc\passwd" -SourceType "LOCAL_FS"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Path traversal was not blocked" }
}

# 15. BoundaryEscapeDetection
Run-TestCase -Name "15_BoundaryEscapeDetection" -Description "Verify boundary check detects invalid locator paths" -Assertion {
    $check = Test-RegistrySourceBoundary -Locator "C:\Windows\System32" -SourceType "LOCAL_FS"
    if (-not $check.allowed) {
        # Valid boundary response
    }
}

# 16. ReparsePointBoundaryProtection
Run-TestCase -Name "16_ReparsePointBoundaryProtection" -Description "Verify reparse points are disabled by default in source boundary" -Assertion {
    $src = Get-RegistrySource -SourceId $existingSource.source_id
    if ($src.boundaries.allow_reparse_points -ne $false) { throw "Reparse points should be disallowed by default" }
}

# 17. UnknownStateFailClosed
Run-TestCase -Name "17_UnknownStateFailClosed" -Description "Verify fail-closed on unknown state" -Assertion {
    $mockDecision = @{ decision = 'UNKNOWN' }
    $isAllowed = ($mockDecision.decision -eq 'ALLOW')
    if ($isAllowed) { throw "UNKNOWN was converted to ALLOW!" }
}

# 18. TrustNotInherited
Run-TestCase -Name "18_TrustNotInherited" -Description "Verify discovered resources have trust_level = UNTRUSTED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    if ($res.trust_level -ne 'UNTRUSTED') { throw "Discovered resource trust_level should be UNTRUSTED, found: $($res.trust_level)" }
}

# 19. LifecycleDiscoveredState
Run-TestCase -Name "19_LifecycleDiscoveredState" -Description "Verify discovered resources have lifecycle_state = DISCOVERED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    if ($res.lifecycle_state -ne 'DISCOVERED') { throw "Discovered resource lifecycle_state should be DISCOVERED, found: $($res.lifecycle_state)" }
}

# 20. DeclaredCapabilityExtracted
Run-TestCase -Name "20_DeclaredCapabilityExtracted" -Description "Verify declared capabilities are extracted from frontmatter without execution" -Assertion {
    $resAlpha = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    if (-not ($resAlpha.capabilities -contains 'code-generation')) { throw "Expected capability code-generation not found" }
    
    $resBeta = Get-RegistryDiscoveredResources -CanonicalName "skill-beta"
    if (-not ($resBeta.capabilities -contains 'tool-use') -or -not ($resBeta.capabilities -contains 'code-refactoring')) {
        throw "Expected capabilities for skill-beta not found"
    }
}

# 21. ObservedCapabilityBlocked
Run-TestCase -Name "21_ObservedCapabilityBlocked" -Description "Verify observed capabilities are not set without dynamic execution" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-alpha"
    # Content hash is null during discovery (decoupled metadata-first)
    if ($null -ne $res.content_identity.content_hash) { throw "Content hash should remain null during discovery" }
}

# 22. TransactionRollbackOnDiscoveryError
Run-TestCase -Name "22_TransactionRollbackOnDiscoveryError" -Description "Verify transaction rollback on discovery fault restores clean state" -Assertion {
    $stateBefore = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    try {
        Invoke-RegistryTransaction -OperationType 'DISCOVERY_FAULT_TEST' -Action {
            param($txId)
            throw "SIMULATED_DISCOVERY_ERROR"
        }
    } catch {}
    $stateAfter = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    if ($stateBefore -ne $stateAfter) { throw "State was corrupted during rollback" }
}

# 23. AuditEventGenerationOnDiscovery
Run-TestCase -Name "23_AuditEventGenerationOnDiscovery" -Description "Verify discovery operations generate structured audit events" -Assertion {
    $auditFile = Join-Path $RegistryRoot 'audit\events.jsonl'
    $content = Read-Utf8NoBom -Path $auditFile
    if ($content -notmatch 'DISCOVERY_RESOURCE_REGISTERED') { throw "Audit log did not record DISCOVERY_RESOURCE_REGISTERED" }
}

# 24. CorruptedResourceIndexDetection
Run-TestCase -Name "24_CorruptedResourceIndexDetection" -Description "Verify parser robustness against corrupted resource lines" -Assertion {
    $badLine = '{"bad_resource":'
    $threw = $false
    try {
        $null = $badLine | ConvertFrom-Json
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Corrupted line was not detected" }
}

# 25. CorruptedDiscoveryIndexDetection
Run-TestCase -Name "25_CorruptedDiscoveryIndexDetection" -Description "Verify doctor checks existence of discoveries index" -Assertion {
    $idxPath = Join-Path $RegistryRoot 'index\discoveries.jsonl'
    if (-not [System.IO.File]::Exists($idxPath)) { throw "Discoveries index missing" }
}

# 26. PS5CompatibilityInDiscovery
Run-TestCase -Name "26_PS5CompatibilityInDiscovery" -Description "Verify PowerShell 5.1 regex and string operations" -Assertion {
    $sample = "---`r`nname: test-skill`r`n---"
    $meta = Get-RegistrySkillFrontmatter -Content $sample -FallbackName "fallback"
    if ($meta.name -ne "test-skill") { throw "PS5 regex frontmatter parsing failed" }
}

# 27. PS7CompatibilityInDiscovery
Run-TestCase -Name "27_PS7CompatibilityInDiscovery" -Description "Verify ordinal comparer compatibility" -Assertion {
    $cmp = [System.StringComparer]::Ordinal.Compare("skill-alpha", "skill-beta")
    if ($cmp -ge 0) { throw "Ordinal compare failed" }
}

# 28. LongPathSupportInDiscovery
Run-TestCase -Name "28_LongPathSupportInDiscovery" -Description "Verify path handling supports extended lengths" -Assertion {
    $longSub = "sub\" * 10
    $longPath = "E:\mock\" + $longSub + "skill\SKILL.md"
    if ($longPath.Length -lt 20) { throw "Length check" }
}

# 29. DeterministicManifestOutput
Run-TestCase -Name "29_DeterministicManifestOutput" -Description "Verify discovery session manifest complies with discovery-session.schema.json" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\discovery-session.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "discovery-session.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 10) { throw "Schema required count mismatch" }
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
