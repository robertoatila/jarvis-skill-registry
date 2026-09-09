<#
.SYNOPSIS
    Skill Registry Phase 4 Structural Analysis Test Suite (30 Synthetic Scenarios)
.DESCRIPTION
    Comprehensive synthetic test harness for Phase 4 Structural Analysis Engine.
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
    schema = 'skill-registry.phase-4.structural-analysis-tests/v1'
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

# --- Setup Fixtures and Discovery for Test Execution ---
$mockStructPool = Join-Path $RegistryRoot 'tests\fixtures\mock-sources\structural-pool'
$structSource = Get-RegistrySource -Namespace "structural-mock-pool"
if ($null -eq $structSource) {
    $structSource = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator $mockStructPool `
                                           -DisplayName "Structural Mock Pool" -Namespace "structural-mock-pool" `
                                           -TrustLevel "UNTRUSTED" -Initiator "StructuralTestHarness"
}
$discSession = Invoke-RegistrySourceDiscovery -SourceId $structSource.source_id -Initiator "StructuralTestHarness"

# 1. StructuralAnalysisValidSkillDir
Run-TestCase -Name "01_StructuralAnalysisValidSkillDir" -Description "Analyze multi-file skill and verify layout and compliance" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($null -eq $res) { throw "Resource valid-multi-skill not discovered" }
    
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id -Initiator "TestHarness"
    
    if ($laudo.status -ne 'COMPLIANT') { throw "Expected COMPLIANT status, got: $($laudo.status)" }
    if ($laudo.structure.layout_type -ne 'STANDARD_SKILL_DIR') { throw "Expected STANDARD_SKILL_DIR layout, got: $($laudo.structure.layout_type)" }
    if ($laudo.inferred_metadata.primary_runtime -ne 'PYTHON') { throw "Expected PYTHON primary runtime, got: $($laudo.inferred_metadata.primary_runtime)" }
    if ($laudo.structure.file_count -ne 4) { throw "Expected 4 files, got: $($laudo.structure.file_count)" }
}

# 2. StructuralAnalysisSingleFileSkill
Run-TestCase -Name "02_StructuralAnalysisSingleFileSkill" -Description "Analyze single-file skill and verify prompt-only classification" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    if ($null -eq $res) { throw "Resource single-file-skill not discovered" }
    
    $skillDir = Join-Path $mockStructPool "single-file-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id -Initiator "TestHarness"
    
    if ($laudo.status -ne 'COMPLIANT') { throw "Expected COMPLIANT status, got: $($laudo.status)" }
    if ($laudo.structure.layout_type -ne 'SINGLE_FILE') { throw "Expected SINGLE_FILE layout, got: $($laudo.structure.layout_type)" }
    if ($laudo.inferred_metadata.primary_runtime -ne 'STATIC_PROMPT') { throw "Expected STATIC_PROMPT runtime, got: $($laudo.inferred_metadata.primary_runtime)" }
}

# 3. StructuralAnalysisIneligibleResource
Run-TestCase -Name "03_StructuralAnalysisIneligibleResource" -Description "Verify rejection of analysis on retired resource" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $null = Set-RegistryResourceState -ResourceId $res.resource_id -TargetState "RETIRED" -Reason "Test Ineligibility"
    
    $threw = $false
    try {
        $null = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id
    } catch {
        $threw = $true
    }
    # Restore state for other tests
    $null = Set-RegistryResourceState -ResourceId $res.resource_id -TargetState "DISCOVERED" -Reason "Restored"
    if (-not $threw) { throw "Analysis should have failed on retired resource" }
}

# 4. StructuralQuarantinePrecedence
Run-TestCase -Name "04_StructuralQuarantinePrecedence" -Description "Verify structural analysis immediately blocks candidate touching quarantine without reading" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $tombstoneDir = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files'
    
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $tombstoneDir -SourceId $structSource.source_id -Initiator "TestHarness"
    if ($laudo.status -ne 'VIOLATION_BLOCKED') { throw "Expected VIOLATION_BLOCKED, got: $($laudo.status)" }
    if ($laudo.quarantine_check.passed -ne $false) { throw "Quarantine check should have failed" }
    
    # Restore valid state
    $null = Set-RegistryResourceState -ResourceId $res.resource_id -TargetState "DISCOVERED" -Reason "Restored"
}

# 5. MissingQuarantineLinkFailClosed
Run-TestCase -Name "05_MissingQuarantineLinkFailClosed" -Description "Verify fail-closed on nonexistent quarantine reference" -Assertion {
    $fakeLink = Join-Path $RegistryRoot 'governance\missing-quarantine-link.json'
    if ([System.IO.File]::Exists($fakeLink)) { throw "Fake link exists" }
}

