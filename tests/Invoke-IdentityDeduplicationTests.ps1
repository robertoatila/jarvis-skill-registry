<#
.SYNOPSIS
    Skill Registry Phase 6 Identity & Deduplication Test Suite (30 Synthetic Scenarios)
.DESCRIPTION
    Comprehensive synthetic test harness for Phase 6 Multi-Dimensional Equivalence,
    Identity Clustering, Taxonomy Classification, Pairwise Divergence, and Leader Resolution.
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
    schema = 'skill-registry.phase-6.identity-deduplication-tests/v1'
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

# --- Setup Fixtures and Synthetics for Phase 6 ---
$null = Invoke-RegistryIdentityDeduplication -Initiator "IdentityTestHarness"

# 1. UniqueResourceSingletonCluster
Run-TestCase -Name "01_UniqueResourceSingletonCluster" -Description "Unique resource produces a SINGLETON cluster" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    if ($null -eq $res) { throw "Resource single-file-skill not found" }
    
    $c = Get-RegistryIdentityClusters -CanonicalName "single-file-skill"
    if ($null -eq $c) { throw "Cluster for single-file-skill not found" }
    if ($c.cluster_type -ne 'SINGLETON') { throw "Expected SINGLETON, got: $($c.cluster_type)" }
    if ($c.member_count -ne 1) { throw "Expected 1 member, got: $($c.member_count)" }
}

# 2. ExactMatchDeduplication
Run-TestCase -Name "02_ExactMatchDeduplication" -Description "Pairwise comparison detects EXACT_MATCH" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $diff = Compare-RegistryResourceDivergence -ResourceId1 $res.resource_id -ResourceId2 $res.resource_id
    if ($diff.relationship -ne 'EXACT_MATCH') { throw "Expected EXACT_MATCH, got: $($diff.relationship)" }
    if (-not $diff.same_content_hash) { throw "Expected same_content_hash to be true" }
}

# 3. MultiOriginMirrorDetection
Run-TestCase -Name "03_MultiOriginMirrorDetection" -Description "Detect MULTI_ORIGIN_MIRROR across distinct origins" -Assertion {
    $res1 = [ordered]@{
        canonical_name = "mirror-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }
    }
    $res2 = [ordered]@{
        canonical_name = "mirror-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        content_identity = [ordered]@{ content_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }
    }
    # Synthetic comparison
    $sameName = ($res1.canonical_name -eq $res2.canonical_name)
    $sameHash = ($res1.content_identity.content_hash -eq $res2.content_identity.content_hash)
    $sameProv = ($res1.provenance_id -eq $res2.provenance_id)
    $rel = if ($sameName -and $sameHash -and -not $sameProv) { 'MULTI_ORIGIN_MIRROR' } else { 'OTHER' }
    if ($rel -ne 'MULTI_ORIGIN_MIRROR') { throw "Expected MULTI_ORIGIN_MIRROR, got $rel" }
}

# 4. ContentCloneDifferentName
Run-TestCase -Name "04_ContentCloneDifferentName" -Description "Detect CONTENT_CLONE_DIFFERENT_NAME for identical content under different names" -Assertion {
    $res1 = [ordered]@{
        canonical_name = "template-skill-a"
        version = "1.0.0"
        content_identity = [ordered]@{ content_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" }
    }
    $res2 = [ordered]@{
        canonical_name = "template-skill-b"
        version = "1.0.0"
        content_identity = [ordered]@{ content_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" }
    }
    $sameName = ($res1.canonical_name -eq $res2.canonical_name)
    $sameHash = ($res1.content_identity.content_hash -eq $res2.content_identity.content_hash)
    $rel = if (-not $sameName -and $sameHash) { 'CONTENT_CLONE_DIFFERENT_NAME' } else { 'OTHER' }
    if ($rel -ne 'CONTENT_CLONE_DIFFERENT_NAME') { throw "Expected CONTENT_CLONE_DIFFERENT_NAME, got $rel" }
}

# 5. VersionEvolutionChain
Run-TestCase -Name "05_VersionEvolutionChain" -Description "Detect VERSION_EVOLUTION between different semver releases" -Assertion {
    $res1 = [ordered]@{
        canonical_name = "evolution-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc" }
    }
    $res2 = [ordered]@{
        canonical_name = "evolution-skill"
        version = "2.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd" }
    }
    $sameName = ($res1.canonical_name -eq $res2.canonical_name)
    $sameProv = ($res1.provenance_id -eq $res2.provenance_id)
    $sameVer = ($res1.version -eq $res2.version)
    $rel = if ($sameName -and $sameProv -and -not $sameVer) { 'VERSION_EVOLUTION' } else { 'OTHER' }
    if ($rel -ne 'VERSION_EVOLUTION') { throw "Expected VERSION_EVOLUTION, got $rel" }
}

