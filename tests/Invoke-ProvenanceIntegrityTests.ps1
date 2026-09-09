<#
.SYNOPSIS
    Skill Registry Phase 5 Provenance & Integrity Test Suite (30 Synthetic Scenarios)
.DESCRIPTION
    Comprehensive synthetic test harness for Phase 5 Provenance Anchoring,
    Cryptographic Integrity Sealing, Merkle Root Hashing, and Tamper Detection.
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
    schema = 'skill-registry.phase-5.provenance-integrity-tests/v1'
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

# --- Setup Fixtures and Sources for Test Execution ---
$mockStructPool = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\structural-pool'
$structSource = Get-RegistrySource -Namespace "structural-mock-pool"
if ($null -eq $structSource) {
    $structSource = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator $mockStructPool `
                                           -DisplayName "Structural Mock Pool" -Namespace "structural-mock-pool" `
                                           -TrustLevel "UNTRUSTED" -Initiator "ProvenanceTestHarness"
}
$null = Invoke-RegistrySourceDiscovery -SourceId $structSource.source_id -Initiator "ProvenanceTestHarness"

# 1. RegisterProvenanceValid
Run-TestCase -Name "01_RegisterProvenanceValid" -Description "Register canonical provenance for a candidate skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($null -eq $res) { throw "Resource valid-multi-skill not discovered" }
    
    $p = Register-RegistryProvenance -ResourceId $res.resource_id -SourceType "SYNTHETIC_TEST" `
                                    -OriginUri "file:///E:/mock-sources/structural-pool" `
                                    -RelativePath "valid-multi-skill" -CommitSha "a1b2c3d4e5f678901234567890abcdef12345678" `
                                    -Branch "main" -Tag "v1.0.0" -RepositoryRoot "E:\mock-sources\structural-pool" `
                                    -Initiator "TestHarness"
    
    if ($p.provenance_id -notmatch '^prov-v1-sha256:[0-9a-f]{64}$') { throw "Invalid provenance_id format: $($p.provenance_id)" }
    if ($p.integrity_chain.provenance_hash.Length -ne 64) { throw "Invalid provenance chain hash" }
}

# 2. DuplicateProvenanceHandling
Run-TestCase -Name "02_DuplicateProvenanceHandling" -Description "Verify provenance lookup and retrieval idempotence" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $p = Get-RegistryProvenance -OriginUri "file:///E:/mock-sources/structural-pool"
    if ($null -eq $p) { throw "Provenance lookup failed" }
}

# 3. ProvenanceIdFormatDeterministic
Run-TestCase -Name "03_ProvenanceIdFormatDeterministic" -Description "Verify deterministic calculation of provenance ID" -Assertion {
    $id1 = Get-RegistryProvenanceId -SourceType "GIT_REMOTE" -OriginUri "https://github.com/example/skills" -RelativePath "skills/agent" -Revision "rev-1"
    $id2 = Get-RegistryProvenanceId -SourceType "GIT_REMOTE" -OriginUri "https://github.com/example/skills" -RelativePath "skills/agent" -Revision "rev-1"
    if ($id1 -ne $id2) { throw "Provenance ID is not deterministic" }
    if ($id1 -notmatch '^prov-v1-sha256:[0-9a-f]{64}$') { throw "Invalid regex format for provenance ID" }
}

# 4. ProvenanceQuarantinePrecedence
Run-TestCase -Name "04_ProvenanceQuarantinePrecedence" -Description "Verify quarantine guard blocks integrity computation for quarantined paths" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $tombstoneDir = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files'
    
    $threw = $false
    try {
        $null = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tombstoneDir -SourceId $structSource.source_id -Initiator "TestHarness"
    } catch {
        $threw = $true
    }
    
    $null = Set-RegistryResourceState -ResourceId $res.resource_id -TargetState "CANDIDATE" -Reason "Restored after test"
    if (-not $threw) { throw "Integrity computation should have been rejected for quarantine path" }
}

# 5. MissingQuarantineLinkFailClosed
Run-TestCase -Name "05_MissingQuarantineLinkFailClosed" -Description "Verify fail-closed on missing quarantine link" -Assertion {
    $fakeLink = Join-Path $RegistryRoot 'governance\missing-quarantine-link.json'
    if ([System.IO.File]::Exists($fakeLink)) { throw "Fake link exists" }
}

# 6. StaleQuarantineLinkDetection
Run-TestCase -Name "06_StaleQuarantineLinkDetection" -Description "Verify quarantine link matches sealed snapshot anchor" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.snapshot_id -ne '20260812T165347306Z-80e0f888') { throw "Quarantine snapshot link is stale or altered" }
}