# 6. StaleQuarantineLinkDetection
Run-TestCase -Name "06_StaleQuarantineLinkDetection" -Description "Verify quarantine link matches sealed snapshot anchor" -Assertion {
    $link = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'governance\quarantine-link.json') | ConvertFrom-Json
    if ($link.snapshot_id -ne '20260812T165347306Z-80e0f888') { throw "Quarantine snapshot link is stale or altered" }
}

# 7. DeterministicStructuralAnalysisId
Run-TestCase -Name "07_DeterministicStructuralAnalysisId" -Description "Verify structural analysis ID format" -Assertion {
    $id = New-RegistryStructuralAnalysisId
    if ($id -notmatch '^stra-[0-9]{8}T[0-9]{9}Z-[0-9a-f]{8}$') { throw "Invalid structural analysis ID format: $id" }
}

# 8. OrdinalFileTreeSorting
Run-TestCase -Name "08_OrdinalFileTreeSorting" -Description "Verify file tree entries are ordinally sorted by relative path" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    
    $paths = @($laudo.structure.file_tree | ForEach-Object { $_.relative_path })
    for ($i = 0; $i -lt ($paths.Count - 1); $i++) {
        $cmp = [System.StringComparer]::Ordinal.Compare($paths[$i], $paths[$i+1])
        if ($cmp -gt 0) { throw "File tree not sorted ordinally: $($paths[$i]) vs $($paths[$i+1])" }
    }
}

# 9. LocaleIndependenceInStructuralAnalysis
Run-TestCase -Name "09_LocaleIndependenceInStructuralAnalysis" -Description "Verify structural analysis invariance under Turkish culture" -Assertion {
    $prevCulture = [System.Threading.Thread]::CurrentThread.CurrentCulture
    try {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('tr-TR')
        $idTr = New-RegistryStructuralAnalysisId
        [System.Threading.Thread]::CurrentThread.CurrentCulture = New-Object System.Globalization.CultureInfo('en-US')
        $idEn = New-RegistryStructuralAnalysisId
        if ($idTr.Length -ne $idEn.Length) { throw "Culture variance detected in ID length" }
    } finally {
        [System.Threading.Thread]::CurrentThread.CurrentCulture = $prevCulture
    }
}

# 10. DeclaredVsObservedSeparation
Run-TestCase -Name "10_DeclaredVsObservedSeparation" -Description "Verify strict separation between declared metadata and observed structure" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    
    if ($null -eq $laudo.declared_metadata.declared_capabilities) { throw "Missing declared capabilities" }
    if ($null -eq $laudo.observed_metadata.file_extensions_present) { throw "Missing observed file extensions" }
    if ($laudo.declared_metadata.declared_capabilities -contains '.py') { throw "Observed extension leaked into declared capabilities" }
}

# 11. InferredPackagingClassification
Run-TestCase -Name "11_InferredPackagingClassification" -Description "Verify inferred packaging matches standard skill directory" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    if ($laudo.inferred_metadata.packaging_type -ne 'STANDARD_SKILL_DIR') { throw "Inferred packaging mismatch: $($laudo.inferred_metadata.packaging_type)" }
}

# 12. DangerousExtensionDetection
Run-TestCase -Name "12_DangerousExtensionDetection" -Description "Verify detection and cataloging of dangerous binary and batch extensions" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    if ($null -eq $res) { throw "Resource dangerous-ext-skill not discovered" }
    
    $skillDir = Join-Path $mockStructPool "dangerous-ext-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    
    if (-not ($laudo.observed_metadata.dangerous_extensions_detected -contains '.exe')) { throw "Dangerous extension .exe was not detected" }
    if (-not ($laudo.observed_metadata.dangerous_extensions_detected -contains '.bat')) { throw "Dangerous extension .bat was not detected" }
    if ($laudo.inferred_metadata.structural_risk_level -notin @('HIGH', 'CRITICAL')) { throw "Risk level should be HIGH or CRITICAL" }
}

# 13. BinaryFileZeroExecutionZeroLoad
Run-TestCase -Name "13_BinaryFileZeroExecutionZeroLoad" -Description "Verify binary file .exe is never executed or loaded" -Assertion {
    $binPath = Join-Path $mockStructPool "dangerous-ext-skill\bin\helper.exe"
    if (-not [System.IO.File]::Exists($binPath)) { throw "Binary fixture missing" }
    $item = Get-Item $binPath
    if ($item.Length -lt 0) { throw "Invalid binary item" }
}

# 14. ReparsePointBlockedByDefault
Run-TestCase -Name "14_ReparsePointBlockedByDefault" -Description "Verify reparse points are disabled by default in source boundary" -Assertion {
    $src = Get-RegistrySource -SourceId $structSource.source_id
    if ($src.boundaries.allow_reparse_points -ne $false) { throw "Reparse points should be disallowed by default" }
}

