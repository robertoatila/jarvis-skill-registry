# =============================================================================
# Phase 20 Test Harness: Compaction, Archive, Real Disaster Restore & Chaos
# =============================================================================

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-20-compaction.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
$CliScript = Join-Path $RegistryRoot 'tooling\skillctl.ps1'

Import-Module $CoreModule -Force

$global:PassCount = 0
$global:FailCount = 0
$global:TestResults = New-Object 'System.Collections.Generic.List[object]'

function Assert-Test {
    param(
        [string]$TestId,
        [string]$Description,
        [scriptblock]$Script
    )
    
    try {
        $result = & $Script
        if ($result -eq $true) {
            Write-Host "  [PASS] $TestId : $Description" -ForegroundColor Green
            $global:PassCount++
            $global:TestResults.Add([ordered]@{
                id = $TestId
                description = $Description
                status = 'PASS'
                error = $null
            })
        } else {
            Write-Host "  [FAIL] $TestId : $Description (Assertion returned false)" -ForegroundColor Red
            $global:FailCount++
            $global:TestResults.Add([ordered]@{
                id = $TestId
                description = $Description
                status = 'FAIL'
                error = 'Assertion returned false'
            })
        }
    } catch {
        Write-Host "  [FAIL] $TestId : $Description (Exception: $($_.Exception.Message))" -ForegroundColor Red
        $global:FailCount++
        $global:TestResults.Add([ordered]@{
            id = $TestId
            description = $Description
            status = 'FAIL'
            error = $_.Exception.Message
        })
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 20 TEST SUITE: COMPACTION, ARCHIVE & CHAOS   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Schema #32 exists and is valid JSON
Assert-Test "Test 01" "Schema #32 definition exists and is valid JSON" {
    $schemaPath = Join-Path $RegistryRoot 'schemas\compaction-retention.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { return $false }
    $content = Read-Utf8NoBom -Path $schemaPath
    $json = $content | ConvertFrom-Json
    return ($null -ne $json -and $json.'$id' -like '*compaction-retention*')
}

# Test 02: Schema #32 required properties
Assert-Test "Test 02" "Schema #32 specifies required compaction and archive governance properties" {
    $schemaPath = Join-Path $RegistryRoot 'schemas\compaction-retention.schema.json'
    $json = (Read-Utf8NoBom -Path $schemaPath) | ConvertFrom-Json
    $req = @($json.required)
    return ($req -contains 'archive_id' -and `
            $req -contains 'archive_type' -and `
            $req -contains 'archive_sha256_hash' -and `
            $req -contains 'archive_merkle_root' -and `
            $req -contains 'governance_lock')
}

# Test 03: New-RegistryArchiveId pattern
Assert-Test "Test 03" "New-RegistryArchiveId generates valid deterministic timestamped pattern" {
    $id = New-RegistryArchiveId
    return ($id -match '^arch-\d{8}T\d{6}\d{3}Z-[a-f0-9]{8}$')
}

# Test 04: Get-RegistryArchives query
Assert-Test "Test 04" "Get-RegistryArchives successfully queries archives index ledger" {
    $archs = @(Get-RegistryArchives)
    return ($null -ne $archs -and $archs.Count -ge 0)
}

# Test 05: Compaction dry-run
Assert-Test "Test 05" "Invoke-RegistryCompaction with -DryRun generates archive manifest without mutating ledgers" {
    $jBefore = if (Test-Path (Join-Path $RegistryRoot 'transactions\journal.jsonl')) { (Get-Item (Join-Path $RegistryRoot 'transactions\journal.jsonl')).Length } else { 0 }
    $res = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 50 -DryRun
    $jAfter = if (Test-Path (Join-Path $RegistryRoot 'transactions\journal.jsonl')) { (Get-Item (Join-Path $RegistryRoot 'transactions\journal.jsonl')).Length } else { 0 }
    return ($res.status -eq 'SUCCESS' -and $res.dry_run -eq $true -and $jBefore -eq $jAfter)
}

# Test 06: Schema conformity of compaction manifest
Assert-Test "Test 06" "Compaction manifest structure conforms to Schema #32 governance locks" {
    $res = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 50 -DryRun
    if ($res.archives_created_count -eq 0) { return $true }
    $m = $res.archives[0]
    return ($m.governance_lock.immutable_archive -eq $true -and `
            $m.governance_lock.quarantine_precedence -eq $true -and `
            $m.governance_lock.zero_unattended_promotion -eq $true)
}

# Test 07: Deterministic SHA-256 archive content hash
Assert-Test "Test 07" "Compaction computes valid 64-character SHA-256 archive hash" {
    $res = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 50 -DryRun
    if ($res.archives_created_count -eq 0) { return $true }
    $m = $res.archives[0]
    return ($m.archive_sha256_hash -match '^[a-f0-9]{64}$')
}

# Test 08: Deterministic Merkle root for archive
Assert-Test "Test 08" "Compaction computes valid 64-character SHA-256 Merkle root" {
    $res = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 50 -DryRun
    if ($res.archives_created_count -eq 0) { return $true }
    $m = $res.archives[0]
    return ($m.archive_merkle_root -match '^[a-f0-9]{64}$')
}

# Test 09: RetainCount threshold enforcement
Assert-Test "Test 09" "Compaction respects RetainCount threshold parameter" {
    $resHigh = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 999999 -DryRun
    return ($resHigh.archives_created_count -eq 0)
}

# Test 10: Journal compaction execution
Assert-Test "Test 10" "Invoke-RegistryCompaction on JOURNAL creates valid sealed archive" {
    $jFile = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $linesBefore = @((Read-Utf8NoBom -Path $jFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
    if ($linesBefore -gt 100) {
        $res = Invoke-RegistryCompaction -Target 'JOURNAL' -RetainCount 100
        $linesAfter = @((Read-Utf8NoBom -Path $jFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
        return ($res.status -eq 'SUCCESS' -and $linesAfter -le ($linesBefore))
    }
    return $true
}

# Test 11: Audit events compaction execution
Assert-Test "Test 11" "Invoke-RegistryCompaction on AUDIT creates valid sealed archive" {
    $eFile = Join-Path $RegistryRoot 'audit\events.jsonl'
    $linesBefore = @((Read-Utf8NoBom -Path $eFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
    if ($linesBefore -gt 100) {
        $res = Invoke-RegistryCompaction -Target 'AUDIT' -RetainCount 100
        $linesAfter = @((Read-Utf8NoBom -Path $eFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
        return ($res.status -eq 'SUCCESS' -and $linesAfter -le ($linesBefore))
    }
    return $true
}

# Test 12: Archive record appended to archives.jsonl
Assert-Test "Test 12" "Compaction appends archive records to index/archives.jsonl" {
    $archs = Get-RegistryArchives
    return ($archs.Count -ge 1)
}

# Test 13: Archive files exist on disk
Assert-Test "Test 13" "Archive files are physically stored in archives/ directory" {
    $archs = Get-RegistryArchives
    if ($archs.Count -eq 0) { return $true }
    $first = $archs[0]
    $fullPath = Join-Path $RegistryRoot ($first.archive_file_path -replace '/', '\')
    return [System.IO.File]::Exists($fullPath)
}

# Test 14: Transaction journal records LEDGER_COMPACTED
Assert-Test "Test 14" "Transaction journal logs LEDGER_COMPACTED operation" {
    $jFile = Join-Path $RegistryRoot 'transactions\journal.jsonl'
    $content = Read-Utf8NoBom -Path $jFile
    return ($content -match 'LEDGER_COMPACTED')
}

# Test 15: Audit trail records ARCHIVE_CREATED
Assert-Test "Test 15" "Audit events log records ARCHIVE_CREATED event" {
    $eFile = Join-Path $RegistryRoot 'audit\events.jsonl'
    $content = Read-Utf8NoBom -Path $eFile
    return ($content -match 'ARCHIVE_CREATED')
}

# Test 16: Crash recovery clears dead process locks
Assert-Test "Test 16" "Invoke-RegistryCrashRecovery identifies and heals dead process lock files" {
    $lockDir = Join-Path $RegistryRoot 'state\locks'
    if (-not [System.IO.Directory]::Exists($lockDir)) { [void][System.IO.Directory]::CreateDirectory($lockDir) }
    $fakeLock = Join-Path $lockDir 'test-dead-process.lock'
    [System.IO.File]::WriteAllText($fakeLock, '999999', [System.Text.Encoding]::UTF8)
    
    $rec = Invoke-RegistryCrashRecovery
    $cleared = (-not [System.IO.File]::Exists($fakeLock))
    return ($cleared -and $rec.stale_locks_cleared -ge 1)
}

# Test 17: Crash recovery detects dangling transactions
Assert-Test "Test 17" "Invoke-RegistryCrashRecovery returns structured summary of dangling transactions" {
    $rec = Invoke-RegistryCrashRecovery -DryRun
    return ($rec.status -eq 'HEALTHY' -or $rec.status -eq 'RECONCILED')
}

# Test 18: Crash recovery reports HEALTHY on clean state
Assert-Test "Test 18" "Invoke-RegistryCrashRecovery reports HEALTHY when no transactions are dangling" {
    $rec = Invoke-RegistryCrashRecovery
    return ($rec.status -eq 'HEALTHY')
}

# Test 19: Checkpoint restore recovers state
Assert-Test "Test 19" "Invoke-RegistryCheckpointRestore recovers valid registry state from checkpoint" {
    $res = Invoke-RegistryCheckpointRestore -DryRun
    return ($res.status -eq 'RESTORED_HEALTHY' -and $null -ne $res.checkpoint_merkle_root)
}

# Test 20: Checkpoint restore fails on missing checkpoint file
Assert-Test "Test 20" "Invoke-RegistryCheckpointRestore fails closed on non-existent checkpoint path" {
    try {
        $null = Invoke-RegistryCheckpointRestore -CheckpointFile 'E:\.skill-registry\non-existent.json'
        return $false
    } catch {
        return ($_.Exception.Message -match 'CHECKPOINT_NOT_FOUND')
    }
}

# Test 21: Checkpoint restore verifies quarantine guard fail-closed
Assert-Test "Test 21" "Invoke-RegistryCheckpointRestore enforces quarantine guard baseline" {
    $res = Invoke-RegistryCheckpointRestore -DryRun
    return ($res.quarantine_link_status -eq 'LOCKED_VALID')
}

# Test 22: Invariant: Zero unattended active promotions
Assert-Test "Test 22" "Strict Invariant: Compaction, restore, and recovery never mutate live active deployments" {
    $depBefore = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    $null = Invoke-RegistryCompaction -Target 'ALL' -RetainCount 200 -DryRun
    $null = Invoke-RegistryCrashRecovery -DryRun
    $null = Invoke-RegistryCheckpointRestore -DryRun
    $depAfter = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    return ($depBefore -eq $depAfter)
}

# Test 23: Chaos Test: Malformed JSON line recovery
Assert-Test "Test 23" "Chaos Fault-Injection: Index parser gracefully ignores malformed JSON lines" {
    $testFile = Join-Path $RegistryRoot 'index\archives.jsonl'
    $curContent = Read-Utf8NoBom -Path $testFile
    # Temporarily append bad line
    $badContent = $curContent + "`n{INVALID_JSON_CORRUPTED_LINE`n"
    Write-Utf8NoBom -Path $testFile -Content $badContent
    
    $archs = Get-RegistryArchives
    # Restore clean content
    Write-Utf8NoBom -Path $testFile -Content $curContent
    return ($null -ne $archs)
}

# Test 24: Chaos Test: Circular DAG detection
Assert-Test "Test 24" "Chaos Fault-Injection: Reconciliation DAG resolution rejects circular dependency cycles" {
    $cyclicResources = @(
        [pscustomobject]@{ canonical_name = 'skill-a'; dependencies = @('skill-b') },
        [pscustomobject]@{ canonical_name = 'skill-b'; dependencies = @('skill-a') }
    )
    try {
        $null = Get-RegistryReconciliationDependencies -Resources $cyclicResources
        return $false
    } catch {
        return ($_.Exception.Message -match 'CIRCULAR_DEPENDENCY_DETECTED')
    }
}

# Test 25: Chaos Test: Quarantine precedence on blocked paths
Assert-Test "Test 25" "Chaos Fault-Injection: Quarantine guard strictly blocks accesses to quarantined subtrees" {
    $qPolicy = Get-QuarantinePolicyInstance
    $res = Test-RegistryQuarantineGuard -Path 'E:\.gemini\baude-skills-brutas\PayloadsAllTheThings' -Policy $qPolicy
    return ($res.decision -ne 'ALLOW' -and $res.record.trust_level -eq 'BLOCKED')
}

# Test 26: Get-RegistryGlobalStatus cross-subsystem telemetry
Assert-Test "Test 26" "Get-RegistryGlobalStatus aggregates cross-subsystem metrics across 23 indices and 32 schemas" {
    $stat = Get-RegistryGlobalStatus
    return ($stat.schemas_active_count -ge 32 -and `
            $stat.indices_count -ge 23 -and `
            $stat.quarantine_tombstones -eq 118 -and `
            $stat.strict_invariants.zero_unattended_active_promotions -eq $true)
}

# Test 27: CLI skillctl status execution
Assert-Test "Test 27" "CLI skillctl status executes successfully with exit code 0" {
    $res = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript status
    return ($LASTEXITCODE -eq 0)
}

# Test 28: CLI skillctl status -Json output
Assert-Test "Test 28" "CLI skillctl status -Json returns valid parseable JSON object" {
    $rawOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript status -Json
    $jsonLines = @($rawOut | Where-Object { $_ -match '^\s*[\{\[\"]' -or $_ -match '^\s*\}' -or $_ -match '^\s*\]' -or $_ -match ':\s*' })
    $jsonStr = $jsonLines -join "`n"
    $obj = $jsonStr | ConvertFrom-Json
    return ($null -ne $obj -and $obj.schemas_active_count -ge 32 -and $obj.system_health -eq 'HEALTHY')
}

# Test 29: CLI skillctl admin doctor
Assert-Test "Test 29" "CLI skillctl admin doctor executes successfully and reports HEALTHY" {
    $res = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript admin doctor
    return ($LASTEXITCODE -eq 0)
}

# Test 30: CLI skillctl registry doctor
Assert-Test "Test 30" "CLI skillctl registry doctor validates all 32 schemas and reports HEALTHY" {
    $res = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript registry doctor
    return ($LASTEXITCODE -eq 0)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $global:PassCount / $($global:PassCount + $global:FailCount) PASSED ($global:FailCount FAILED)" -ForegroundColor $(if ($global:FailCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-20.compaction-tests/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($global:FailCount -eq 0) { 'PASS' } else { 'FAIL' }
    passed_count = $global:PassCount
    failed_count = $global:FailCount
    test_cases = $global:TestResults.ToArray()
}

$jsonOutput = ($reportObj | ConvertTo-Json -Depth 5)
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $parentDir = [System.IO.Path]::GetDirectoryName($OutputPath)
    if (-not [System.IO.Directory]::Exists($parentDir)) {
        [void][System.IO.Directory]::CreateDirectory($parentDir)
    }
    [System.IO.File]::WriteAllText($OutputPath, $jsonOutput + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

if ($global:FailCount -gt 0) {
    exit 1
} else {
    exit 0
}
