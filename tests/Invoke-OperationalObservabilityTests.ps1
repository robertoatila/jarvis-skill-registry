# Phase 19 Test Suite: Registry Operational Observability, Audit & Recovery Governance
# 30 Synthetic Scenarios verifying Schema #31, Telemetry, Consistency Proofs, Checkpoints, Timelines, and Invariants

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-19-observability.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

$passCount = 0
$failCount = 0
$testResults = New-Object 'System.Collections.Generic.List[object]'

function Assert-Test {
    param(
        [string]$TestId,
        [string]$Description,
        [scriptblock]$Assertion
    )
    
    try {
        $result = & $Assertion
        if ($result -eq $true) {
            $script:passCount++
            Write-Host "  [PASS] $TestId : $Description" -ForegroundColor Green
            $script:testResults.Add([ordered]@{
                id = $TestId
                description = $Description
                status = 'PASS'
                error = $null
            })
        } else {
            $script:failCount++
            Write-Host "  [FAIL] $TestId : $Description (Assertion returned false)" -ForegroundColor Red
            $script:testResults.Add([ordered]@{
                id = $TestId
                description = $Description
                status = 'FAIL'
                error = 'Assertion returned false'
            })
        }
    } catch {
        $script:failCount++
        Write-Host "  [FAIL] $TestId : $Description (Exception: $($_.Exception.Message))" -ForegroundColor Red
        $script:testResults.Add([ordered]@{
            id = $TestId
            description = $Description
            status = 'FAIL'
            error = $_.Exception.Message
        })
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 19 TEST SUITE: OPERATIONAL OBSERVABILITY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Schema #31 exists and is valid JSON
Assert-Test "Test 01" "Schema #31 definition exists and is valid JSON" {
    $sFile = Join-Path $RegistryRoot 'schemas\operational-observability.schema.json'
    if (-not [System.IO.File]::Exists($sFile)) { return $false }
    $content = Read-Utf8NoBom -Path $sFile
    $json = $content | ConvertFrom-Json
    return ($null -ne $json -and $json.title -eq 'SkillRegistryOperationalObservability')
}

# Test 02: Schema #31 specifies required properties
Assert-Test "Test 02" "Schema #31 specifies required governance and telemetry properties" {
    $sFile = Join-Path $RegistryRoot 'schemas\operational-observability.schema.json'
    $json = (Read-Utf8NoBom -Path $sFile) | ConvertFrom-Json
    $req = $json.required
    return ($req -contains 'snapshot_id' -and $req -contains 'subsystem_telemetry' -and $req -contains 'ledger_consistency_proof' -and $req -contains 'recovery_checkpoint' -and $req -contains 'quarantine_guard_status')
}

# Test 03: New-RegistryObservabilitySnapshotId format
Assert-Test "Test 03" "New-RegistryObservabilitySnapshotId generates valid pattern" {
    $snapId = New-RegistryObservabilitySnapshotId
    return ($snapId -match '^obs-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$')
}

# Test 04: New-RegistryRecoveryCheckpointId format
Assert-Test "Test 04" "New-RegistryRecoveryCheckpointId generates valid pattern" {
    $chkId = New-RegistryRecoveryCheckpointId
    return ($chkId -match '^recchk-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$')
}

# Test 05: Get-RegistrySubsystemTelemetry structure
Assert-Test "Test 05" "Get-RegistrySubsystemTelemetry extracts structured metrics across subsystems" {
    $telem = Get-RegistrySubsystemTelemetry
    return ($null -ne $telem.overall_health -and $telem.active_schemas_count -ge 30 -and $telem.discovered_resources_count -ge 0)
}

# Test 06: Subsystem health reporting
Assert-Test "Test 06" "Get-RegistrySubsystemTelemetry reports overall_health as HEALTHY in baseline state" {
    $telem = Get-RegistrySubsystemTelemetry
    return ($telem.overall_health -eq 'HEALTHY')
}

# Test 07: Deployments by state calculation
Assert-Test "Test 07" "Subsystem telemetry correctly computes deployments_by_state breakdown" {
    $telem = Get-RegistrySubsystemTelemetry
    $depStates = $telem.deployments_by_state
    return ($null -ne $depStates.ACTIVE -and $null -ne $depStates.STAGED -and $null -ne $depStates.ROLLED_BACK)
}

# Test 08: Deployments by provider distribution
Assert-Test "Test 08" "Subsystem telemetry correctly computes deployments_by_provider distribution" {
    $telem = Get-RegistrySubsystemTelemetry
    return ($null -ne $telem.deployments_by_provider)
}

# Test 09: Updates by state calculation
Assert-Test "Test 09" "Subsystem telemetry correctly computes updates_by_state breakdown" {
    $telem = Get-RegistrySubsystemTelemetry
    $updStates = $telem.updates_by_state
    return ($null -ne $updStates.EVALUATED -and $null -ne $updStates.STAGED)
}

# Test 10: Schedules by state calculation
Assert-Test "Test 10" "Subsystem telemetry correctly computes schedules_by_state breakdown" {
    $telem = Get-RegistrySubsystemTelemetry
    $schedStates = $telem.schedules_by_state
    return ($null -ne $schedStates.ENABLED -and $schedStates.CIRCUIT_OPEN -eq 0)
}

# Test 11: Consistency proof passes on intact repository
Assert-Test "Test 11" "Invoke-RegistryConsistencyVerification returns VERIFIED_HEALTHY on intact indices" {
    $proof = Invoke-RegistryConsistencyVerification
    return ($proof.status -eq 'VERIFIED_HEALTHY' -and $proof.corrupt_lines_found -eq 0 -and $proof.broken_references_found -eq 0)
}

# Test 12: Invariant evaluation in consistency proof
Assert-Test "Test 12" "Consistency verification confirms 0 auto_promote violations and 0 quarantine violations" {
    $proof = Invoke-RegistryConsistencyVerification
    return ($proof.auto_promote_violations -eq 0 -and $proof.quarantine_violations -eq 0)
}

# Test 13: Recovery checkpoint deterministic Merkle root
Assert-Test "Test 13" "New-RegistryRecoveryCheckpoint computes valid 64-char hex SHA-256 Merkle root" {
    $chk = New-RegistryRecoveryCheckpoint -DryRun
    return ($chk.indices_checksum_merkle_root -match '^[a-f0-9]{64}$' -and $chk.total_indices_hashed -ge 20)
}

# Test 14: Recovery checkpoint persists state file
Assert-Test "Test 14" "New-RegistryRecoveryCheckpoint persists checkpoint to state\\recovery-checkpoint.json" {
    $chk = New-RegistryRecoveryCheckpoint
    $chkFile = Join-Path $RegistryRoot 'state\recovery-checkpoint.json'
    if (-not [System.IO.File]::Exists($chkFile)) { return $false }
    $content = (Read-Utf8NoBom -Path $chkFile) | ConvertFrom-Json
    return ($content.checkpoint_id -eq $chk.checkpoint_id -and $content.indices_checksum_merkle_root -eq $chk.indices_checksum_merkle_root)
}

# Test 15: Observability snapshot generation
Assert-Test "Test 15" "Invoke-RegistryObservabilitySnapshot creates valid compliant snapshot object" {
    $snap = Invoke-RegistryObservabilitySnapshot -DryRun
    return ($snap.schema_version -eq '1.0.0' -and $snap.snapshot_id -match '^obs-' -and $snap.subsystem_telemetry.overall_health -eq 'HEALTHY')
}

# Test 16: Observability snapshot persists to index
Assert-Test "Test 16" "Invoke-RegistryObservabilitySnapshot appends snapshot record to observability-snapshots.jsonl" {
    $snap = Invoke-RegistryObservabilitySnapshot
    $snapFile = Join-Path $RegistryRoot 'index\observability-snapshots.jsonl'
    $lines = @((Read-Utf8NoBom -Path $snapFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match $snap.snapshot_id })
    return ($lines.Count -ge 1)
}

# Test 17: Observability snapshot DryRun does not mutate index
Assert-Test "Test 17" "Invoke-RegistryObservabilitySnapshot with -DryRun does not persist mutations" {
    $snapFile = Join-Path $RegistryRoot 'index\observability-snapshots.jsonl'
    $beforeLines = @((Read-Utf8NoBom -Path $snapFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match 'obs-' }).Count
    $snapDry = Invoke-RegistryObservabilitySnapshot -DryRun
    $afterLines = @((Read-Utf8NoBom -Path $snapFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match 'obs-' }).Count
    return ($beforeLines -eq $afterLines)
}

# Test 18: State recovery reconstructs missing current-state.json
Assert-Test "Test 18" "Invoke-RegistryStateRecovery rebuilds current-state.json from live indices" {
    $stFile = Join-Path $RegistryRoot 'state\current-state.json'
    $recoveryResult = Invoke-RegistryStateRecovery -ForceRebuild
    $st = (Read-Utf8NoBom -Path $stFile) | ConvertFrom-Json
    return ($recoveryResult.status -eq 'RECOVERED' -and $st.schemas_active_count -ge 30 -and $st.quarantine_link_status -eq 'LOCKED_VALID')
}

# Test 19: Lifecycle timeline reconstructs audit events
Assert-Test "Test 19" "Get-RegistryLifecycleTimeline queries and reconstructs audit events for target entity" {
    # Write a test audit event to verify timeline reconstruction
    $txRes = Invoke-RegistryTransaction -OperationType 'TEST_OBSERVABILITY_EVENT' -Action {
        param($TxId)
        Write-RegistryAuditEvent -EventType 'TEST_OBSERVABILITY_EVENT' -Action 'TEST_TIMELINE' -Result 'SUCCESS' `
                                 -TransactionId $TxId -Component 'ObservabilityTest' -TargetResourceId 'test-timeline-skill' `
                                 -Details @{ reason = 'timeline_verification' }
    } -Initiator 'ObservabilityTestHarness'
    
    $timeline = @(Get-RegistryLifecycleTimeline -Identifier 'test-timeline-skill')
    return ($timeline.Count -ge 1 -and $timeline[0].event_type -eq 'TEST_OBSERVABILITY_EVENT')
}

# Test 20: Lifecycle timeline ordering
Assert-Test "Test 20" "Get-RegistryLifecycleTimeline returns events sorted strictly by timestamp_utc ascending" {
    $timeline = @(Get-RegistryLifecycleTimeline -Identifier 'test-timeline-skill')
    if ($timeline.Count -le 1) { return $true }
    for ($i = 1; $i -lt $timeline.Count; $i++) {
        if ([string]::CompareOrdinal($timeline[$i].timestamp_utc, $timeline[$i-1].timestamp_utc) -lt 0) { return $false }
    }
    return $true
}

# Test 21: Invariant: Quarantine precedence baseline
Assert-Test "Test 21" "Quarantine precedence baseline is locked at 118 tombstones and 8 subtrees" {
    $telem = Get-RegistrySubsystemTelemetry
    return ($telem.quarantine_tombstones_count -eq 118 -and $telem.quarantine_blocked_subtrees_count -eq 8)
}

# Test 22: Strict Invariant: Zero unattended active promotions
Assert-Test "Test 22" "Strict Invariant: Observability snapshots and checkpoints never mutate live active deployments" {
    $depBefore = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    $null = Invoke-RegistryObservabilitySnapshot
    $null = New-RegistryRecoveryCheckpoint
    $null = Invoke-RegistryConsistencyVerification
    $depAfter = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    return ($depBefore -eq $depAfter)
}

# Test 23: Telemetry detects degraded health when schedule circuit breaker trips
Assert-Test "Test 23" "Telemetry transitions overall_health to DEGRADED when circuit breaker is open" {
    # Register test schedule and trip circuit breaker
    $schedName = "test-obs-tripped-$(Get-Random)"
    $sched = Register-RegistrySchedule -ScheduleName $schedName -Initiator 'TestHarness'
    $null = Set-RegistryScheduleState -ScheduleId $sched.schedule_id -State 'CIRCUIT_OPEN'
    
    $telem = Get-RegistrySubsystemTelemetry
    $degradedCheck = ($telem.overall_health -eq 'DEGRADED' -and $telem.schedules_by_state.CIRCUIT_OPEN -ge 1)
    
    # Cleanup schedule by disabling it
    $null = Set-RegistryScheduleState -ScheduleId $sched.schedule_id -State 'DISABLED'
    return $degradedCheck
}

# Test 24: Telemetry health recovers after circuit breaker reset
Assert-Test "Test 24" "Telemetry health recovers to HEALTHY when circuit breaker is reset" {
    $telem = Get-RegistrySubsystemTelemetry
    return ($telem.overall_health -eq 'HEALTHY')
}

# Test 25: ACID transaction journal logs OBSERVABILITY_SNAPSHOT_SAVED
Assert-Test "Test 25" "ACID transaction journal logs OBSERVABILITY_SNAPSHOT_SAVED operation" {
    $jFile = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = @((Read-Utf8NoBom -Path $jFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match 'OBSERVABILITY_SNAPSHOT_SAVED' })
    return ($lines.Count -ge 1)
}

# Test 26: ACID transaction journal logs RECOVERY_CHECKPOINT_CREATED
Assert-Test "Test 26" "ACID transaction journal logs RECOVERY_CHECKPOINT_CREATED operation" {
    $jFile = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $lines = @((Read-Utf8NoBom -Path $jFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match 'RECOVERY_CHECKPOINT_CREATED' })
    return ($lines.Count -ge 1)
}

# Test 27: Audit trail logs RECOVERY_CHECKPOINT_CREATED event
Assert-Test "Test 27" "Audit trail events.jsonl contains RECOVERY_CHECKPOINT_CREATED events" {
    $eFile = Join-Path $RegistryRoot 'audit\events.jsonl'
    $lines = @((Read-Utf8NoBom -Path $eFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -match 'RECOVERY_CHECKPOINT_CREATED' })
    return ($lines.Count -ge 1)
}

# Test 28: Test-RegistryOperationalHealth returns HEALTHY
Assert-Test "Test 28" "Test-RegistryOperationalHealth reports overall_health as HEALTHY" {
    $health = Test-RegistryOperationalHealth
    return ($health.overall_health -eq 'HEALTHY' -and $health.schema_conformance -eq 'PASS' -and $health.consistency_status -eq 'PASS')
}

# Test 29: Get-RegistryStatus includes observability_snapshots_count
Assert-Test "Test 29" "Get-RegistryStatus includes observability_snapshots_count and active schemas" {
    $status = Get-RegistryStatus
    return ($null -ne $status.observability_snapshots_count -and $status.schema_count -ge 31)
}

# Test 30: CLI skillctl observe telemetry and doctor execution
Assert-Test "Test 30" "CLI skillctl observe doctor executes successfully with exit code 0" {
    $cliScript = Join-Path $RegistryRoot 'tooling\skillctl.ps1'
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $cliScript observe doctor
    $passText = ($output -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY'
    return $passText
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $passCount / $($passCount + $failCount) PASSED ($failCount FAILED)" -ForegroundColor $(if ($failCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-19.observability-tests/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($failCount -eq 0) { 'PASS' } else { 'FAIL' }
    passed_count = $passCount
    failed_count = $failCount
    test_cases = $testResults.ToArray()
}

$jsonOutput = ($reportObj | ConvertTo-Json -Depth 5)
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $parentDir = [System.IO.Path]::GetDirectoryName($OutputPath)
    if (-not [System.IO.Directory]::Exists($parentDir)) {
        [void][System.IO.Directory]::CreateDirectory($parentDir)
    }
    [System.IO.File]::WriteAllText($OutputPath, $jsonOutput + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
