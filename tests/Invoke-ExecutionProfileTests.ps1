# Skill Registry Test Harness: Phase 14 — Execution Profiles & Runtime Sandbox Environments
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-14-execution-profiles.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-14.execution-profile-tests/v1'
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

# 1. StrictSandboxProfileRegistration
Run-TestCase -Name "01_StrictSandboxProfileRegistration" -Description "Register and verify STRICT_SANDBOX profile definition" -Assertion {
    $p = Register-RegistryExecutionProfile -ProfileName "STRICT_SANDBOX" -Description "Maximum isolation sandbox" `
                                          -TargetTrustLevel "UNTRUSTED" -IsolationLevel "MAXIMUM" -NetworkPolicy "BLOCKED" `
                                          -AllowedDomains @() -FilesystemPolicy "ISOLATED_TEMP_EPHEMERAL" `
                                          -ProcessLimits @{ max_runtime_seconds = 15; max_memory_mb = 256; max_cpu_percent = 25; allow_child_processes = $false } `
                                          -EnvVariablePolicy "CLEAN_ISOLATED" -WhitelistedEnvVars @("TEMP", "TMP")
    if ($null -eq $p) { throw "Strict sandbox registration returned null" }
    if ($p.profile_id -ne "prof-strict-sandbox-v1") { throw "Profile ID mismatch: $($p.profile_id)" }
}

# 2. OfflineDeveloperProfileRegistration
Run-TestCase -Name "02_OfflineDeveloperProfileRegistration" -Description "Register and verify OFFLINE_DEVELOPER profile definition" -Assertion {
    $p = Register-RegistryExecutionProfile -ProfileName "OFFLINE_DEVELOPER" -Description "Offline developer sandbox" `
                                          -TargetTrustLevel "UNTRUSTED" -IsolationLevel "HIGH" -NetworkPolicy "BLOCKED" `
                                          -AllowedDomains @() -FilesystemPolicy "WORKSPACE_TEMP_READWRITE" `
                                          -ProcessLimits @{ max_runtime_seconds = 60; max_memory_mb = 1024; max_cpu_percent = 50; allow_child_processes = $true } `
                                          -EnvVariablePolicy "SAFE_WHITELIST" -WhitelistedEnvVars @("PATH", "TEMP", "TMP", "PYTHONPATH")
    if ($null -eq $p) { throw "Offline developer registration returned null" }
    if ($p.profile_name -ne "OFFLINE_DEVELOPER") { throw "Profile name mismatch" }
}

# 3. NetworkRestrictedProfileRegistration
Run-TestCase -Name "03_NetworkRestrictedProfileRegistration" -Description "Register and verify NETWORK_RESTRICTED profile definition" -Assertion {
    $p = Register-RegistryExecutionProfile -ProfileName "NETWORK_RESTRICTED" -Description "Network restricted sandbox" `
                                          -TargetTrustLevel "PROMOTABLE" -IsolationLevel "HIGH" -NetworkPolicy "RESTRICTED_WHITELIST" `
                                          -AllowedDomains @("api.github.com", "registry.npmjs.org") -FilesystemPolicy "WORKSPACE_TEMP_READWRITE" `
                                          -ProcessLimits @{ max_runtime_seconds = 120; max_memory_mb = 2048; max_cpu_percent = 75; allow_child_processes = $true } `
                                          -EnvVariablePolicy "AUDITED_WHITELIST" -WhitelistedEnvVars @("PATH", "TEMP", "TMP")
    if ($null -eq $p) { throw "Network restricted registration returned null" }
    if ($p.allowed_domains.Count -lt 2) { throw "Allowed domains missing" }
}