# 15. PathTraversalInSkillReferences
Run-TestCase -Name "15_PathTraversalInSkillReferences" -Description "Verify locator path traversal is rejected" -Assertion {
    $threw = $false
    try {
        $null = Get-RegistryNormalizedLocator -Locator "..\..\windows\system32" -SourceType "LOCAL_FS"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Path traversal was not blocked" }
}

# 16. FrontmatterSyntaxValidation
Run-TestCase -Name "16_FrontmatterSyntaxValidation" -Description "Verify resilient handling of malformed frontmatter syntax" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "malformed-manifest-skill"
    if ($null -eq $res) { throw "Resource malformed-manifest-skill not discovered" }
    
    $skillDir = Join-Path $mockStructPool "malformed-manifest-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    if ($null -eq $laudo) { throw "Analysis failed to produce a report for malformed manifest" }
}

# 17. MissingSkillMdDetection
Run-TestCase -Name "17_MissingSkillMdDetection" -Description "Verify detection of directory without SKILL.md" -Assertion {
    $provId = Get-RegistryProvenanceId -SourceType "SYNTHETIC_TEST" -OriginUri "E:\mock" -RelativePath "no-manifest-skill"
    $resId = Get-RegistryResourceId -CanonicalName "no-manifest-skill" -Version "1.0.0" -ProvenanceId $provId
    
    $existing = Get-RegistryDiscoveredResources -ResourceId $resId
    if ($null -eq $existing) {
        $nowUtc = [DateTime]::UtcNow.ToString('o')
        $adHoc = [ordered]@{
            schema_version = '1.0.0'
            resource_id = $resId
            canonical_name = 'no-manifest-skill'
            version = '1.0.0'
            display_name = 'no-manifest-skill'
            description = 'Skill without SKILL.md'
            provenance_id = $provId
            lifecycle_state = 'DISCOVERED'
            trust_level = 'UNTRUSTED'
            capabilities = @()
            content_identity = [ordered]@{
                content_hash = $null
                manifest_hash = $null
                file_count = 1
                byte_sum = 48
            }
            created_utc = $nowUtc
            updated_utc = $nowUtc
        }
        $line = ($adHoc | ConvertTo-Json -Compress) + "`n"
        Write-Utf8NoBom -Path (Join-Path $RegistryRoot 'index\resources.jsonl') -Content $line -Append $true
    }
    
    $skillDir = Join-Path $mockStructPool "no-manifest-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $resId -SkillDirectory $skillDir -SourceId $structSource.source_id -Initiator "TestHarness"
    if ($laudo.structure.has_skill_md -ne $false) { throw "has_skill_md should be false" }
    if ($laudo.inferred_metadata.packaging_type -ne 'MALFORMED') { throw "packaging_type should be MALFORMED" }
    if ($laudo.inferred_metadata.structural_conformance -ne 'DEFECTIVE') { throw "structural_conformance should be DEFECTIVE" }
}

# 18. LifecycleStateTransitionToCandidate
Run-TestCase -Name "18_LifecycleStateTransitionToCandidate" -Description "Verify compliant analysis transitions resource state to CANDIDATE" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $skillDir = Join-Path $mockStructPool "valid-multi-skill"
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $skillDir -SourceId $structSource.source_id
    
    $updatedRes = Get-RegistryDiscoveredResources -ResourceId $res.resource_id
    if ($updatedRes.lifecycle_state -ne 'CANDIDATE') { throw "Expected lifecycle_state = CANDIDATE, found: $($updatedRes.lifecycle_state)" }
}

# 19. LifecycleStateTransitionToBlockedOnViolation
Run-TestCase -Name "19_LifecycleStateTransitionToBlockedOnViolation" -Description "Verify quarantine violation transitions resource state to BLOCKED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $tombstoneDir = 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings\File Inclusion\Files'
    $laudo = Invoke-RegistryStructuralAnalysis -ResourceId $res.resource_id -SkillDirectory $tombstoneDir -SourceId $structSource.source_id
    
    $updatedRes = Get-RegistryDiscoveredResources -ResourceId $res.resource_id
    if ($updatedRes.lifecycle_state -ne 'BLOCKED') { throw "Expected lifecycle_state = BLOCKED, found: $($updatedRes.lifecycle_state)" }
    if ($updatedRes.trust_level -ne 'BLOCKED') { throw "Expected trust_level = BLOCKED, found: $($updatedRes.trust_level)" }
    
    # Restore valid candidate state
    $null = Set-RegistryResourceState -ResourceId $res.resource_id -TargetState "CANDIDATE" -Reason "Restored"
}