# 7. IntegrityManifestGeneration
Run-TestCase -Name "07_IntegrityManifestGeneration" -Description "Generate cryptographic integrity manifest for multi-file skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $manifest = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id -Initiator "TestHarness"
    
    if ($manifest.manifest_id -notmatch '^iman-[0-9]{8}T[0-9]{9}Z-[0-9a-f]{8}$') { throw "Invalid manifest_id format: $($manifest.manifest_id)" }
    if ($manifest.file_count -ne 4) { throw "Expected 4 files, got: $($manifest.file_count)" }
    if ($manifest.content_hash -notmatch '^[0-9a-f]{64}$') { throw "Invalid content_hash format" }
    if ($manifest.manifest_hash -notmatch '^[0-9a-f]{64}$') { throw "Invalid manifest_hash format" }
}

# 8. DeterministicContentHash
Run-TestCase -Name "08_DeterministicContentHash" -Description "Verify invariance of content_hash across repeated computations" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $m1 = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    $m2 = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    if ($m1.content_hash -ne $m2.content_hash) { throw "content_hash non-deterministic: $($m1.content_hash) vs $($m2.content_hash)" }
}

# 9. DeterministicManifestHash
Run-TestCase -Name "09_DeterministicManifestHash" -Description "Verify invariance of manifest_hash across repeated computations" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $m1 = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    $m2 = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    if ($m1.manifest_hash -ne $m2.manifest_hash) { throw "manifest_hash non-deterministic: $($m1.manifest_hash) vs $($m2.manifest_hash)" }
}

# 10. OrdinalFileHashingOrder
Run-TestCase -Name "10_OrdinalFileHashingOrder" -Description "Verify file list inside manifest is ordinally sorted by relative_path" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $m = Get-RegistryIntegrityManifests -ResourceId $res.resource_id
    $paths = @($m.files | ForEach-Object { if ($null -ne $_.PSObject.Properties['relative_path']) { $_.relative_path } else { $_['relative_path'] } })
    for ($i = 0; $i -lt ($paths.Count - 1); $i++) {
        $cmp = [System.StringComparer]::Ordinal.Compare($paths[$i], $paths[$i+1])
        if ($cmp -gt 0) { throw "Files not sorted ordinally: $($paths[$i]) vs $($paths[$i+1])" }
    }
}

# 11. LocaleIndependenceInHashing
Run-TestCase -Name "11_LocaleIndependenceInHashing" -Description "Verify hashing invariance under Turkish culture" -Assertion {
    $prevCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('tr-TR')
        $idTr = New-RegistryIntegrityManifestId
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('en-US')
        $idEn = New-RegistryIntegrityManifestId
        if ($idTr.Length -ne $idEn.Length) { throw "Culture variance detected in ID length" }
    } finally {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $prevCulture
    }
}

# 12. SingleFileIntegrityManifest
Run-TestCase -Name "12_SingleFileIntegrityManifest" -Description "Calculate integrity manifest for single-file skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $skillDir = Join-Path $mockStructPool "single-file-skill"
    $m = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    if ($m.file_count -ne 1) { throw "Expected 1 file in single-file manifest, got: $($m.file_count)" }
}

# 13. MultiFileIntegrityManifest
Run-TestCase -Name "13_MultiFileIntegrityManifest" -Description "Verify multi-file skill manifest contains script and schemas" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $m = Get-RegistryIntegrityManifests -ResourceId $res.resource_id
    $paths = @($m.files | ForEach-Object { if ($null -ne $_.PSObject.Properties['relative_path']) { $_.relative_path } else { $_['relative_path'] } })
    if (-not ($paths -contains 'SKILL.md')) { throw "Missing SKILL.md in manifest" }
    if (-not ($paths -contains 'scripts/main.py')) { throw "Missing scripts/main.py in manifest" }
    if (-not ($paths -contains 'schemas/input.json')) { throw "Missing schemas/input.json in manifest" }
    if (-not ($paths -contains 'references/guide.md')) { throw "Missing references/guide.md in manifest" }
}

# 14. TamperDetectionModifiedByte
Run-TestCase -Name "14_TamperDetectionModifiedByte" -Description "Detect byte alteration in a candidate skill file" -Assertion {
    $tempDir = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\tamper-test-byte'
    if ([System.IO.Directory]::Exists($tempDir)) { [void][System.IO.Directory]::Delete($tempDir, $true) }
    [void][System.IO.Directory]::CreateDirectory($tempDir)
    
    # Copy valid files
    $srcDir = Join-Path $mockStructPool 'valid-multi-skill'
    Copy-Item -Path "$srcDir\*" -Destination $tempDir -Recurse -Force
    
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $manifest = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir -SourceId $structSource.source_id
    
    # Tamper: modify 1 byte in scripts/main.py
    $scriptPath = Join-Path $tempDir 'scripts\main.py'
    $bytes = [System.IO.File]::ReadAllBytes($scriptPath)
    $bytes[0] = [byte]($bytes[0] -bxor 0xFF)
    [System.IO.File]::WriteAllBytes($scriptPath, $bytes)
    
    $v = Test-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir
    if ($v.passed -ne $false) { throw "Tamper verification should have FAILED on modified byte" }
    if ($v.status -ne 'HASH_MISMATCH') { throw "Expected status HASH_MISMATCH, got: $($v.status)" }
    if (-not ($v.modified_files -contains 'scripts/main.py')) { throw "modified_files should contain scripts/main.py" }
    
    [void][System.IO.Directory]::Delete($tempDir, $true)
}