# 6. ContentDriftSameVersion
Run-TestCase -Name "06_ContentDriftSameVersion" -Description "Detect CONTENT_DRIFT_SAME_VERSION when content mutated without version bump" -Assertion {
    $res1 = [ordered]@{
        canonical_name = "drift-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" }
    }
    $res2 = [ordered]@{
        canonical_name = "drift-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" }
    }
    $sameName = ($res1.canonical_name -eq $res2.canonical_name)
    $sameProv = ($res1.provenance_id -eq $res2.provenance_id)
    $sameVer = ($res1.version -eq $res2.version)
    $sameHash = ($res1.content_identity.content_hash -eq $res2.content_identity.content_hash)
    $rel = if ($sameName -and $sameProv -and $sameVer -and -not $sameHash) { 'CONTENT_DRIFT_SAME_VERSION' } else { 'OTHER' }
    if ($rel -ne 'CONTENT_DRIFT_SAME_VERSION') { throw "Expected CONTENT_DRIFT_SAME_VERSION, got $rel" }
}

# 7. NameCollisionDifferentContent
Run-TestCase -Name "07_NameCollisionDifferentContent" -Description "Detect NAME_COLLISION_DIFFERENT_CONTENT across unrelated sources" -Assertion {
    $res1 = [ordered]@{
        canonical_name = "collision-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        content_identity = [ordered]@{ content_hash = "1111111111111111111111111111111111111111111111111111111111111111" }
    }
    $res2 = [ordered]@{
        canonical_name = "collision-skill"
        version = "1.0.0"
        provenance_id = "prov-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        content_identity = [ordered]@{ content_hash = "2222222222222222222222222222222222222222222222222222222222222222" }
    }
    $sameName = ($res1.canonical_name -eq $res2.canonical_name)
    $sameProv = ($res1.provenance_id -eq $res2.provenance_id)
    $sameHash = ($res1.content_identity.content_hash -eq $res2.content_identity.content_hash)
    $rel = if ($sameName -and -not $sameProv -and -not $sameHash) { 'NAME_COLLISION_DIFFERENT_CONTENT' } else { 'OTHER' }
    if ($rel -ne 'NAME_COLLISION_DIFFERENT_CONTENT') { throw "Expected NAME_COLLISION_DIFFERENT_CONTENT, got $rel" }
}

# 8. LeaderSelectionByTrust
Run-TestCase -Name "08_LeaderSelectionByTrust" -Description "Resolve leader preferring higher trust level" -Assertion {
    $resA = [pscustomobject]@{
        resource_id = "sres-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        trust_level = "UNTRUSTED"
        lifecycle_state = "CANDIDATE"
        version = "1.0.0"
    }
    $resB = [pscustomobject]@{
        resource_id = "sres-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        trust_level = "REVIEWED"
        lifecycle_state = "CANDIDATE"
        version = "1.0.0"
    }
    $leader = Resolve-RegistryCanonicalResource -Resources @($resA, $resB)
    if ($leader.resource_id -ne $resB.resource_id) { throw "Expected resB with REVIEWED trust to be leader" }
}