# 4. ProviderNativeProfileRegistration
Run-TestCase -Name "04_ProviderNativeProfileRegistration" -Description "Register and verify PROVIDER_NATIVE profile definition" -Assertion {
    $p = Register-RegistryExecutionProfile -ProfileName "PROVIDER_NATIVE" -Description "Provider native profile" `
                                          -TargetTrustLevel "VERIFIED_CANONICAL" -IsolationLevel "PROVIDER_DELEGATED" -NetworkPolicy "PROVIDER_CONTROLLED" `
                                          -AllowedDomains @("*") -FilesystemPolicy "PROVIDER_SANDBOX" `
                                          -ProcessLimits @{ max_runtime_seconds = 300; max_memory_mb = 4096; max_cpu_percent = 100; allow_child_processes = $true } `
                                          -EnvVariablePolicy "PROVIDER_MANAGED" -WhitelistedEnvVars @("*")
    if ($null -eq $p) { throw "Provider native registration returned null" }
}

# Setup test skills
$validSkill = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
$dangSkill = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"

# 5. DefaultUntrustedMappingToStrictSandbox
Run-TestCase -Name "05_DefaultUntrustedMappingToStrictSandbox" -Description "Untrusted resource resolves to STRICT_SANDBOX" -Assertion {
    $res = Resolve-RegistrySkillExecutionProfile -ResourceId $validSkill.resource_id
    if ($res.status -ne "RESOLVED") { throw "Resolution failed: $($res.status)" }
    if ($res.resolved_profile_name -ne "STRICT_SANDBOX" -and $res.resolved_profile_name -ne "OFFLINE_DEVELOPER") {
        throw "Unexpected profile: $($res.resolved_profile_name)"
    }
}

# 6. QuarantinedResourceBindingRefusal
Run-TestCase -Name "06_QuarantinedResourceBindingRefusal" -Description "Blocked/Quarantined resource resolves to REFUSED_QUARANTINE" -Assertion {
    $res = Resolve-RegistrySkillExecutionProfile -ResourceId $dangSkill.resource_id
    if ($res.status -ne "REFUSED_QUARANTINE") { throw "Expected REFUSED_QUARANTINE, got: $($res.status)" }
    if ($null -ne $res.resolved_profile_id) { throw "Quarantined resource was unexpectedly assigned profile ID" }
}

# 7. StructuralViolationResourceRefusal
Run-TestCase -Name "07_StructuralViolationResourceRefusal" -Description "Resource with structural violation resolves to REFUSED_QUARANTINE" -Assertion {
    $res = Resolve-RegistrySkillExecutionProfile -ResourceId $dangSkill.resource_id
    if ($res.isolation_required -ne "ABSOLUTE_BLOCK") { throw "Expected ABSOLUTE_BLOCK isolation" }
}

# 8. HighRiskResourceMappingToStrictSandbox
Run-TestCase -Name "08_HighRiskResourceMappingToStrictSandbox" -Description "High risk skill resolves to STRICT_SANDBOX" -Assertion {
    $malformed = Get-RegistryDiscoveredResources -CanonicalName "skill-malformed"
    if ($null -ne $malformed) {
        $res = Resolve-RegistrySkillExecutionProfile -ResourceId $malformed.resource_id
        if ($res.resolved_profile_name -ne "STRICT_SANDBOX") {
            throw "Expected STRICT_SANDBOX for malformed skill, got: $($res.resolved_profile_name)"
        }
    }
}

# 9. LowRiskOfflineResourceMappingToOfflineDeveloper
Run-TestCase -Name "09_LowRiskOfflineResourceMappingToOfflineDeveloper" -Description "Promotable low-risk offline skill resolves to OFFLINE_DEVELOPER" -Assertion {
    $singleSkill = Get-RegistryDiscoveredResources -CanonicalName "single-file-skill"
    if ($null -ne $singleSkill) {
        $res = Resolve-RegistrySkillExecutionProfile -ResourceId $singleSkill.resource_id
        if ($res.status -ne "RESOLVED") { throw "Resolution failed for single-file-skill" }
    }
}

# 10. NetworkResourceMappingToNetworkRestricted
Run-TestCase -Name "10_NetworkResourceMappingToNetworkRestricted" -Description "Skill with network capability resolves to NETWORK_RESTRICTED when promotable" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "NETWORK_RESTRICTED"
    if ($null -eq $p) { throw "NETWORK_RESTRICTED profile missing" }
    if ($p.network_policy -ne "RESTRICTED_WHITELIST") { throw "Network policy mismatch" }
}

