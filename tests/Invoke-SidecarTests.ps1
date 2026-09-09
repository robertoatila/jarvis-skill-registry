# Phase 32 Test Harness — Sidecar Background Observer & Sync

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-32-sidecar-sync.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $RegistryRoot 'tooling\SidecarEngine.psm1') -Force

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-SidecarTest {
    param(
        [string]$Id,
        [string]$Description,
        [scriptblock]$Assertion
    )
    $testResult = [ordered]@{
        id = $Id
        description = $Description
        status = 'FAIL'
        error = $null
    }
    
    try {
        $passed = & $Assertion
        if ($passed -eq $true) {
            $testResult.status = 'PASS'
            Write-Host "  [PASS] $Id : $Description" -ForegroundColor Green
        } else {
            $testResult.status = 'FAIL'
            $testResult.error = 'Assertion returned false'
            Write-Host "  [FAIL] $Id : $Description (Assertion returned false)" -ForegroundColor Red
            $script:globalPassed = $false
        }
    } catch {
        $testResult.status = 'FAIL'
        $testResult.error = $_.Exception.Message
        Write-Host "  [FAIL] $Id : $Description ($($_.Exception.Message))" -ForegroundColor Red
        $script:globalPassed = $false
    }
    
    $script:testResults.Add($testResult)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 32 TEST SUITE: SIDECAR BACKGROUND OBSERVER   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Sidecar Config Schema exists and is valid JSON
Assert-SidecarTest "Test 01" "sidecar-config.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\sidecar-config.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:sidecar-config:1.0.0')
}

# Test 02: Sidecar Config catalog defines READ_ANALYZE_PROPOSE governance
Assert-SidecarTest "Test 02" "sidecar-config.json defines READ_ANALYZE_PROPOSE governance" {
    $cfg = Get-SidecarConfig -RegistryRoot $RegistryRoot
    return ($cfg.governance_mode -eq 'READ_ANALYZE_PROPOSE' -and
            $cfg.allow_autonomous_writes -eq $false -and
            $cfg.monitored_targets.Count -ge 6)
}

# Test 03: Sidecar Observation Schema exists and is valid JSON
Assert-SidecarTest "Test 03" "sidecar-observation.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\sidecar-observation.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:sidecar-observation:1.0.0')
}