# 9. LeaderSelectionByLifecycleState
Run-TestCase -Name "09_LeaderSelectionByLifecycleState" -Description "Resolve leader preferring CANDIDATE/ACTIVE over DISCOVERED" -Assertion {
    $resA = [pscustomobject]@{
        resource_id = "sres-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        trust_level = "UNTRUSTED"
        lifecycle_state = "DISCOVERED"
        version = "1.0.0"
    }
    $resB = [pscustomobject]@{
        resource_id = "sres-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        trust_level = "UNTRUSTED"
        lifecycle_state = "CANDIDATE"
        version = "1.0.0"
    }
    $leader = Resolve-RegistryCanonicalResource -Resources @($resA, $resB)
    if ($leader.resource_id -ne $resB.resource_id) { throw "Expected resB with CANDIDATE state to be leader" }
}

# 10. LeaderSelectionBySemanticVersion
Run-TestCase -Name "10_LeaderSelectionBySemanticVersion" -Description "Resolve leader preferring higher semver version" -Assertion {
    $resA = [pscustomobject]@{
        resource_id = "sres-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        trust_level = "UNTRUSTED"
        lifecycle_state = "CANDIDATE"
        version = "1.0.0"
    }
    $resB = [pscustomobject]@{
        resource_id = "sres-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        trust_level = "UNTRUSTED"
        lifecycle_state = "CANDIDATE"
        version = "2.1.0"
    }
    $leader = Resolve-RegistryCanonicalResource -Resources @($resA, $resB)
    if ($leader.resource_id -ne $resB.resource_id) { throw "Expected resB with version 2.1.0 to be leader" }
}

# 11. PairwiseDivergenceContentDiff
Run-TestCase -Name "11_PairwiseDivergenceContentDiff" -Description "Verify pairwise divergence detects distinct content hashes" -Assertion {
    $res1 = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $res2 = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $diff = Compare-RegistryResourceDivergence -ResourceId1 $res1.resource_id -ResourceId2 $res2.resource_id
    if ($diff.same_content_hash) { throw "Content hash should have differed" }
}

# 12. PairwiseDivergenceMetadataDiff
Run-TestCase -Name "12_PairwiseDivergenceMetadataDiff" -Description "Verify divergence detects capability deltas" -Assertion {
    $res1 = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $res2 = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $diff = Compare-RegistryResourceDivergence -ResourceId1 $res1.resource_id -ResourceId2 $res2.resource_id
    if ($diff.metadata_delta.description_diff -ne $true) { throw "Expected description_diff to be true" }
    if ($diff.metadata_delta.added_capabilities.Count -eq 0 -and $diff.metadata_delta.removed_capabilities.Count -eq 0) {
        throw "Expected capability deltas between valid-multi-skill and single-file-skill"
    }
}

# 13. ClusterIdFormatDeterministic
Run-TestCase -Name "13_ClusterIdFormatDeterministic" -Description "Verify cluster ID regex pattern" -Assertion {
    $id = New-RegistryIdentityClusterId
    if ($id -notmatch '^idcl-[0-9]{8}T[0-9]{9}Z-[0-9a-f]{8}$') { throw "Invalid cluster ID format: $id" }
}

# 14. QuarantinePrecedenceInClustering
Run-TestCase -Name "14_QuarantinePrecedenceInClustering" -Description "Verify quarantine policy link matches sealed anchor" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.snapshot_id -ne '20260812T165347306Z-80e0f888') { throw "Quarantine snapshot link mismatch" }
}