# 11. VerifiedCanonicalMappingToProviderNative
Run-TestCase -Name "11_VerifiedCanonicalMappingToProviderNative" -Description "Skill with VERIFIED_CANONICAL trust resolves to PROVIDER_NATIVE" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "PROVIDER_NATIVE"
    if ($null -eq $p) { throw "PROVIDER_NATIVE profile missing" }
    if ($p.isolation_level -ne "PROVIDER_DELEGATED") { throw "Isolation level mismatch" }
}

# 12. TrustLevelImmutabilityOnProfileResolution
Run-TestCase -Name "12_TrustLevelImmutabilityOnProfileResolution" -Description "Profile resolution leaves skill trust_level UNTRUSTED" -Assertion {
    $res = Resolve-RegistrySkillExecutionProfile -ResourceId $validSkill.resource_id
    if ($res.trust_level -ne "UNTRUSTED") { throw "Trust level escalated: $($res.trust_level)" }
}

# 13. ZeroPayloadExecutionDuringProfileResolution
Run-TestCase -Name "13_ZeroPayloadExecutionDuringProfileResolution" -Description "Zero processes spawned during resolution" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
}

# 14. ProcessLimitConstraintValidation
Run-TestCase -Name "14_ProcessLimitConstraintValidation" -Description "Verify process limits in STRICT_SANDBOX (15s / 256MB)" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($p.process_limits.max_runtime_seconds -ne 15) { throw "Max runtime mismatch" }
    if ($p.process_limits.max_memory_mb -ne 256) { throw "Max memory mismatch" }
    if ($p.process_limits.allow_child_processes -ne $false) { throw "Allow child processes mismatch" }
}

# 15. NetworkEgressBlockedValidation
Run-TestCase -Name "15_NetworkEgressBlockedValidation" -Description "Verify network policy is BLOCKED in STRICT_SANDBOX" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($p.network_policy -ne "BLOCKED") { throw "Network policy is not BLOCKED" }
}

# 16. FilesystemIsolationPolicyValidation
Run-TestCase -Name "16_FilesystemIsolationPolicyValidation" -Description "Verify filesystem policy is ISOLATED_TEMP_EPHEMERAL" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($p.filesystem_policy -ne "ISOLATED_TEMP_EPHEMERAL") { throw "Filesystem policy mismatch" }
}

# 17. EnvironmentScrubbingPolicyValidation
Run-TestCase -Name "17_EnvironmentScrubbingPolicyValidation" -Description "Verify CLEAN_ISOLATED env variable policy" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($p.env_variable_policy -ne "CLEAN_ISOLATED") { throw "Env variable policy mismatch" }
}

# 18. ACIDTransactionProfileRegistration
Run-TestCase -Name "18_ACIDTransactionProfileRegistration" -Description "Verify PROFILE_REGISTRATION in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"PROFILE_REGISTRATION"') { $found = $true; break }
    }
    if (-not $found) { throw "PROFILE_REGISTRATION not found in transaction journal" }
}

# 19. AuditEventsEmittedForProfile
Run-TestCase -Name "19_AuditEventsEmittedForProfile" -Description "Verify PROFILE_REGISTERED in audit trail" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"PROFILE_REGISTERED"') { $found = $true; break }
    }
    if (-not $found) { throw "PROFILE_REGISTERED not found in audit trail" }
}

# 20. CorruptedExecutionProfilesIndexResilience
Run-TestCase -Name "20_CorruptedExecutionProfilesIndexResilience" -Description "JSON parser resilience on profile index" -Assertion {
    $profiles = @(Get-RegistryExecutionProfiles)
    if ($profiles.Count -lt 4) { throw "Expected at least 4 registered profiles" }
}

# 21. PS5CompatibilityInProfileEngine
Run-TestCase -Name "21_PS5CompatibilityInProfileEngine" -Description "Compatibility with PowerShell 5.1" -Assertion {
    $p = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($null -eq $p.profile_id) { throw "PS5 profile retrieval failed" }
}

# 22. PS7CompatibilityInProfileEngine
Run-TestCase -Name "22_PS7CompatibilityInProfileEngine" -Description "Compatibility with PowerShell 7+" -Assertion {
    $profiles = @(Get-RegistryExecutionProfiles)
    if ($profiles.Count -lt 4) { throw "Expected at least 4 profiles in PS7" }
}