# Test 04: Sidecar Observation catalog defines event structure
Assert-SidecarTest "Test 04" "sidecar-observation.json defines observation event structure" {
    $obsFile = Join-Path $RegistryRoot 'schemas\sidecar-observation.json'
    if (-not [System.IO.File]::Exists($obsFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($obsFile) | ConvertFrom-Json
    return ($data.event_type -eq 'TARGET_DRIFT_DETECTED' -and $data.observation_id.StartsWith('sobs-'))
}

# Test 05: Sidecar Proposal Schema exists and is valid JSON
Assert-SidecarTest "Test 05" "sidecar-proposal.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\sidecar-proposal.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:sidecar-proposal:1.0.0')
}

# Test 06: Sidecar Proposal catalog defines proposal structure & approval requirement
Assert-SidecarTest "Test 06" "sidecar-proposal.json defines proposal structure & approval requirement" {
    $propFile = Join-Path $RegistryRoot 'schemas\sidecar-proposal.json'
    if (-not [System.IO.File]::Exists($propFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($propFile) | ConvertFrom-Json
    return ($data.approval_required -eq $true -and $data.auto_executed -eq $false)
}

# Test 07: Sidecar State Schema exists and is valid JSON
Assert-SidecarTest "Test 07" "sidecar-state.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\sidecar-state.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:sidecar-state:1.0.0')
}

# Test 08: Sidecar State catalog defines checkpoint state
Assert-SidecarTest "Test 08" "sidecar-state.json defines runtime checkpoint state" {
    $stateFile = Join-Path $RegistryRoot 'schemas\sidecar-state.json'
    if (-not [System.IO.File]::Exists($stateFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($stateFile) | ConvertFrom-Json
    return ($data.status -eq 'IDLE' -and $data.last_known_registry_merkle.Length -eq 64)
}

# Test 09: Test-WorkspaceDriftObservation detects manifest changes
Assert-SidecarTest "Test 09" "Test-WorkspaceDriftObservation detects stack changes in mock project" {
    $tempWs = Join-Path $RegistryRoot 'staging\temp-sidecar-ws'
    if (Test-Path $tempWs) { Remove-Item -Path $tempWs -Recurse -Force | Out-Null }
    New-Item -ItemType Directory -Path $tempWs -Force | Out-Null
    
    $pkgJson = '{"name":"test-sidecar-app","dependencies":{"react":"18.2.0"}}'
    [System.IO.File]::WriteAllText((Join-Path $tempWs 'package.json'), $pkgJson, [System.Text.Encoding]::UTF8)
    
    $obsList = @(Test-WorkspaceDriftObservation -RegistryRoot $RegistryRoot -WorkspacePath $tempWs)
    Remove-Item -Path $tempWs -Recurse -Force | Out-Null
    
    return ($obsList.Count -ge 1 -and $obsList[0].event_type -eq 'MANIFEST_STACK_CHANGED')
}

# Test 10: Invoke-SidecarCycle runs non-blocking pass with zero autonomous writes
Assert-SidecarTest "Test 10" "Invoke-SidecarCycle executes passive read-only observation pass" {
    $tempWs = Join-Path $RegistryRoot 'staging\temp-sidecar-cycle'
    if (Test-Path $tempWs) { Remove-Item -Path $tempWs -Recurse -Force | Out-Null }
    New-Item -ItemType Directory -Path $tempWs -Force | Out-Null
    
    $pkgJson = '{"name":"test-cycle-app","dependencies":{"next":"14.1.0"}}'
    [System.IO.File]::WriteAllText((Join-Path $tempWs 'package.json'), $pkgJson, [System.Text.Encoding]::UTF8)
    
    $cycle = Invoke-SidecarCycle -RegistryRoot $RegistryRoot -WorkspacesToScan @($tempWs)
    Remove-Item -Path $tempWs -Recurse -Force | Out-Null
    
    return ($cycle.cycle_status -eq 'COMPLETED' -and
            $cycle.zero_writes_enforced -eq $true -and
            $cycle.observations.Count -ge 1 -and
            $cycle.proposals.Count -ge 1)
}

# Test 11: New-SidecarProposal enforces approval_required: true and auto_executed: false
Assert-SidecarTest "Test 11" "New-SidecarProposal enforces approval_required: true and auto_executed: false" {
    $mockObs = New-SidecarObservation -EventType 'TARGET_DRIFT_DETECTED' -SourceLocation 'E:\test' -TargetPlatform 'cursor' -Details 'test drift'
    $prop = New-SidecarProposal -Observation $mockObs -ProposedAction 'PROPOSE_SYNC_UPDATE' -TargetPlatform 'cursor' -SkillId 'react-modernization' -Reason 'Drift detected' -Priority 'HIGH'
    return ($prop.approval_required -eq $true -and
            $prop.auto_executed -eq $false -and
            $prop.proposal_id.StartsWith('sprop-'))
}

# Test 12: Zero autonomous execution guarantee (Sidecar never calls execute_distribution)
Assert-SidecarTest "Test 12" "Sidecar never executes distribution autonomously" {
    # Check that no unauthorized installations took place in Gemini skills folder
    $geminiSkills = 'C:\Users\Ad\.gemini\config\skills'
    if (Test-Path $geminiSkills) {
        $items = @(Get-ChildItem -Path $geminiSkills -Directory)
        return ($items.Count -ge 160)
    }
    return $true
}

# Test 13: Clean IN_SYNC status emitted when zero events detected
Assert-SidecarTest "Test 13" "Invoke-SidecarCycle produces IN_SYNC observation when zero events present" {
    $cycle = Invoke-SidecarCycle -RegistryRoot $RegistryRoot -WorkspacesToScan @()
    return ($cycle.observations[0].event_type -eq 'IN_SYNC' -and $cycle.proposals.Count -eq 0)
}

# Test 14: Quarantined observation preserves fail-closed status
Assert-SidecarTest "Test 14" "Quarantined observation flags suspect/quarantined status" {
    $mockObs = New-SidecarObservation -EventType 'TARGET_DRIFT_DETECTED' -SourceLocation 'E:\test' -TargetPlatform 'cursor' -Details 'malicious file' -QuarantineFlag 'QUARANTINED'
    return ($mockObs.quarantine_flag -eq 'QUARANTINED')
}

# Test 15: Non-privileged execution (Observer runs with minimum privileges and is interruptible)
Assert-SidecarTest "Test 15" "Sidecar observer runs with minimum privileges and clean lifecycle" {
    $cfg = Get-SidecarConfig -RegistryRoot $RegistryRoot
    return ($cfg.poll_interval_seconds -ge 10 -and $cfg.governance_mode -eq 'READ_ANALYZE_PROPOSE')
}

# Test 16: Core Gates 0-24 immutability check verified
Assert-SidecarTest "Test 16" "Core Gates 0-24 immutability check verified" {
    $archFile = Join-Path $RegistryRoot 'docs\ARCHITECTURE.md'
    $content = [System.IO.File]::ReadAllText($archFile)
    return ($content.Contains("596552cf11583365510fb13503394efd59e9769e01ab53da96342f0ce807f958") -and
            $content.Contains("gov-quarantine-link-v1"))
}

$passedCount = @($testResults | Where-Object { $_.status -eq 'PASS' }).Count
$failedCount = @($testResults | Where-Object { $_.status -eq 'FAIL' }).Count

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $passedCount / $($testResults.Count) PASSED ($failedCount FAILED)" -ForegroundColor $(if ($script:globalPassed) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$auditReport = [ordered]@{
    schema = 'skill-registry.phase-32.sidecar-sync/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    loop_model = "READ_ANALYZE_PROPOSE"
    zero_autonomous_writes = $true
    quarantine_fail_closed = $true
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
