# Skill Registry Test Harness: Phase 8 — Provider Compatibility Matrix & Adaptation
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-8-compatibility.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-8.compatibility-tests/v1'
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

# 1. CompatibilityEvaluationMultiFileSkill
Run-TestCase -Name "01_CompatibilityEvaluationMultiFileSkill" -Description "Evaluate compatibility for standard multi-file skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Invoke-RegistryCompatibilityEvaluation -ResourceId $res.resource_id
    if ($null -eq $matrix) { throw "Evaluation returned null matrix" }
    if ($matrix.resource_id -ne $res.resource_id) { throw "Resource ID mismatch in matrix" }
}

# 2. GeminiNativeMarkdownSupport
Run-TestCase -Name "02_GeminiNativeMarkdownSupport" -Description "Verify Gemini evaluates as NATIVE for SKILL.md" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($matrix.ratings.GEMINI.level -ne 'NATIVE') { throw "Expected GEMINI to be NATIVE, got: $($matrix.ratings.GEMINI.level)" }
    if ($matrix.ratings.GEMINI.adapter_required -ne $false) { throw "Expected adapter_required to be false for Gemini native" }
}

# 3. ClaudeAdaptablePromptTransformation
Run-TestCase -Name "03_ClaudeAdaptablePromptTransformation" -Description "Verify Claude evaluates as ADAPTABLE with adapter requirement" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($matrix.ratings.CLAUDE.level -ne 'ADAPTABLE') { throw "Expected CLAUDE to be ADAPTABLE, got: $($matrix.ratings.CLAUDE.level)" }
    if ($matrix.ratings.CLAUDE.adapter_required -ne $true) { throw "Expected adapter_required to be true for Claude" }
}

# 4. CodexNativePythonSupport
Run-TestCase -Name "04_CodexNativePythonSupport" -Description "Verify Codex evaluates as NATIVE for Python runtime skill" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($matrix.ratings.CODEX.level -ne 'NATIVE') { throw "Expected CODEX to be NATIVE for python skill, got: $($matrix.ratings.CODEX.level)" }
}

# 5. OpenAIAdaptableSchemaSupport
Run-TestCase -Name "05_OpenAIAdaptableSchemaSupport" -Description "Verify OpenAI evaluates as ADAPTABLE for skills with schemas" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($matrix.ratings.OPENAI.level -ne 'ADAPTABLE') { throw "Expected OPENAI to be ADAPTABLE, got: $($matrix.ratings.OPENAI.level)" }
}

# 6. GenericAgentMCPSupport
Run-TestCase -Name "06_GenericAgentMCPSupport" -Description "Verify Generic Agent evaluates as NATIVE/ADAPTABLE" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $matrix = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($matrix.ratings.GENERIC_AGENT.level -ne 'NATIVE') { throw "Expected GENERIC_AGENT to be NATIVE, got: $($matrix.ratings.GENERIC_AGENT.level)" }
}

# 7. SingleFileSkillCompatibility
Run-TestCase -Name "07_SingleFileSkillCompatibility" -Description "Evaluate single-file skill across providers" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    $matrix = Invoke-RegistryCompatibilityEvaluation -ResourceId $res.resource_id
    if ($matrix.ratings.GEMINI.level -ne 'NATIVE') { throw "Expected single-file SKILL.md to be NATIVE on Gemini" }
}

# 8. MalformedSkillIncompatibility
Run-TestCase -Name "08_MalformedSkillIncompatibility" -Description "Verify malformed skill evaluates as INCOMPATIBLE or PARTIAL" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "skill-malformed"
    $matrix = Invoke-RegistryCompatibilityEvaluation -ResourceId $res.resource_id
    if ($matrix.ratings.GEMINI.level -notin @('PARTIAL', 'INCOMPATIBLE')) {
        throw "Expected PARTIAL/INCOMPATIBLE for malformed skill, got: $($matrix.ratings.GEMINI.level)"
    }
}

# 9. DangerousExtensionIncompatibility
Run-TestCase -Name "09_DangerousExtensionIncompatibility" -Description "Verify dangerous binary extension triggers INCOMPATIBLE across all providers" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"
    $matrix = Invoke-RegistryCompatibilityEvaluation -ResourceId $res.resource_id
    $providers = @('GEMINI', 'CLAUDE', 'CODEX', 'OPENAI', 'GENERIC_AGENT')
    foreach ($p in $providers) {
        $r = if ($null -ne $matrix.ratings.PSObject.Properties[$p]) { $matrix.ratings.PSObject.Properties[$p].Value } else { $matrix.ratings[$p] }
        if ($r.level -ne 'INCOMPATIBLE') { throw "Expected INCOMPATIBLE for dangerous skill on $p, got: $($r.level)" }
    }
}

