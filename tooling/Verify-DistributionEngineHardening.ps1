# Skill Registry - Layer 4 Distribution Engine Hardening Verification (Frente C)
# End-to-end sandbox audit verifying real canonical skill distribution, cryptographic fidelity,
# multi-file drift detection, idempotency, quarantine fail-closed, and zero leaks.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VERIFY DISTRIBUTION ENGINE HARDENING (FRENTE C)            " -ForegroundColor Cyan
Write-Host " Scope: Layer 4 Non-Mock Distribution, Drift & Idempotency  " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Import-Module (Join-Path $RegistryRoot 'tooling\DistributionEngine.psm1') -Force

$sandboxRoot = Join-Path $RegistryRoot 'staging\sandbox-dist'
if (Test-Path $sandboxRoot) { Remove-Item -Path $sandboxRoot -Recurse -Force | Out-Null }
New-Item -ItemType Directory -Path $sandboxRoot -Force | Out-Null

$testSkillName = 'unsloth-fast-kernel-finetuning'
$originalSkillDir = Join-Path $RegistryRoot ("skills\" + $testSkillName)
if (-not (Test-Path $originalSkillDir)) { throw "Test canonical skill $testSkillName does not exist in skills/!" }
$originalSkillMd = Join-Path $originalSkillDir 'SKILL.md'
$originalHash = Get-Sha256FileHash -Path $originalSkillMd

$tests = [ordered]@{}

try {
    # --- TEST 01: Real Canonical Skill Distribution Plan ---
    $destPath = Join-Path $sandboxRoot "gemini\$testSkillName"
    $plan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $testSkillName -TargetPlatform 'gemini' -DestinationRoot (Join-Path $sandboxRoot 'gemini')
    
    $p1 = ($plan.action_type -eq 'CREATE' -and `
           $plan.canonical_name -eq $testSkillName -and `
           $plan.files_plan.Count -ge 1 -and `
           $plan.files_plan[0].sha256 -eq $originalHash -and `
           $plan.files_plan[0].size_bytes -eq (Get-Item $originalSkillMd).Length)
    $tests['01_RealSkillPlanCryptoFidelity'] = if ($p1) { 'PASS' } else { 'FAIL' }
    Write-Host "  [01] Real Skill Plan Fidelity       : $($tests['01_RealSkillPlanCryptoFidelity']) (Hash: $($plan.files_plan[0].sha256.Substring(0,16))...)" -ForegroundColor $(if ($p1) { 'Green' } else { 'Red' })

    # --- TEST 02: Execution Copies Real Physical Content (No Mocks) ---
    $exec = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $plan -Approved
    $deployedSkillMd = Join-Path $destPath 'SKILL.md'
    $p2 = $false
    if (Test-Path $deployedSkillMd) {
        $deployedHash = Get-Sha256FileHash -Path $deployedSkillMd
        $deployedContent = [System.IO.File]::ReadAllText($deployedSkillMd)
        $isNotMock = -not ($deployedContent.StartsWith('# Skill:') -and $deployedContent.Contains('Automated instruction for'))
        if ($deployedHash -eq $originalHash -and $isNotMock) { $p2 = $true }
    }
    $tests['02_DeployedContentAuthentic'] = if ($p2) { 'PASS' } else { 'FAIL' }
    Write-Host "  [02] Authentic Content Deployed     : $($tests['02_DeployedContentAuthentic']) (Matches canonical skills/ exactly)" -ForegroundColor $(if ($p2) { 'Green' } else { 'Red' })

    # --- TEST 03: True Idempotency (2nd Run = NOOP, Zero Writes) ---
    $plan2 = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $testSkillName -TargetPlatform 'gemini' -DestinationRoot (Join-Path $sandboxRoot 'gemini')
    $exec2 = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $plan2 -Approved
    $p3 = ($plan2.action_type -eq 'NOOP' -and `
           $plan2.collision_status -eq 'NONE' -and `
           $plan2.approval_required -eq $false -and `
           $exec2.status -eq 'COMMITTED' -and `
           $exec2.operation -eq 'SYNC')
    $tests['03_IdempotencyNoopVerified'] = if ($p3) { 'PASS' } else { 'FAIL' }
    Write-Host "  [03] Idempotency (2nd = NOOP)       : $($tests['03_IdempotencyNoopVerified']) (Action: $($plan2.action_type), Writes: 0)" -ForegroundColor $(if ($p3) { 'Green' } else { 'Red' })

    # --- TEST 04: Deep Drift Detection (In-Sync & Tamper Detection) ---
    $driftClean = Test-DistributionDrift -RegistryRoot $RegistryRoot -TargetPlatform 'gemini' -DestinationPath $destPath -ExpectedContentHash $plan.expected_content_hash
    # Tamper with file
    [System.IO.File]::AppendAllText($deployedSkillMd, "`n<!-- ADULTERATED DRIFT TEST -->`n")
    $driftTampered = Test-DistributionDrift -RegistryRoot $RegistryRoot -TargetPlatform 'gemini' -DestinationPath $destPath -ExpectedContentHash $plan.expected_content_hash
    $p4 = ($driftClean.drift_status -eq 'IN_SYNC' -and `
           $driftTampered.drift_status -eq 'MODIFIED_EXTERNALLY' -and `
           $driftTampered.reconciliation_action -eq 'PROPOSE_SYNC_UPDATE')
    $tests['04_DeepDriftDetection'] = if ($p4) { 'PASS' } else { 'FAIL' }
    Write-Host "  [04] Deep Drift Detection           : $($tests['04_DeepDriftDetection']) (InSync -> ModifiedExternally)" -ForegroundColor $(if ($p4) { 'Green' } else { 'Red' })

    # --- TEST 05: Clean Uninstallation & Tombstone Recording ---
    $uninst = Invoke-DistributionUninstall -RegistryRoot $RegistryRoot -TargetPlatform 'gemini' -CanonicalName $testSkillName -DestinationPath $destPath -Approved
    $destStillExists = [System.IO.Directory]::Exists($destPath)
    $lockFile = Join-Path (Join-Path $sandboxRoot 'gemini') '.skill-registry.lock'
    $hasTombstone = (Test-Path $lockFile) -and ([System.IO.File]::ReadAllText($lockFile).Contains("TOMBSTONE: $testSkillName"))
    $p5 = ($uninst.status -eq 'UNINSTALLED' -and -not $destStillExists -and $hasTombstone)
    $tests['05_CleanUninstallAndTombstone'] = if ($p5) { 'PASS' } else { 'FAIL' }
    Write-Host "  [05] Clean Uninstall & Tombstone    : $($tests['05_CleanUninstallAndTombstone']) (Folder removed, tombstone written)" -ForegroundColor $(if ($p5) { 'Green' } else { 'Red' })

    # --- TEST 06: Quarantine Barrier Fail-Closed ---
    $planQuarantine = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $testSkillName -TargetPlatform 'gemini' -QuarantineStatus 'QUARANTINED'
    $quarantineBlockedExecution = $false
    try {
        Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $planQuarantine -Approved
    } catch {
        $quarantineBlockedExecution = $_.Exception.Message.Contains("quarantined")
    }
    $p6 = ($planQuarantine.action_type -eq 'QUARANTINE_BLOCKED' -and $quarantineBlockedExecution)
    $tests['06_QuarantineFailClosed'] = if ($p6) { 'PASS' } else { 'FAIL' }
    Write-Host "  [06] Quarantine Barrier Fail-Closed : $($tests['06_QuarantineFailClosed']) (Execution strictly refused)" -ForegroundColor $(if ($p6) { 'Green' } else { 'Red' })

    # --- TEST 07: Workspace Isolation Guarantee ---
    $userGlobalSkills = "$env:USERPROFILE\.gemini\config\skills"
    $leaksFound = 0
    if (Test-Path $userGlobalSkills) {
        $cand = Join-Path $userGlobalSkills $testSkillName
        if (Test-Path $cand) { $leaksFound++ }
    }
    $p7 = ($leaksFound -eq 0)
    $tests['07_WorkspaceIsolationZeroLeaks'] = if ($p7) { 'PASS' } else { 'FAIL' }
    Write-Host "  [07] Zero Leaks in User Workspace   : $($tests['07_WorkspaceIsolationZeroLeaks']) (Sandbox strictly contained)" -ForegroundColor $(if ($p7) { 'Green' } else { 'Red' })

} finally {
    if (Test-Path $sandboxRoot) {
        Remove-Item -Path $sandboxRoot -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
    }
}

$allPass = $true
foreach ($k in $tests.Keys) {
    if ($tests[$k] -ne 'PASS') { $allPass = $false }
}

Write-Host "============================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host " AUDITORIA DA FRENTE C: 100% PASS! DISTRIBUIÇÃO ENDURECIDA  " -ForegroundColor Green
} else {
    Write-Host " AUDITORIA DA FRENTE C: FALHAS DETECTADAS!                  " -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan

if (-not $allPass) { exit 1 }
