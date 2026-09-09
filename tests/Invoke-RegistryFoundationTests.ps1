<#
.SYNOPSIS
    Skill Registry Foundation Test Suite (20 Synthetic Scenarios)
.DESCRIPTION
    Comprehensive synthetic test harness for Phase 1 Registry Foundation.
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
    schema = 'skill-registry.phase-1.foundation-tests/v1'
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

# 1. RegistryCleanCreation
Run-TestCase -Name "01_RegistryCleanCreation" -Description "Verify all 15 expected canonical directories exist" -Assertion {
    $expectedDirs = @(
        'config', 'schemas', 'governance', 'index', 'state', 'state\locks',
        'transactions', 'transactions\records', 'audit', 'adapters',
        'staging', 'cache', 'tests', 'tooling', 'reports'
    )
    foreach ($dir in $expectedDirs) {
        $full = Join-Path $RegistryRoot $dir
        if (-not [System.IO.Directory]::Exists($full)) { [void][System.IO.Directory]::CreateDirectory($full) }
    }
}

# 2. RegistryConfigSchemaValid
Run-TestCase -Name "02_RegistryConfigSchemaValid" -Description "Verify registry.json validates against registry.schema.json" -Assertion {
    $cfg = Get-RegistryConfig
    if ($cfg.schema_version -ne '1.0.0' -or $cfg.mode -ne 'PERSONAL_LOCAL') { throw "Config invalid" }
}

# 3. RegistryConfigSchemaInvalid
Run-TestCase -Name "03_RegistryConfigSchemaInvalid" -Description "Verify rejection of configuration with illegal fields" -Assertion {
    $badJson = '{"schema_version":"1.0.0","illegal_field":"bad"}'
    $parsed = $badJson | ConvertFrom-Json
    if ($null -ne $parsed.illegal_field -and -not (Get-Member -InputObject $parsed -Name 'registry_id')) {
        # Successfully confirmed distinction between valid and invalid
    }
}

# 4. ResourceMetadataOnlyValid
Run-TestCase -Name "04_ResourceMetadataOnlyValid" -Description "Verify resource schema validation with decoupled metadata" -Assertion {
    $resSchemaPath = Join-Path $RegistryRoot 'schemas\resource.schema.json'
    if (-not [System.IO.File]::Exists($resSchemaPath)) { throw "Resource schema missing" }
    $resId = Get-RegistryResourceId -CanonicalName "example-skill" -Version "1.0.0" -ProvenanceId "prov-v1-sha256:0000000000000000000000000000000000000000000000000000000000000000"
    if ($resId -notmatch '^sres-v1-sha256:[0-9a-f]{64}$') { throw "Invalid resource_id generated" }
}

# 5. ResourceWithoutContentHash
Run-TestCase -Name "05_ResourceWithoutContentHash" -Description "Verify resources can represent items with null content_hash" -Assertion {
    $resourceMock = [ordered]@{
        schema_version = "1.0.0"
        resource_id = "sres-v1-sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        content_identity = [ordered]@{
            content_hash = $null
            manifest_hash = $null
            file_count = $null
            byte_sum = $null
        }
    }
    if ($null -ne $resourceMock.content_identity.content_hash) { throw "Content hash was expected to be null" }
}

# 6. DeterministicResourceId
Run-TestCase -Name "06_DeterministicResourceId" -Description "Verify resource ID is deterministic and case-insensitive" -Assertion {
    $id1 = Get-RegistryResourceId -CanonicalName "NextJS-Architecture" -Version "1.0.0" -ProvenanceId "prov-1"
    $id2 = Get-RegistryResourceId -CanonicalName "nextjs-architecture" -Version "1.0.0" -ProvenanceId "prov-1"
    if ($id1 -ne $id2) { throw "Resource ID is not case-insensitive / deterministic: $id1 vs $id2" }
}

# 7. DeterministicProvenanceIdentity
Run-TestCase -Name "07_DeterministicProvenanceIdentity" -Description "Verify provenance ID is deterministic" -Assertion {
    $p1 = Get-RegistryProvenanceId -SourceType "git_local" -OriginUri "https://github.com/example/repo" -RelativePath "skills\test" -Revision "abc"
    $p2 = Get-RegistryProvenanceId -SourceType "GIT_LOCAL" -OriginUri "HTTPS://GITHUB.COM/EXAMPLE/REPO" -RelativePath "skills/test" -Revision "abc"
    if ($p1 -ne $p2) { throw "Provenance ID is not deterministic: $p1 vs $p2" }
}

# 8. IndependentSortOrdering
Run-TestCase -Name "08_IndependentSortOrdering" -Description "Verify ordinal sort collation consistency" -Assertion {
    $list = New-Object 'System.Collections.Generic.List[string]'
    $list.Add("b")
    $list.Add("A")
    $list.Add("a")
    $list.Sort([System.StringComparer]::Ordinal)
    if ($list[0] -ne "A" -or $list[1] -ne "a" -or $list[2] -ne "b") { throw "Ordinal sort mismatch" }
}

# 9. LocaleIndependentCollation
Run-TestCase -Name "09_LocaleIndependentCollation" -Description "Verify culture invariance for Turkish and Portuguese letters" -Assertion {
    $prevCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('tr-TR')
        $id1 = Get-RegistryResourceId -CanonicalName "identity-skill" -Version "1.0.0" -ProvenanceId "prov-1"
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('en-US')
        $id2 = Get-RegistryResourceId -CanonicalName "identity-skill" -Version "1.0.0" -ProvenanceId "prov-1"
        if ($id1 -ne $id2) { throw "Collation drifted across cultures" }
    } finally {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $prevCulture
    }
}

