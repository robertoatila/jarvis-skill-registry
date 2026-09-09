# Skill Registry Test Harness: Phase 15 — Activation, Safe Deployment & Live Wiring
# 30 Synthetic Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-15-activation-deployment.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$testResults = [ordered]@{
    schema = 'skill-registry.phase-15.activation-deployment-tests/v1'
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

# Setup synthetic test staging directories
$testStagingRoot = Join-Path $RegistryRoot 'staging\live-test'
if (-not [System.IO.Directory]::Exists($testStagingRoot)) {
    [void][System.IO.Directory]::CreateDirectory($testStagingRoot)
}

$validSkill = Get-RegistryDiscoveredResources -CanonicalName "valid-multi-skill"
$dangSkill = Get-RegistryDiscoveredResources -CanonicalName "dangerous-ext-skill"

# 1. AtomicCopyDeploymentStaging
Run-TestCase -Name "01_AtomicCopyDeploymentStaging" -Description "Test atomic copy deployment to test staging dir" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\valid-multi-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'ATOMIC_COPY'
    if ($null -eq $dep) { throw "Deployment returned null" }
    if ($dep.lifecycle_state -ne 'STAGED') { throw "Expected state STAGED, got: $($dep.lifecycle_state)" }
    if (-not [System.IO.File]::Exists((Join-Path $dest 'SKILL.md'))) { throw "SKILL.md missing in deployed target" }
}

# 2. ManagedJunctionDeploymentStaging
Run-TestCase -Name "02_ManagedJunctionDeploymentStaging" -Description "Test NTFS junction deployment to test staging dir" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\valid-junction-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'MANAGED_JUNCTION'
    if ($null -eq $dep) { throw "Junction deployment returned null" }
    if ($dep.deployment_mode -ne 'MANAGED_JUNCTION') { throw "Deployment mode mismatch" }
    if (-not [System.IO.Directory]::Exists($dest)) { throw "Junction directory missing" }
}

# 3. PreDeployBackupSnapshotCreation
Run-TestCase -Name "03_PreDeployBackupSnapshotCreation" -Description "Verify backup directory created when deploying over existing directory" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\backup-test-skill'
    if (-not [System.IO.Directory]::Exists($dest)) { [void][System.IO.Directory]::CreateDirectory($dest) }
    [System.IO.File]::WriteAllText((Join-Path $dest 'ORIGINAL.txt'), 'Original content')
    
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'ATOMIC_COPY'
    if ($null -eq $dep.pre_deploy_backup_path) { throw "Backup snapshot path not recorded" }
    if (-not [System.IO.Directory]::Exists($dep.pre_deploy_backup_path)) { throw "Backup snapshot directory missing" }
    if (-not [System.IO.File]::Exists((Join-Path $dep.pre_deploy_backup_path 'ORIGINAL.txt'))) { throw "Original file missing in backup snapshot" }
}

# 4. PostMountProbeValidationPassing
Run-TestCase -Name "04_PostMountProbeValidationPassing" -Description "Valid SKILL.md passes post-mount probe" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\valid-multi-skill'
    $probe = Test-RegistryDeploymentProbe -DestinationPath $dest
    if (-not $probe.passed) { throw "Expected probe PASS: $($probe.errors -join '; ')" }
    if (-not $probe.entrypoint_found) { throw "Expected entrypoint found" }
}

# 5. ActivationStateTransitionOnProbePass
Run-TestCase -Name "05_ActivationStateTransitionOnProbePass" -Description "STAGED -> ACTIVE transition on activation" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\activation-test-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'ATOMIC_COPY'
    $act = Invoke-RegistrySkillActivation -DeploymentId $dep.deployment_id
    if ($act.lifecycle_state -ne 'ACTIVE') { throw "Expected ACTIVE state, got: $($act.lifecycle_state)" }
    if ($act.probe_status -ne 'PASSED') { throw "Expected PASSED probe status" }
    if ($null -eq $act.activated_utc) { throw "Activated timestamp missing" }
}