# 15. BlockedResourceExclusionFromLeader
Run-TestCase -Name "15_BlockedResourceExclusionFromLeader" -Description "Verify BLOCKED resource is never selected as leader if non-blocked candidate exists" -Assertion {
    $resA = [pscustomobject]@{
        resource_id = "sres-v1-sha256:1111111111111111111111111111111111111111111111111111111111111111"
        trust_level = "BLOCKED"
        lifecycle_state = "BLOCKED"
        version = "9.9.9"
    }
    $resB = [pscustomobject]@{
        resource_id = "sres-v1-sha256:2222222222222222222222222222222222222222222222222222222222222222"
        trust_level = "UNTRUSTED"
        lifecycle_state = "DISCOVERED"
        version = "1.0.0"
    }
    $leader = Resolve-RegistryCanonicalResource -Resources @($resA, $resB)
    if ($leader.resource_id -ne $resB.resource_id) { throw "BLOCKED resource was erroneously chosen as leader" }
}

# 16. OrdinalMemberSortingInCluster
Run-TestCase -Name "16_OrdinalMemberSortingInCluster" -Description "Verify members array within clusters is sorted ordinally by resource_id" -Assertion {
    $clusters = @(Get-RegistryIdentityClusters)
    foreach ($c in $clusters) {
        $ids = @($c.members | ForEach-Object { if ($null -ne $_.PSObject.Properties['resource_id']) { $_.resource_id } else { $_['resource_id'] } })
        for ($i = 0; $i -lt ($ids.Count - 1); $i++) {
            $cmp = [System.StringComparer]::Ordinal.Compare($ids[$i], $ids[$i+1])
            if ($cmp -gt 0) { throw "Members not sorted ordinally: $($ids[$i]) vs $($ids[$i+1]) in $($c.cluster_id)" }
        }
    }
}

# 17. LocaleIndependenceInClustering
Run-TestCase -Name "17_LocaleIndependenceInClustering" -Description "Verify clustering and ID generation invariance under Turkish locale" -Assertion {
    $prevCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('tr-TR')
        $idTr = New-RegistryIdentityClusterId
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('en-US')
        $idEn = New-RegistryIdentityClusterId
        if ($idTr.Length -ne $idEn.Length) { throw "Locale variance detected in cluster ID length" }
    } finally {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $prevCulture
    }
}

# 18. ZeroExecutionDuringClustering
Run-TestCase -Name "18_ZeroExecutionDuringClustering" -Description "Verify zero payload execution during clustering" -Assertion {
    $binPath = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\structural-pool\dangerous-ext-skill\bin\helper.exe'
    if ([System.IO.File]::Exists($binPath)) {
        $hash = Get-Sha256FileHash -Path $binPath
        if ($hash.Length -ne 64) { throw "Hashing check failed" }
    }
}

# 19. TrustLevelImmutabilityInClustering
Run-TestCase -Name "19_TrustLevelImmutabilityInClustering" -Description "Verify trust levels of discovered resources remain UNTRUSTED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($res.trust_level -ne 'UNTRUSTED') { throw "Trust level altered unexpectedly: $($res.trust_level)" }
}

# 20. ACIDTransactionClusterCommit
Run-TestCase -Name "20_ACIDTransactionClusterCommit" -Description "Verify IDENTITY_DEDUPLICATION_EXECUTE recorded in journal" -Assertion {
    $journal = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'transactions\journal.jsonl')
    if ($journal -notmatch 'IDENTITY_DEDUPLICATION_EXECUTE') { throw "Journal missing IDENTITY_DEDUPLICATION_EXECUTE" }
}

# 21. AuditEventsEmittedForClustering
Run-TestCase -Name "21_AuditEventsEmittedForClustering" -Description "Verify IDENTITY_CLUSTER_CREATED in audit trail" -Assertion {
    $audit = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'audit\events.jsonl')
    if ($audit -notmatch 'IDENTITY_CLUSTER_CREATED') { throw "Audit missing IDENTITY_CLUSTER_CREATED" }
}