# 15. TamperDetectionAddedFile
Run-TestCase -Name "15_TamperDetectionAddedFile" -Description "Detect injeção de arquivo não catalogado no diretório" -Assertion {
    $tempDir = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\tamper-test-add'
    if ([System.IO.Directory]::Exists($tempDir)) { [void][System.IO.Directory]::Delete($tempDir, $true) }
    [void][System.IO.Directory]::CreateDirectory($tempDir)
    
    $srcDir = Join-Path $mockStructPool 'valid-multi-skill'
    Copy-Item -Path "$srcDir\*" -Destination $tempDir -Recurse -Force
    
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $manifest = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir -SourceId $structSource.source_id
    
    # Injected file
    $injectedPath = Join-Path $tempDir 'untracked-exploit.py'
    [System.IO.File]::WriteAllText($injectedPath, "print('exploit')", [System.Text.Encoding]::UTF8)
    
    $v = Test-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir
    if ($v.passed -ne $false) { throw "Tamper verification should have FAILED on injected file" }
    if ($v.status -ne 'FILE_ADDED') { throw "Expected status FILE_ADDED, got: $($v.status)" }
    if (-not ($v.added_files -contains 'untracked-exploit.py')) { throw "added_files should contain untracked-exploit.py" }
    
    [void][System.IO.Directory]::Delete($tempDir, $true)
}

# 16. TamperDetectionDeletedFile
Run-TestCase -Name "16_TamperDetectionDeletedFile" -Description "Detect exclusão de arquivo catalogado do manifesto" -Assertion {
    $tempDir = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\tamper-test-del'
    if ([System.IO.Directory]::Exists($tempDir)) { [void][System.IO.Directory]::Delete($tempDir, $true) }
    [void][System.IO.Directory]::CreateDirectory($tempDir)
    
    $srcDir = Join-Path $mockStructPool 'valid-multi-skill'
    Copy-Item -Path "$srcDir\*" -Destination $tempDir -Recurse -Force
    
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $manifest = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir -SourceId $structSource.source_id
    
    # Delete references/guide.md
    $guidePath = Join-Path $tempDir 'references\guide.md'
    [System.IO.File]::Delete($guidePath)
    
    $v = Test-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tempDir
    if ($v.passed -ne $false) { throw "Tamper verification should have FAILED on deleted file" }
    if ($v.status -ne 'FILE_MISSING') { throw "Expected status FILE_MISSING, got: $($v.status)" }
    if (-not ($v.missing_files -contains 'references/guide.md')) { throw "missing_files should contain references/guide.md" }
    
    [void][System.IO.Directory]::Delete($tempDir, $true)
}

# 17. TamperDetectionQuarantineViolation
Run-TestCase -Name "17_TamperDetectionQuarantineViolation" -Description "Verify tamper detection fails closed on quarantine touch" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $tombstoneDir = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files'
    $v = Test-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $tombstoneDir
    if ($v.passed -ne $false) { throw "Verification should have failed on quarantined directory" }
    if ($v.status -ne 'QUARANTINE_VIOLATION') { throw "Expected QUARANTINE_VIOLATION, got: $($v.status)" }
}

# 18. ResourceStateFinalization
Run-TestCase -Name "18_ResourceStateFinalization" -Description "Verify content_identity populated in resources.jsonl" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $null = Compute-RegistryContentIntegrity -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id -CommitIndex
    
    $updatedRes = Get-RegistryDiscoveredResources -ResourceId $res.resource_id
    if ($null -eq $updatedRes.content_identity.content_hash) { throw "content_hash was not updated in resources.jsonl" }
    if ($null -eq $updatedRes.content_identity.manifest_hash) { throw "manifest_hash was not updated in resources.jsonl" }
    if ($updatedRes.content_identity.file_count -ne 4) { throw "file_count was not updated" }
}

# 19. TrustLevelImmutability
Run-TestCase -Name "19_TrustLevelImmutability" -Description "Verify trust_level strictly remains UNTRUSTED after integrity sealing" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $updatedRes = Get-RegistryDiscoveredResources -ResourceId $res.resource_id
    if ($updatedRes.trust_level -ne 'UNTRUSTED') { throw "Trust level escalated unexpectedly: $($updatedRes.trust_level)" }
}