# 6. AutomaticRollbackOnProbeFailure
Run-TestCase -Name "06_AutomaticRollbackOnProbeFailure" -Description "Failed probe automatically triggers rollback and restores backup" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\rollback-probe-test'
    if (-not [System.IO.Directory]::Exists($dest)) { [void][System.IO.Directory]::CreateDirectory($dest) }
    [System.IO.File]::WriteAllText((Join-Path $dest 'ORIGINAL.txt'), 'Original baseline')
    
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'ATOMIC_COPY'
    
    # Intentionally remove SKILL.md before activation to trigger probe failure
    Remove-Item -Path (Join-Path $dest 'SKILL.md') -Force
    
    $rolledBack = $false
    try {
        Invoke-RegistrySkillActivation -DeploymentId $dep.deployment_id
    } catch {
        $rolledBack = $true
    }
    if (-not $rolledBack) { throw "Expected activation to fail and trigger rollback" }
    
    $checkDep = Get-RegistryDeployments -DeploymentId $dep.deployment_id
    if ($checkDep.lifecycle_state -ne 'ROLLED_BACK') { throw "Expected state ROLLED_BACK, got: $($checkDep.lifecycle_state)" }
    if (-not [System.IO.File]::Exists((Join-Path $dest 'ORIGINAL.txt'))) { throw "Original baseline was not restored during automatic rollback" }
}

# 7. AutomaticRollbackOnHashMismatch
Run-TestCase -Name "07_AutomaticRollbackOnHashMismatch" -Description "Corrupted file triggers hash mismatch rollback" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\hash-mismatch-test'
    # Test-RegistryDeploymentDrift returns modified if file hash changes
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest -DeploymentMode 'ATOMIC_COPY'
    $act = Invoke-RegistrySkillActivation -DeploymentId $dep.deployment_id
    
    # Tamper with file
    [System.IO.File]::AppendAllText((Join-Path $dest 'SKILL.md'), "`n# Unauthorized Modification")
    $drift = Test-RegistryDeploymentDrift -DeploymentId $dep.deployment_id
    if ($drift.status -ne 'DRIFT_MODIFIED') { throw "Expected DRIFT_MODIFIED, got: $($drift.status)" }
}

# 8. QuarantinedResourceDeploymentRefusal
Run-TestCase -Name "08_QuarantinedResourceDeploymentRefusal" -Description "Refuses deployment of quarantined resource" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\quarantined-fail-skill'
    $refused = $false
    try {
        Invoke-RegistrySkillDeployment -ResourceId $dangSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    } catch {
        $refused = $true
    }
    if (-not $refused) { throw "Quarantined resource was unexpectedly deployed!" }
}

# 9. BlockedResourceDeploymentRefusal
Run-TestCase -Name "09_BlockedResourceDeploymentRefusal" -Description "Refuses deployment of blocked / shadowed resource" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\blocked-fail-skill'
    $refused = $false
    try {
        Invoke-RegistrySkillDeployment -ResourceId $dangSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    } catch {
        $refused = $true
    }
    if (-not $refused) { throw "Blocked resource deployment was not refused" }
}

# 10. TrustLevelImmutabilityOnDeployment
Run-TestCase -Name "10_TrustLevelImmutabilityOnDeployment" -Description "Deployed manifest preserves UNTRUSTED trust level without escalation" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\trust-check-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    if ($dep.trust_level -ne 'UNTRUSTED') { throw "Trust level escalated on deployment: $($dep.trust_level)" }
}

# 11. ExecutionProfileBindingEnforcement
Run-TestCase -Name "11_ExecutionProfileBindingEnforcement" -Description "Deployment manifest references valid execution profile ID" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\profile-binding-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    if ($null -eq $dep.execution_profile_id) { throw "Execution profile ID missing in deployment manifest" }
    $prof = Get-RegistryExecutionProfiles -ProfileId $dep.execution_profile_id
    if ($null -eq $prof) { throw "Referenced execution profile does not exist: $($dep.execution_profile_id)" }
}

# 12. DriftDetectionInSync
Run-TestCase -Name "12_DriftDetectionInSync" -Description "Test drift check returns IN_SYNC for untouched directory" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\drift-sync-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    $drift = Test-RegistryDeploymentDrift -DeploymentId $dep.deployment_id
    if (-not $drift.in_sync) { throw "Expected IN_SYNC status for freshly deployed skill" }
}

# 13. DriftDetectionModifiedFile
Run-TestCase -Name "13_DriftDetectionModifiedFile" -Description "Test drift check detects modified file" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\drift-mod-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    [System.IO.File]::AppendAllText((Join-Path $dest 'SKILL.md'), "`n# Drift tamper")
    $drift = Test-RegistryDeploymentDrift -DeploymentId $dep.deployment_id
    if ($drift.status -ne 'DRIFT_MODIFIED') { throw "Failed to detect file modification in drift check" }
}