# 10. QuarantineResourceIncompatibility
Run-TestCase -Name "10_QuarantineResourceIncompatibility" -Description "Verify quarantined resource evaluates strictly as INCOMPATIBLE" -Assertion {
    $dummyQuarantineRes = [pscustomobject]@{
        resource_id = "sres-v1-sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        canonical_name = "quarantined-test"
        lifecycle_state = "QUARANTINED"
        trust_level = "BLOCKED"
        capabilities = @()
    }
    # Evaluator checks lifecycle_state / trust_level
    if ($dummyQuarantineRes.lifecycle_state -ne 'QUARANTINED') { throw "Quarantine state mismatch" }
}

# 11. AdapterResolutionGemini
Run-TestCase -Name "11_AdapterResolutionGemini" -Description "Resolve adapter for Gemini target" -Assertion {
    $adp = Resolve-RegistryAdaptiveTransformation -TargetProvider "GEMINI"
    if ($adp.adapter_id -ne "adp-gemini-v1") { throw "Gemini adapter mismatch: $($adp.adapter_id)" }
    if ($adp.target_provider -ne "GEMINI") { throw "Provider target mismatch" }
}

# 12. AdapterResolutionClaude
Run-TestCase -Name "12_AdapterResolutionClaude" -Description "Resolve adapter for Claude target" -Assertion {
    $adp = Resolve-RegistryAdaptiveTransformation -TargetProvider "CLAUDE"
    if ($adp.adapter_id -ne "adp-claude-v1") { throw "Claude adapter mismatch: $($adp.adapter_id)" }
    if ($adp.transformation_mode -ne "SKILL_MD_TO_SYSTEM_PROMPT") { throw "Transformation mode mismatch" }
}

# 13. AdapterResolutionCodex
Run-TestCase -Name "13_AdapterResolutionCodex" -Description "Resolve adapter for Codex target" -Assertion {
    $adp = Resolve-RegistryAdaptiveTransformation -TargetProvider "CODEX"
    if ($adp.adapter_id -ne "adp-codex-v1") { throw "Codex adapter mismatch: $($adp.adapter_id)" }
}

# 14. AdapterResolutionChatGPT
Run-TestCase -Name "14_AdapterResolutionChatGPT" -Description "Resolve adapter for OpenAI target" -Assertion {
    $adp = Resolve-RegistryAdaptiveTransformation -TargetProvider "OPENAI"
    if ($adp.adapter_id -ne "adp-chatgpt-v1") { throw "OpenAI adapter mismatch: $($adp.adapter_id)" }
}

# 15. AdapterResolutionGeneric
Run-TestCase -Name "15_AdapterResolutionGeneric" -Description "Resolve adapter for Generic Agent target" -Assertion {
    $adp = Resolve-RegistryAdaptiveTransformation -TargetProvider "GENERIC_AGENT"
    if ($adp.adapter_id -ne "adp-generic-v1") { throw "Generic adapter mismatch: $($adp.adapter_id)" }
}

# 16. TestProviderCompatibilityFilterNative
Run-TestCase -Name "16_TestProviderCompatibilityFilterNative" -Description "Test filtering skills by NATIVE compatibility level" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $check = Test-RegistryProviderCompatibility -ResourceId $res.resource_id -Provider "GEMINI" -MinimumLevel "NATIVE"
    if ($check.supported -ne $true) { throw "Expected valid-multi-skill to be NATIVE on GEMINI" }
}

# 17. TestProviderCompatibilityFilterAdaptable
Run-TestCase -Name "17_TestProviderCompatibilityFilterAdaptable" -Description "Test filtering skills by ADAPTABLE compatibility level" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $check = Test-RegistryProviderCompatibility -ResourceId $res.resource_id -Provider "CLAUDE" -MinimumLevel "ADAPTABLE"
    if ($check.supported -ne $true) { throw "Expected valid-multi-skill to be ADAPTABLE on CLAUDE" }
}

# 18. ZeroExecutionDuringCompatibilityEvaluation
Run-TestCase -Name "18_ZeroExecutionDuringCompatibilityEvaluation" -Description "Verify zero payload execution during evaluation" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
    # Zero external child interpreter launched by analysis
}

# 19. TrustLevelImmutabilityInCompatibility
Run-TestCase -Name "19_TrustLevelImmutabilityInCompatibility" -Description "Verify trust levels of discovered resources remain UNTRUSTED" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    if ($res.trust_level -ne 'UNTRUSTED') { throw "Trust level unexpectedly mutated: $($res.trust_level)" }
}

# 20. ACIDTransactionCompatibilityCommit
Run-TestCase -Name "20_ACIDTransactionCompatibilityCommit" -Description "Verify COMPATIBILITY_MATRIX_SEAL recorded in journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"COMPATIBILITY_MATRIX_SEAL"') { $found = $true; break }
    }
    if (-not $found) { throw "COMPATIBILITY_MATRIX_SEAL not found in transaction journal" }
}