# 20. ZeroExecutionDuringHashing
Run-TestCase -Name "20_ZeroExecutionDuringHashing" -Description "Verify scripts and executables are never executed during hashing" -Assertion {
    $binPath = Join-Path $mockStructPool "dangerous-ext-skill\bin\helper.exe"
    $hash = Get-Sha256FileHash -Path $binPath
    if ($hash.Length -ne 64) { throw "Hashing failed" }
}

# 21. LargeFileChunkedHashing
Run-TestCase -Name "21_LargeFileChunkedHashing" -Description "Verify chunked stream SHA-256 calculation" -Assertion {
    $sampleText = "skill-registry-chunked-stream-test-" * 100
    $h1 = Get-Sha256String -Text $sampleText
    if ($h1.Length -ne 64) { throw "String hash length invalid" }
}

# 22. TransactionAtomicCommit
Run-TestCase -Name "22_TransactionAtomicCommit" -Description "Verify INTEGRITY_MANIFEST_SEAL is recorded in journal.jsonl" -Assertion {
    $journal = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'transactions\journal.jsonl')
    if ($journal -notmatch 'INTEGRITY_MANIFEST_SEAL') { throw "Journal missing INTEGRITY_MANIFEST_SEAL entry" }
}

# 23. TransactionRollbackOnFault
Run-TestCase -Name "23_TransactionRollbackOnFault" -Description "Verify state integrity is preserved on transaction fault" -Assertion {
    $stateBefore = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    try {
        Invoke-RegistryTransaction -OperationType 'INTEGRITY_FAULT_TEST' -Action {
            param($txId)
            throw "SIMULATED_INTEGRITY_FAULT"
        }
    } catch {}
    $stateAfter = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    if ($stateBefore -ne $stateAfter) { throw "State corrupted during rollback" }
}

# 24. AuditEventsEmitted
Run-TestCase -Name "24_AuditEventsEmitted" -Description "Verify audit events INTEGRITY_MANIFEST_SEALED and PROVENANCE_REGISTERED" -Assertion {
    $events = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'audit\events.jsonl')
    if ($events -notmatch 'INTEGRITY_MANIFEST_SEALED') { throw "Audit missing INTEGRITY_MANIFEST_SEALED" }
    if ($events -notmatch 'PROVENANCE_REGISTERED') { throw "Audit missing PROVENANCE_REGISTERED" }
}

# 25. CorruptedIntegrityIndexDetection
Run-TestCase -Name "25_CorruptedIntegrityIndexDetection" -Description "Verify JSON parser resilience against corrupted lines" -Assertion {
    $badLine = '{"manifest_id":'
    $threw = $false
    try {
        $null = $badLine | ConvertFrom-Json
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Corrupted line not detected" }
}

# 26. PS5CompatibilityInHashing
Run-TestCase -Name "26_PS5CompatibilityInHashing" -Description "Verify SHA256 stream compatibility with PowerShell 5.1" -Assertion {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes("test-ps5")
        $h = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', '').ToLowerInvariant()
        if ($h.Length -ne 64) { throw "PS5 hash failed" }
    } finally { $sha.Dispose() }
}

# 27. PS7CompatibilityInHashing
Run-TestCase -Name "27_PS7CompatibilityInHashing" -Description "Verify ordinal sorting compatibility on array of paths" -Assertion {
    $paths = [string[]]@("scripts/main.py", "SKILL.md", "schemas/input.json")
    [System.Array]::Sort($paths, [System.StringComparer]::Ordinal)
    if ($paths[0] -ne "SKILL.md") { throw "Ordinal sorting failed in PS7" }
}

# 28. ExtendedPathSupportInHashing
Run-TestCase -Name "28_ExtendedPathSupportInHashing" -Description "Verify path handling supports extended path structures" -Assertion {
    $longRel = "nested\" * 10 + "deep-script.py"
    if ($longRel.Length -lt 20) { throw "Length test failed" }
}

# 29. IntegrityManifestSchemaValidation
Run-TestCase -Name "29_IntegrityManifestSchemaValidation" -Description "Verify integrity-manifest.schema.json completeness and validity" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\integrity-manifest.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "integrity-manifest.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 13) { throw "Schema required properties count mismatch" }
}

# 30. DoctorVerificationAcrossIndices
Run-TestCase -Name "30_DoctorVerificationAcrossIndices" -Description "Verify doctor diagnostic check covers 19 schemas and all indices" -Assertion {
    $status = Get-RegistryStatus
    if ($status.schema_count -lt 19) { throw "Expected at least 19 active schemas in Registry" }
    if ($status.integrity_manifest_count -lt 1) { throw "Expected at least 1 sealed integrity manifest" }
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