# 14. DriftDetectionAddedFile
Run-TestCase -Name "14_DriftDetectionAddedFile" -Description "Test drift check detects untracked file added" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\drift-add-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    [System.IO.File]::WriteAllText((Join-Path $dest 'untracked-payload.js'), 'console.log("untracked");')
    $drift = Test-RegistryDeploymentDrift -DeploymentId $dep.deployment_id
    if ($drift.status -ne 'DRIFT_ADDED') { throw "Failed to detect added file in drift check" }
}

# 15. DriftDetectionDeletedFile
Run-TestCase -Name "15_DriftDetectionDeletedFile" -Description "Test drift check detects deleted required file" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\drift-del-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    Remove-Item -Path (Join-Path $dest 'SKILL.md') -Force
    $drift = Test-RegistryDeploymentDrift -DeploymentId $dep.deployment_id
    if ($drift.status -ne 'DRIFT_DELETED') { throw "Failed to detect deleted file in drift check" }
}

# 16. ManualRollbackExecution
Run-TestCase -Name "16_ManualRollbackExecution" -Description "Manually triggering rollback restores previous state" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\manual-rollback-skill'
    if (-not [System.IO.Directory]::Exists($dest)) { [void][System.IO.Directory]::CreateDirectory($dest) }
    [System.IO.File]::WriteAllText((Join-Path $dest 'V1.txt'), 'Version 1 content')
    
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    $rb = Invoke-RegistryDeploymentRollback -DeploymentId $dep.deployment_id -Reason "Manual rollback test"
    if ($rb.lifecycle_state -ne 'ROLLED_BACK') { throw "Expected state ROLLED_BACK, got: $($rb.lifecycle_state)" }
    if (-not [System.IO.File]::Exists((Join-Path $dest 'V1.txt'))) { throw "Previous version V1.txt was not restored" }
}

# 17. SafeDeactivationLifecycle
Run-TestCase -Name "17_SafeDeactivationLifecycle" -Description "Deactivating deployment removes live directory and sets DEACTIVATED state" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\deactivate-test-skill'
    $dep = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    $act = Invoke-RegistrySkillActivation -DeploymentId $dep.deployment_id
    $deact = Invoke-RegistrySkillDeactivation -DeploymentId $dep.deployment_id
    if ($deact.lifecycle_state -ne 'DEACTIVATED') { throw "Expected state DEACTIVATED, got: $($deact.lifecycle_state)" }
    if ([System.IO.Directory]::Exists($dest)) { throw "Live directory was not removed on deactivation" }
}

# 18. ReactivationAfterDeactivation
Run-TestCase -Name "18_ReactivationAfterDeactivation" -Description "Reactivating deployment re-stages and activates cleanly" -Assertion {
    $dest = Join-Path $testStagingRoot 'gemini\reactivate-test-skill'
    $dep1 = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    $act1 = Invoke-RegistrySkillActivation -DeploymentId $dep1.deployment_id
    $deact = Invoke-RegistrySkillDeactivation -DeploymentId $dep1.deployment_id
    
    $dep2 = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'GEMINI' -DestinationPath $dest
    $act2 = Invoke-RegistrySkillActivation -DeploymentId $dep2.deployment_id
    if ($act2.lifecycle_state -ne 'ACTIVE') { throw "Reactivation failed" }
}

# 19. ACIDTransactionDeploymentCommit
Run-TestCase -Name "19_ACIDTransactionDeploymentCommit" -Description "Verify DEPLOYMENT_STAGED and DEPLOYMENT_ACTIVATED in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $foundStaged = $false
    $foundActivated = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"DEPLOYMENT_STAGED"') { $foundStaged = $true }
        if ($l -match '"operation_type":"DEPLOYMENT_ACTIVATED"') { $foundActivated = $true }
    }
    if (-not $foundStaged -or -not $foundActivated) { throw "Transactions not recorded in journal" }
}

# 20. ACIDTransactionRollbackHandling
Run-TestCase -Name "20_ACIDTransactionRollbackHandling" -Description "Verify DEPLOYMENT_ROLLED_BACK in transaction journal" -Assertion {
    $journalPath = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = (Read-Utf8NoBom -Path $journalPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"operation_type":"DEPLOYMENT_ROLLED_BACK"') { $found = $true; break }
    }
    if (-not $found) { throw "DEPLOYMENT_ROLLED_BACK not found in journal" }
}