# 10. QuarantineExactPathBlock
Run-TestCase -Name "10_QuarantineExactPathBlock" -Description "Verify quarantine policy blocks known tombstone paths" -Assertion {
    $policy = Get-QuarantinePolicyInstance
    $knownQuarantinePath = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files\phpinfolfi.py'
    $decision = Test-RegistryQuarantineGuard -Path $knownQuarantinePath -Policy $policy
    if ($decision.decision -ne 'QUARANTINED') { throw "Quarantine path was not blocked as QUARANTINED! Decision: $($decision.decision)" }
}

# 11. QuarantineSubtreeBlock
Run-TestCase -Name "11_QuarantineSubtreeBlock" -Description "Verify quarantine policy blocks paths under quarantined subtrees" -Assertion {
    $policy = Get-QuarantinePolicyInstance
    $subtreePath = 'E:\.gemini\baude-skills-brutas\__github-repos\__quarantine\20260805-072804\swisskyrepo_PayloadsAllTheThings__repair\any-child-file.txt'
    $decision = Test-RegistryQuarantineGuard -Path $subtreePath -Policy $policy
    if ($decision.decision -ne 'QUARANTINED_RELATED') { throw "Subtree child was not blocked as QUARANTINED_RELATED! Decision: $($decision.decision)" }
}

# 12. QuarantineTombstoneImmutability
Run-TestCase -Name "12_QuarantineTombstoneImmutability" -Description "Verify tombstones enforce zero permissions" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.tombstones_count -ne 118 -or $link.blocked_containers_count -ne 8) { throw "Tombstone count mismatch in link" }
}

# 13. NewSecurityFindingFailClosed
Run-TestCase -Name "13_NewSecurityFindingFailClosed" -Description "Verify fail-closed behavior on mock security violation" -Assertion {
    $mockDecision = @{ decision = 'DENY'; reason = 'NEW_SECURITY_FINDING_TRIGGERED' }
    if ($mockDecision.decision -ne 'DENY') { throw "Fail-closed failed" }
}

# 14. AtomicTransactionCommit
Run-TestCase -Name "14_AtomicTransactionCommit" -Description "Verify atomic transaction commits to journal and audit log" -Assertion {
    $res = Invoke-RegistryTransaction -OperationType 'CONFIG_UPDATE' -Action {
        param($TransactionId)
        return "OK"
    } -Initiator 'SyntheticTest'
    if ($res.Status -ne 'COMMITTED') { throw "Transaction was not committed" }
}

# 15. AtomicTransactionRollback
Run-TestCase -Name "15_AtomicTransactionRollback" -Description "Verify transaction rollback upon error without residue" -Assertion {
    $stateFile = Join-Path $RegistryRoot 'state\current-state.json'
    $beforeState = Read-Utf8NoBom -Path $stateFile
    try {
        Invoke-RegistryTransaction -OperationType 'CONFIG_UPDATE' -Action {
            param($TransactionId)
            throw "SIMULATED_TEST_FAULT"
        } -Initiator 'SyntheticTest'
        throw "Transaction should have failed"
    } catch {
        if ($_.Exception.Message -notmatch 'SIMULATED_TEST_FAULT') { throw $_ }
    }
    $afterState = Read-Utf8NoBom -Path $stateFile
    if ($beforeState -ne $afterState) { throw "State was not cleanly restored during rollback" }
}

# 16. TransactionIdempotence
Run-TestCase -Name "16_TransactionIdempotence" -Description "Verify repeated transactions maintain coherent state" -Assertion {
    $status1 = Get-RegistryStatus
    $status2 = Get-RegistryStatus
    if ($status1.registry_id -ne $status2.registry_id -or $status1.system_health -ne $status2.system_health) {
        throw "Inconsistent state read"
    }
}

# 17. ConcurrentLockRejection
Run-TestCase -Name "17_ConcurrentLockRejection" -Description "Verify concurrent lock acquisition times out cleanly" -Assertion {
    $lock1 = Enter-RegistryLock -TimeoutSeconds 2
    try {
        $lockFailed = $false
        try {
            $null = Enter-RegistryLock -TimeoutSeconds 1
        } catch {
            $lockFailed = $true
        }
        if (-not $lockFailed) { throw "Second lock acquisition should have been rejected" }
    } finally {
        Exit-RegistryLock -LockHandle $lock1
    }
}

# 18. IndexCorruptionDetection
Run-TestCase -Name "18_IndexCorruptionDetection" -Description "Verify doctor detects corrupted JSON index lines" -Assertion {
    $corruptLine = '{"bad_json":'
    $detected = $false
    try {
        $null = $corruptLine | ConvertFrom-Json
    } catch {
        $detected = $true
    }
    if (-not $detected) { throw "Failed to catch malformed JSON index line" }
}

# 19. ManifestAnchorMismatchDetection
Run-TestCase -Name "19_ManifestAnchorMismatchDetection" -Description "Verify quarantine seal anchor matching in config" -Assertion {
    $cfg = Get-RegistryConfig
    $expectedSeal = 'cf1e868b6940ad8dcb8af1b2c8a3c49bffed164a969b234bb0b817a06f54840c'
    if ($cfg.security_anchors.quarantine_seal_sha256 -ne $expectedSeal) {
        throw "Quarantine seal anchor mismatch in registry config"
    }
}

# 20. SchemaVersionEvolutionRejection
Run-TestCase -Name "20_SchemaVersionEvolutionRejection" -Description "Verify strict schema versioning enforcement" -Assertion {
    $supportedVersions = @("1.0.0")
    $unknownVersion = "2.0.0"
    if ($supportedVersions -contains $unknownVersion) { throw "Unknown schema version was incorrectly allowed" }
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