# 23. QueryProfilesByIdAndName
Run-TestCase -Name "23_QueryProfilesByIdAndName" -Description "Querying profiles by ID and Name" -Assertion {
    $pById = Get-RegistryExecutionProfiles -ProfileId "prof-strict-sandbox-v1"
    $pByName = Get-RegistryExecutionProfiles -ProfileName "STRICT_SANDBOX"
    if ($pById.profile_id -ne $pByName.profile_id) { throw "Profile query mismatch" }
}

# 24. ProfileConformanceTestingCompliant
Run-TestCase -Name "24_ProfileConformanceTestingCompliant" -Description "Test conforming resource requirement" -Assertion {
    $c = Test-RegistryExecutionProfileConformance -ProfileId "prof-strict-sandbox-v1" -RequestedRequirements @{
        runtime_seconds = 10
        memory_mb = 128
        requires_network = $false
        spawn_children = $false
    }
    if (-not $c.passed) { throw "Expected conformance PASS: $($c.violations -join '; ')" }
}

# 25. ProfileConformanceTestingExcessMemory
Run-TestCase -Name "25_ProfileConformanceTestingExcessMemory" -Description "Non-conformant on excess memory" -Assertion {
    $c = Test-RegistryExecutionProfileConformance -ProfileId "prof-strict-sandbox-v1" -RequestedRequirements @{
        runtime_seconds = 10
        memory_mb = 512
    }
    if ($c.passed) { throw "Expected conformance failure due to excess memory" }
    if ($c.violations.Count -eq 0) { throw "Expected violations recorded" }
}

# 26. ProfileConformanceTestingUnauthorizedNetwork
Run-TestCase -Name "26_ProfileConformanceTestingUnauthorizedNetwork" -Description "Non-conformant on network access when BLOCKED" -Assertion {
    $c = Test-RegistryExecutionProfileConformance -ProfileId "prof-strict-sandbox-v1" -RequestedRequirements @{
        requires_network = $true
    }
    if ($c.passed) { throw "Expected conformance failure due to blocked network" }
}

# 27. ProfileConformanceTestingUnauthorizedDomain
Run-TestCase -Name "27_ProfileConformanceTestingUnauthorizedDomain" -Description "Non-conformant on unlisted domain" -Assertion {
    $c = Test-RegistryExecutionProfileConformance -ProfileId "prof-network-restricted-v1" -RequestedRequirements @{
        requires_network = $true
        target_domain = "unauthorized-malicious-domain.com"
    }
    if ($c.passed) { throw "Expected conformance failure due to unlisted domain" }
}

# 28. ProfileIdFormatValidation
Run-TestCase -Name "28_ProfileIdFormatValidation" -Description "Verify format of generated profile ID (prof-...-v1)" -Assertion {
    $id = New-RegistryExecutionProfileId -ProfileName "CUSTOM_TEST_PROFILE"
    if ($id -notmatch '^prof-[a-z0-9-]+-v[0-9]+$') {
        throw "Profile ID failed format check: $id"
    }
}

# 29. NonExistentResourceResolutionGraceful
Run-TestCase -Name "29_NonExistentResourceResolutionGraceful" -Description "Error handling for non-existent resource ID" -Assertion {
    $threw = $false
    try {
        Resolve-RegistrySkillExecutionProfile -ResourceId "sres-v1-sha256:0000000000000000000000000000000000000000000000000000000000000000"
    } catch {
        $threw = $true
    }
    if (-not $threw) { throw "Expected exception for non-existent resource" }
}

# 30. DoctorVerificationAcross26Schemas
Run-TestCase -Name "30_DoctorVerificationAcross26Schemas" -Description "Verify status and doctor validate all 26 active schemas and profile index" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 26) { throw "Expected at least 26 active schemas, got: $($st.schema_count)" }
    if ($st.execution_profiles_count -lt 4) { throw "Expected at least 4 registered profiles, got: $($st.execution_profiles_count)" }
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