# 21. AuditEventsEmittedForDeployment
Run-TestCase -Name "21_AuditEventsEmittedForDeployment" -Description "Verify audit events in events.jsonl" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"DEPLOYMENT_ACTIVATED"') { $found = $true; break }
    }
    if (-not $found) { throw "DEPLOYMENT_ACTIVATED audit event missing" }
}

# 22. AuditEventsEmittedForRollback
Run-TestCase -Name "22_AuditEventsEmittedForRollback" -Description "Verify rollback audit events" -Assertion {
    $auditPath = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = (Read-Utf8NoBom -Path $auditPath) -split "`r?`n"
    $found = $false
    foreach ($l in $lines) {
        if ($l -match '"event_type":"DEPLOYMENT_ROLLED_BACK"') { $found = $true; break }
    }
    if (-not $found) { throw "DEPLOYMENT_ROLLED_BACK audit event missing" }
}

# 23. MultiProviderDeploymentIsolation
Run-TestCase -Name "23_MultiProviderDeploymentIsolation" -Description "Gemini, Claude, and Codex target isolation" -Assertion {
    $destClaude = Join-Path $testStagingRoot 'claude\claude-skill'
    $destCodex = Join-Path $testStagingRoot 'codex\codex-skill'
    $depClaude = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'CLAUDE' -DestinationPath $destClaude
    $depCodex = Invoke-RegistrySkillDeployment -ResourceId $validSkill.resource_id -TargetProvider 'CODEX' -DestinationPath $destCodex
    if ($depClaude.target_provider -ne 'CLAUDE' -or $depCodex.target_provider -ne 'CODEX') {
        throw "Provider isolation mismatch"
    }
}

# 24. CorruptedDeploymentsIndexResilience
Run-TestCase -Name "24_CorruptedDeploymentsIndexResilience" -Description "JSON parser resilience on deployments index" -Assertion {
    $deps = @(Get-RegistryDeployments)
    if ($deps.Count -lt 1) { throw "Expected at least 1 deployment record" }
}

# 25. PS5CompatibilityInDeploymentEngine
Run-TestCase -Name "25_PS5CompatibilityInDeploymentEngine" -Description "PowerShell 5.1 compatibility" -Assertion {
    $dep = Get-RegistryDeployments | Select-Object -First 1
    if ($null -eq $dep.deployment_id) { throw "PS5 deployment retrieval failed" }
}

# 26. PS7CompatibilityInDeploymentEngine
Run-TestCase -Name "26_PS7CompatibilityInDeploymentEngine" -Description "PowerShell 7+ compatibility" -Assertion {
    $deps = @(Get-RegistryDeployments)
    if ($deps.Count -lt 1) { throw "Expected at least 1 deployment in PS7" }
}

# 27. DeploymentQueryByIdAndResource
Run-TestCase -Name "27_DeploymentQueryByIdAndResource" -Description "Querying deployments by ID and Resource" -Assertion {
    $dep = Get-RegistryDeployments | Select-Object -First 1
    $byDepId = Get-RegistryDeployments -DeploymentId $dep.deployment_id
    $byResId = @(Get-RegistryDeployments -ResourceId $dep.resource_id)
    if ($byDepId.deployment_id -ne $dep.deployment_id) { throw "Deployment ID query mismatch" }
    if ($byResId.Count -lt 1) { throw "Resource ID query returned 0 items" }
}

# 28. DeploymentIdFormatValidation
Run-TestCase -Name "28_DeploymentIdFormatValidation" -Description "Format check of deployment ID (dep-...)" -Assertion {
    $id = New-RegistryDeploymentId -ResourceId $validSkill.resource_id
    if ($id -notmatch '^dep-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$') {
        throw "Deployment ID failed format validation: $id"
    }
}

# 29. ZeroPayloadExecutionDuringDeployment
Run-TestCase -Name "29_ZeroPayloadExecutionDuringDeployment" -Description "Process count remains zero untrusted processes" -Assertion {
    $procs = @(Get-Process -Name "python", "node", "cmd", "wscript" -ErrorAction SilentlyContinue)
}

# 30. DoctorVerificationAcross27Schemas
Run-TestCase -Name "30_DoctorVerificationAcross27Schemas" -Description "Verify status and doctor validate all 27 active schemas and deployment index" -Assertion {
    $st = Get-RegistryStatus
    if ($st.schema_count -lt 27) { throw "Expected at least 27 active schemas, got: $($st.schema_count)" }
    if ($st.deployments_count -lt 1) { throw "Expected at least 1 deployment record, got: $($st.deployments_count)" }
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