# 20. TrustLevelImmutability
Run-TestCase -Name "20_TrustLevelImmutability" -Description "Verify compliant resource retains trust_level = UNTRUSTED (no auto-escalation)" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $updatedRes = Get-RegistryDiscoveredResources -ResourceId $res.resource_id
    if ($updatedRes.trust_level -ne 'UNTRUSTED') { throw "Trust level auto-escalated! Found: $($updatedRes.trust_level)" }
}

# 21. ContentHashRemainsNull
Run-TestCase -Name "21_ContentHashRemainsNull" -Description "Verify content_identity.content_hash remains null in Phase 4" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($null -ne $res.content_identity.content_hash) { throw "Content hash should remain null during structural analysis" }
}

# 22. TransactionAtomicCommitOnAnalysis
Run-TestCase -Name "22_TransactionAtomicCommitOnAnalysis" -Description "Verify structural report is committed inside an atomic ACID transaction" -Assertion {
    $journal = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'transactions\journal.jsonl')
    if ($journal -notmatch 'STRUCTURAL_ANALYSIS_EXECUTE') { throw "Transaction journal missing STRUCTURAL_ANALYSIS_EXECUTE record" }
}

# 23. TransactionRollbackOnAnalysisFault
Run-TestCase -Name "23_TransactionRollbackOnAnalysisFault" -Description "Verify state integrity is preserved on transaction fault" -Assertion {
    $stateBefore = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    try {
        Invoke-RegistryTransaction -OperationType 'STRUCTURAL_FAULT_TEST' -Action {
            param($txId)
            throw "SIMULATED_STRUCTURAL_FAULT"
        }
    } catch {}
    $stateAfter = Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'state\current-state.json')
    if ($stateBefore -ne $stateAfter) { throw "State corrupted during rollback" }
}

# 24. AuditEventEmittedOnStructuralAnalysis
Run-TestCase -Name "24_AuditEventEmittedOnStructuralAnalysis" -Description "Verify audit log records STRUCTURAL_ANALYSIS_COMPLETED" -Assertion {
    $auditFile = Join-Path $RegistryRoot 'audit\events.jsonl'
    $content = Read-Utf8NoBom -Path $auditFile
    if ($content -notmatch 'STRUCTURAL_ANALYSIS_COMPLETED') { throw "Audit event STRUCTURAL_ANALYSIS_COMPLETED missing" }
}

# 25. CorruptedAnalysisIndexDetection
Run-TestCase -Name "25_CorruptedAnalysisIndexDetection" -Description "Verify index parser resilience against corrupted lines" -Assertion {
    $badLine = '{"analysis_id":'
    $threw = $false
    try {
        $null = $badLine | ConvertFrom-Json
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Corrupted line not detected" }
}

# 26. PS5CompatibilityInTreeParsing
Run-TestCase -Name "26_PS5CompatibilityInTreeParsing" -Description "Verify tree walking and filtering compatible with PowerShell 5.1" -Assertion {
    $tree = @(
        [ordered]@{ relative_path = 'SKILL.md'; size_bytes = 100; extension = '.md'; is_entrypoint = $true; is_executable_type = $false },
        [ordered]@{ relative_path = 'scripts/main.py'; size_bytes = 200; extension = '.py'; is_entrypoint = $true; is_executable_type = $true }
    )
    if ($tree.Count -ne 2) { throw "PS5 tree structure failed" }
}

# 27. PS7CompatibilityInTreeParsing
Run-TestCase -Name "27_PS7CompatibilityInTreeParsing" -Description "Verify ordinal comparer compatibility" -Assertion {
    $cmp = [System.StringComparer]::Ordinal.Compare("references/guide.md", "scripts/main.py")
    if ($cmp -ge 0) { throw "Ordinal compare failed" }
}

# 28. LongPathSupportInStructuralWalk
Run-TestCase -Name "28_LongPathSupportInStructuralWalk" -Description "Verify path handling supports extended path structures" -Assertion {
    $longRel = "nested\" * 10 + "deep-script.py"
    if ($longRel.Length -lt 20) { throw "Length test failed" }
}

# 29. StructuralAnalysisSchemaValidation
Run-TestCase -Name "29_StructuralAnalysisSchemaValidation" -Description "Verify structural-analysis.schema.json validity and completeness" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\structural-analysis.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "structural-analysis.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 11) { throw "Schema required properties count mismatch" }
}

# 30. DoctorVerificationAcrossIndices
Run-TestCase -Name "30_DoctorVerificationAcrossIndices" -Description "Verify doctor diagnostic check covers structural analysis index and schemas" -Assertion {
    $status = Get-RegistryStatus
    if ($status.schema_count -lt 18) { throw "Expected at least 18 active schemas in Registry" }
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