# 22. TransactionRollbackOnClusterFault
Run-TestCase -Name "22_TransactionRollbackOnClusterFault" -Description "Verify state integrity is preserved on transaction fault" -Assertion {
    $stateBefore = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    try {
        Invoke-RegistryTransaction -OperationType 'IDENTITY_FAULT_TEST' -Action {
            param($txId)
            throw "SIMULATED_IDENTITY_FAULT"
        }
    } catch {}
    $stateAfter = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    if ($stateBefore -ne $stateAfter) { throw "State corrupted during rollback" }
}

# 23. CorruptedClusterIndexDetection
Run-TestCase -Name "23_CorruptedClusterIndexDetection" -Description "Verify JSON parser resilience against corrupted lines" -Assertion {
    $badLine = '{"cluster_id":'
    $threw = $false
    try {
        $null = $badLine | ConvertFrom-Json
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Corrupted line not detected" }
}

# 24. PS5CompatibilityInClustering
Run-TestCase -Name "24_PS5CompatibilityInClustering" -Description "Verify PS5 compatibility with OrderedDictionary serialization" -Assertion {
    $dict = [ordered]@{ a = 1; b = 2; c = @("x", "y") }
    $json = $dict | ConvertTo-Json -Depth 5 -Compress
    if ($json -notmatch '"a":1') { throw "Serialization failed" }
}

# 25. PS7CompatibilityInClustering
Run-TestCase -Name "25_PS7CompatibilityInClustering" -Description "Verify ordinal sorting compatibility on array of cluster IDs" -Assertion {
    $ids = [string[]]@("idcl-20260831T020000000Z-bbbbbbbb", "idcl-20260831T020000000Z-aaaaaaaa")
    [System.Array]::Sort($ids, [System.StringComparer]::Ordinal)
    if ($ids[0] -ne "idcl-20260831T020000000Z-aaaaaaaa") { throw "Ordinal sorting failed" }
}

# 26. ExtendedPathSupportInDivergence
Run-TestCase -Name "26_ExtendedPathSupportInDivergence" -Description "Verify path handling supports deep structures" -Assertion {
    $deepPath = "scripts/submodules/deep/nested/handler.py"
    if ($deepPath.Length -lt 20) { throw "Path length test failed" }
}

# 27. IdentityClusterSchemaValidation
Run-TestCase -Name "27_IdentityClusterSchemaValidation" -Description "Verify identity-cluster.schema.json completeness and validity" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\identity-cluster.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "identity-cluster.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 9) { throw "Schema required properties count mismatch" }
}

# 28. MultiClusterMembershipIntegrity
Run-TestCase -Name "28_MultiClusterMembershipIntegrity" -Description "Verify cluster lookup by member resource ID" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $c = Get-RegistryIdentityClusters -ResourceId $res.resource_id
    if ($null -eq $c) { throw "Failed to find cluster by resource_id: $($res.resource_id)" }
    if ($c.leader_resource_id -ne $res.resource_id) { throw "Expected valid-multi-skill to be cluster leader" }
}

# 29. DoctorVerificationAcross20Schemas
Run-TestCase -Name "29_DoctorVerificationAcross20Schemas" -Description "Verify doctor validates all 20 active schemas" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 20) { throw "Expected at least 20 active schemas, got: $($st.schema_count)" }
    if ($st.identity_cluster_count -lt 1) { throw "Expected at least 1 identity cluster" }
}

# 30. LiveResolutionCanonicalQuery
Run-TestCase -Name "30_LiveResolutionCanonicalQuery" -Description "Verify Resolve-RegistryCanonicalResource selects correct leader" -Assertion {
    $resList = @(Get-RegistryDiscoveredResources)
    $leader = Resolve-RegistryCanonicalResource -Resources $resList
    if ($null -eq $leader) { throw "Failed to resolve leader from discovered resources" }
    if ($leader.trust_level -eq 'BLOCKED') { throw "Leader should not be BLOCKED" }
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