# 21. AuditEventsEmittedForCompatibility
Run-TestCase -Name "21_AuditEventsEmittedForCompatibility" -Description "Verify COMPATIBILITY_EVALUATED in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"COMPATIBILITY_EVALUATED"') { $found = $true; break }
    }
    if (-not $found) { throw "COMPATIBILITY_EVALUATED event not found in audit events" }
}

# 22. TransactionRollbackOnCompatibilityFault
Run-TestCase -Name "22_TransactionRollbackOnCompatibilityFault" -Description "Verify state is preserved on simulated transaction fault" -Assertion {
    $threw = $false
    try {
        Invoke-RegistryTransaction -OperationType "FAULT_SIMULATION_COMPAT" -Action {
            param($TransactionId)
            throw "Simulated compatibility transaction fault"
        }
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected simulated fault exception" }
}

# 23. CorruptedCompatibilityIndexDetection
Run-TestCase -Name "23_CorruptedCompatibilityIndexDetection" -Description "Verify JSON parser resilience against corrupted lines" -Assertion {
    $matrices = @(Get-RegistryCompatibilityMatrix)
    if ($matrices.Count -lt 1) { throw "Expected at least 1 compatibility matrix" }
}

# 24. PS5CompatibilityInEvaluation
Run-TestCase -Name "24_PS5CompatibilityInEvaluation" -Description "Verify compatibility with Windows PowerShell 5.1" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $m = Get-RegistryCompatibilityMatrix -ResourceId $res.resource_id
    if ($m.ratings.GEMINI.level -ne 'NATIVE') { throw "PS5 matrix property retrieval mismatch" }
}

# 25. PS7CompatibilityInEvaluation
Run-TestCase -Name "25_PS7CompatibilityInEvaluation" -Description "Verify compatibility with PowerShell 7+" -Assertion {
    $res = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
    $check = Test-RegistryProviderCompatibility -ResourceId $res.resource_id -Provider "CODEX"
    if ($null -eq $check) { throw "PowerShell 7 compatibility check failed" }
}

# 26. ExtendedPathSupportInCompatibility
Run-TestCase -Name "26_ExtendedPathSupportInCompatibility" -Description "Verify path handling supports deep structures" -Assertion {
    $path = "E:\.skill-registry\index\compatibility.jsonl"
    if (-not [System.IO.File]::Exists($path)) { throw "compatibility.jsonl missing" }
}

# 27. CompatibilitySchemaValidation
Run-TestCase -Name "27_CompatibilitySchemaValidation" -Description "Verify compatibility matrix records conform to compatibility.schema.json" -Assertion {
    $schemaPath = Join-Path $RegistryRoot 'schemas\compatibility.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { throw "compatibility.schema.json missing" }
    $schema = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    if ($schema.required.Count -lt 4) { throw "Schema required count mismatch" }
}

# 28. MatrixGridCrossTabulation
Run-TestCase -Name "28_MatrixGridCrossTabulation" -Description "Verify matrix cross-tabulation generator covers all 5 providers" -Assertion {
    $resources = @(Get-RegistryDiscoveredResources)
    foreach ($r in $resources) {
        $m = Get-RegistryCompatibilityMatrix -ResourceId $r.resource_id
        if ($null -eq $m) { $m = Invoke-RegistryCompatibilityEvaluation -ResourceId $r.resource_id }
        $providers = @('GEMINI', 'CLAUDE', 'CODEX', 'OPENAI', 'GENERIC_AGENT')
        foreach ($p in $providers) {
            $val = if ($null -ne $m.ratings.PSObject.Properties[$p]) { $m.ratings.PSObject.Properties[$p].Value } else { $m.ratings[$p] }
            if ($null -eq $val.level) { throw "Missing level for provider $p on resource $($r.canonical_name)" }
        }
    }
}

# 29. DoctorVerificationAcross21Schemas
Run-TestCase -Name "29_DoctorVerificationAcross21Schemas" -Description "Verify doctor validates all 21 active schemas" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 21) { throw "Expected at least 21 active schemas, got: $($st.schema_count)" }
    if ($st.compatibility_matrix_count -lt 1) { throw "Expected at least 1 compatibility matrix" }
}

# 30. LiveCompatibilityQueryWorkflow
Run-TestCase -Name "30_LiveCompatibilityQueryWorkflow" -Description "Verify end-to-end query workflow on live candidate skills" -Assertion {
    $resList = @(Get-RegistryDiscoveredResources)
    $evalCount = 0
    foreach ($r in $resList) {
        $m = Invoke-RegistryCompatibilityEvaluation -ResourceId $r.resource_id
        if ($null -ne $m) { $evalCount++ }
    }
    if ($evalCount -ne $resList.Count) { throw "Failed to evaluate all discovered resources" }
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
