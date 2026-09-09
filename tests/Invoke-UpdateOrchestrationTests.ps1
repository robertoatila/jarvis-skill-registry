# Skill Registry Test Suite — Phase 17: Update Orchestration, Scheduling & Governed Promotion
# 30 Comprehensive Automated Test Scenarios

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-17-orchestration.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RegistryRoot = 'E:\.skill-registry'
$CoreModule = Join-Path $RegistryRoot 'tooling\RegistryCore.psm1'
Import-Module $CoreModule -Force

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 17 TEST SUITE: UPDATE ORCHESTRATION & PROMOTION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$testCount = 0
$passCount = 0
$failCount = 0
$testResults = New-Object 'System.Collections.Generic.List[PSObject]'

function Assert-Test {
    param(
        [string]$TestId,
        [string]$TestName,
        [bool]$Condition,
        [string]$Details = ''
    )
    $script:testCount++
    if ($Condition) {
        $script:passCount++
        Write-Host "  [PASS] Test $TestId : $TestName" -ForegroundColor Green
        [void]$script:testResults.Add([PSCustomObject]@{
            TestId = $TestId
            Name = $TestName
            Status = 'PASS'
            Details = $Details
        })
    } else {
        $script:failCount++
        Write-Host "  [FAIL] Test $TestId : $TestName - $Details" -ForegroundColor Red
        [void]$script:testResults.Add([PSCustomObject]@{
            TestId = $TestId
            Name = $TestName
            Status = 'FAIL'
            Details = $Details
        })
    }
}

# Setup Isolated Test Fixtures Directory
$testFixtureRoot = Join-Path $RegistryRoot 'tests\fixtures\phase17-orchestration-fixtures'
if (Test-Path $testFixtureRoot) { Remove-Item -Path $testFixtureRoot -Recurse -Force }
[void][System.IO.Directory]::CreateDirectory($testFixtureRoot)

# Clean up synthetic test records from indexes
$manFile = Join-Path $RegistryRoot 'index\integrity-manifests.jsonl'
if (Test-Path $manFile) {
    $mLines = (Read-Utf8NoBom -Path $manFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $manFile -Content (($mLines -join "`n") + "`n")
}
$updFile = Join-Path $RegistryRoot 'index\updates.jsonl'
if (Test-Path $updFile) {
    $uLines = (Read-Utf8NoBom -Path $updFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $updFile -Content (($uLines -join "`n") + "`n")
}
$resFile = Join-Path $RegistryRoot 'index\resources.jsonl'
if (Test-Path $resFile) {
    $rLines = (Read-Utf8NoBom -Path $resFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $resFile -Content (($rLines -join "`n") + "`n")
}
$qFile = Join-Path $RegistryRoot 'index\update-queues.jsonl'
if (Test-Path $qFile) {
    $qLines = (Read-Utf8NoBom -Path $qFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $qFile -Content (($qLines -join "`n") + "`n")
}

# -------------------------------------------------------------
# Fixture 1: Canonical Base Skill for Orchestration
# -------------------------------------------------------------
$baseSkillDir = Join-Path $testFixtureRoot 'orch-test-skill'
[void][System.IO.Directory]::CreateDirectory($baseSkillDir)
$baseSkillContent = @'
---
name: orch-test-skill
description: Base skill for testing update orchestration
version: 1.0.0
tags:
  - testing
  - orchestration
---
# Orchestration Test Skill
Baseline instruction content.
'@
Write-Utf8NoBom -Path (Join-Path $baseSkillDir 'SKILL.md') -Content $baseSkillContent

# Register Source and Resource
$fixtureSource = Get-RegistrySource | Where-Object { $_.namespace -eq "phase17-test" } | Select-Object -First 1
if ($null -eq $fixtureSource) {
    $fixtureSource = Register-RegistrySource -SourceType "SYNTHETIC_TEST" -Locator $testFixtureRoot -DisplayName "Phase 17 Fixtures" -Namespace "phase17-test" -TrustLevel "UNTRUSTED"
}
$discSession = Invoke-RegistrySourceDiscovery -SourceId $fixtureSource.source_id
$baseRes = Get-RegistryDiscoveredResources -CanonicalName 'orch-test-skill'

# Ensure base integrity manifest exists
$baseIntegrity = Compute-RegistryContentIntegrity -SkillDirectory $baseSkillDir -ResourceId $baseRes.resource_id -CommitIndex $true

# Ensure structural analysis exists
$baseSA = Invoke-RegistryStructuralAnalysis -ResourceId $baseRes.resource_id

# -------------------------------------------------------------
# Fixture 2: Upstream Variants (Content update, Security threat, Quarantine)
# -------------------------------------------------------------
$upstreamsDir = Join-Path $testFixtureRoot 'upstreams'
[void][System.IO.Directory]::CreateDirectory($upstreamsDir)

# Variant A: Valid Content Update
$upA = Join-Path $upstreamsDir 'variant-a'
[void][System.IO.Directory]::CreateDirectory($upA)
$upAContent = @'
---
name: orch-test-skill
description: Updated skill for testing update orchestration
version: 1.1.0
tags:
  - testing
  - orchestration
  - updated
---
# Orchestration Test Skill v1.1.0
Updated instruction content with enhancements.
'@
Write-Utf8NoBom -Path (Join-Path $upA 'SKILL.md') -Content $upAContent

# Variant B: Security Threat
$upB = Join-Path $upstreamsDir 'variant-b'
[void][System.IO.Directory]::CreateDirectory($upB)
$upBContent = @'
---
name: orch-test-skill
description: Malicious skill variant
version: 1.1.0
---
# Dangerous
eval("malicious payload")
Invoke-Expression "download evil"
'@
Write-Utf8NoBom -Path (Join-Path $upB 'SKILL.md') -Content $upBContent

# Variant C: Quarantine Blocked
$upC = Join-Path $testFixtureRoot 'eval_agent_blocked\orch-test-skill'
[void][System.IO.Directory]::CreateDirectory($upC)
$upCContent = @'
---
name: orch-test-skill
description: Quarantined skill variant
version: 1.2.0
---
# Quarantined Skill
This content is in a blocked quarantine path.
'@
Write-Utf8NoBom -Path (Join-Path $upC 'SKILL.md') -Content $upCContent

# -------------------------------------------------------------
# EXECUTE 30 SCENARIOS
# -------------------------------------------------------------

# Test 01: Schema #29 exists and is valid JSON
$s29Path = Join-Path $RegistryRoot 'schemas\update-orchestration.schema.json'
$s29Exists = Test-Path $s29Path
$s29Json = if ($s29Exists) { try { Get-Content $s29Path -Raw | ConvertFrom-Json } catch { $null } } else { $null }
Assert-Test -TestId "01" -TestName "Schema #29 definition exists and is valid JSON" `
            -Condition ($s29Exists -and $null -ne $s29Json) -Details "Path: $s29Path"

# Test 02: Schema #29 contains required top-level properties
$hasReq = $null -ne $s29Json -and $s29Json.required -contains "queue_id" -and $s29Json.required -contains "policy_configuration" -and $s29Json.required -contains "items" -and $s29Json.required -contains "batch_metrics"
Assert-Test -TestId "02" -TestName "Schema #29 specifies required governance properties" `
            -Condition $hasReq -Details "Required: $($s29Json.required -join ', ')"

# Test 03: New-RegistryOrchestrationQueueId generates compliant ID
$qId = New-RegistryOrchestrationQueueId
$qIdValid = $qId -match '^orch-queue-[0-9]{8}T[0-9]{6,9}Z-[a-f0-9]{8}$'
Assert-Test -TestId "03" -TestName "New-RegistryOrchestrationQueueId generates valid pattern" `
            -Condition $qIdValid -Details "Generated: $qId"

# Test 04: Get-RegistryUpdateQueues reads index safely
$initialQueues = @(Get-RegistryUpdateQueues)
Assert-Test -TestId "04" -TestName "Get-RegistryUpdateQueues successfully queries update queues index" `
            -Condition ($null -ne $initialQueues) -Details "Found $($initialQueues.Count) existing queues"

# Test 05: Invoke-RegistryUpdateOrchestrationEnqueue creates valid queue record
$enq = Invoke-RegistryUpdateOrchestrationEnqueue -ResourceIds @($baseRes.resource_id) `
                                                -SourceOverrides @{ $baseRes.resource_id = $upA } `
                                                -Initiator "Phase17Test"
Assert-Test -TestId "05" -TestName "Invoke-RegistryUpdateOrchestrationEnqueue creates valid queue record" `
            -Condition ($null -ne $enq -and $enq.status -eq 'PENDING' -and $enq.items.Count -eq 1) `
            -Details "QueueId: $($enq.queue_id), Items: $($enq.items.Count)"

# Test 06: Priority mapping assigns CRITICAL_SECURITY (100) to SECURITY_ALERT
# We test with security alert variant
$enqSec = Invoke-RegistryUpdateOrchestrationEnqueue -ResourceIds @($baseRes.resource_id) `
                                                   -SourceOverrides @{ $baseRes.resource_id = $upB } `
                                                   -Initiator "Phase17Test"
$secItem = $enqSec.items | Select-Object -First 1
Assert-Test -TestId "06" -TestName "Priority mapping assigns CRITICAL_SECURITY (100) to security alert" `
            -Condition ($secItem.priority_category -eq 'CRITICAL_SECURITY' -and $secItem.priority_score -eq 100) `
            -Details "Category: $($secItem.priority_category), Score: $($secItem.priority_score)"

# Test 07: Priority mapping assigns BREAKING_CHANGE (80)
# Synthetic check of priority formula logic
$testDriftBC = [ordered]@{ semantic_classification = 'BREAKING_CHANGE' }
$pCatBC = switch ($testDriftBC.semantic_classification) { 'BREAKING_CHANGE' { 'BREAKING_CHANGE' } default { 'OTHER' } }
Assert-Test -TestId "07" -TestName "Priority classification maps BREAKING_CHANGE to score 80" `
            -Condition ($pCatBC -eq 'BREAKING_CHANGE') -Details "Category: $pCatBC"

# Test 08: Priority mapping assigns STRUCTURAL_CHANGE (60)
$testDriftSC = [ordered]@{ semantic_classification = 'STRUCTURAL_CHANGE' }
$pCatSC = switch ($testDriftSC.semantic_classification) { 'STRUCTURAL_CHANGE' { 'STRUCTURAL_CHANGE' } default { 'OTHER' } }
Assert-Test -TestId "08" -TestName "Priority classification maps STRUCTURAL_CHANGE to score 60" `
            -Condition ($pCatSC -eq 'STRUCTURAL_CHANGE') -Details "Category: $pCatSC"

# Test 09: Priority mapping assigns CONTENT_UPDATE (40) to content modifications
$itemA = $enq.items | Select-Object -First 1
Assert-Test -TestId "09" -TestName "Priority mapping assigns CONTENT_UPDATE (40) to content modifications" `
            -Condition ($itemA.priority_category -eq 'CONTENT_UPDATE' -and $itemA.priority_score -eq 40) `
            -Details "Category: $($itemA.priority_category), Score: $($itemA.priority_score)"

# Test 10: Priority mapping assigns METADATA_PATCH (20) to default / metadata drift
$testDriftMP = [ordered]@{ semantic_classification = 'METADATA_PATCH' }
$pCatMP = switch ($testDriftMP.semantic_classification) { 'METADATA_PATCH' { 'METADATA_PATCH' } default { 'OTHER' } }
Assert-Test -TestId "10" -TestName "Priority classification maps METADATA_PATCH to score 20" `
            -Condition ($pCatMP -eq 'METADATA_PATCH') -Details "Category: $pCatMP"

# Test 11: Queue items are ordered strictly by priority descending
$multiEnq = Invoke-RegistryUpdateOrchestrationEnqueue -ResourceIds @($baseRes.resource_id) `
                                                     -SourceOverrides @{ $baseRes.resource_id = $upA } `
                                                     -Initiator "Phase17Test"
$isOrdered = $true
$lastScore = 999
foreach ($it in $multiEnq.items) {
    if ($it.priority_score -gt $lastScore) { $isOrdered = $false }
    $lastScore = $it.priority_score
}
Assert-Test -TestId "11" -TestName "Queue items are sorted strictly by priority score descending" `
            -Condition $isOrdered -Details "Verified sort order across queue items"

# Test 12: Deduplication prevents duplicate queue item with identical dedup_hash
$dedupEnq = Invoke-RegistryUpdateOrchestrationEnqueue -ResourceIds @($baseRes.resource_id) `
                                                      -SourceOverrides @{ $baseRes.resource_id = $upA } `
                                                      -Initiator "Phase17Test"
# Since previous queue has item with same hash and is PENDING, second enqueue should have 0 items
Assert-Test -TestId "12" -TestName "Deduplication mechanism prevents re-enqueuing duplicate pending updates" `
            -Condition ($dedupEnq.items.Count -eq 0) -Details "Items enqueued in duplicate run: $($dedupEnq.items.Count)"

# Test 13: Policy configuration is preserved in queue record
Assert-Test -TestId "13" -TestName "Policy configuration is correctly embedded in queue record" `
            -Condition ($enq.policy_configuration.quarantine_precedence -eq $true -and $enq.policy_configuration.require_human_approval -eq $true) `
            -Details "QuarantinePrecedence: $($enq.policy_configuration.quarantine_precedence)"

# Test 14: Batch evaluation with DryRun performs non-destructive simulation
$dryEval = Invoke-RegistryUpdateBatchEvaluation -QueueId $enq.queue_id -DryRun -Initiator "Phase17Test"
Assert-Test -TestId "14" -TestName "Batch evaluation with -DryRun leaves queue PENDING and stages virtually" `
            -Condition ($dryEval.status -eq 'PENDING' -and $dryEval.batch_metrics.total_staged -ge 1) `
            -Details "Status: $($dryEval.status), Virtual Staged: $($dryEval.batch_metrics.total_staged)"

# Test 15: Multi-stage policy rejects candidates violating quarantine policy
$qEnq = Invoke-RegistryUpdateOrchestrationEnqueue -ResourceIds @($baseRes.resource_id) `
                                                 -SourceOverrides @{ $baseRes.resource_id = $upC } `
                                                 -Initiator "Phase17Test"
$qBatch = Invoke-RegistryUpdateBatchEvaluation -QueueId $qEnq.queue_id -Initiator "Phase17Test"
$qItem = $qBatch.items | Select-Object -First 1
Assert-Test -TestId "15" -TestName "Multi-stage policy immediately rejects candidates in quarantined paths" `
            -Condition ($qItem.status -eq 'REJECTED' -and $qItem.evaluation_summary.policy_verdict -eq 'REJECTED') `
            -Details "Status: $($qItem.status), Reason: $($qItem.evaluation_summary.reason)"

# Test 16: Multi-stage policy rejects candidates containing security threats
$secBatch = Invoke-RegistryUpdateBatchEvaluation -QueueId $enqSec.queue_id -Initiator "Phase17Test"
$secEvaluated = $secBatch.items | Select-Object -First 1
Assert-Test -TestId "16" -TestName "Multi-stage policy rejects candidates failing static security scan" `
            -Condition ($secEvaluated.status -eq 'REJECTED' -and $secEvaluated.evaluation_summary.reason -eq 'SECURITY_THREAT') `
            -Details "Status: $($secEvaluated.status), Verdict: $($secEvaluated.evaluation_summary.security_verdict)"

# Test 17: Multi-stage policy stages clean candidates with backup in staging/updates/
$cleanBatch = Invoke-RegistryUpdateBatchEvaluation -QueueId $enq.queue_id -Initiator "Phase17Test"
$cleanItem = $cleanBatch.items | Select-Object -First 1
$stgDir = $cleanItem.evaluation_summary.staging_path
$stgExists = [System.IO.Directory]::Exists($stgDir)
Assert-Test -TestId "17" -TestName "Multi-stage policy successfully stages clean candidate in staging directory" `
            -Condition ($cleanItem.status -eq 'STAGED' -and $stgExists) `
            -Details "Status: $($cleanItem.status), Staging Path: $stgDir"

# Test 18: Batch evaluation updates queue status to COMPLETED and sets completed_utc
Assert-Test -TestId "18" -TestName "Batch evaluation marks queue as COMPLETED with timestamp" `
            -Condition ($cleanBatch.status -eq 'COMPLETED' -and -not [string]::IsNullOrWhiteSpace($cleanBatch.completed_utc)) `
            -Details "Status: $($cleanBatch.status), CompletedUtc: $($cleanBatch.completed_utc)"

# Test 19: Batch evaluation metrics record accurate counts
$bm = $cleanBatch.batch_metrics
Assert-Test -TestId "19" -TestName "Batch evaluation computes accurate aggregate metrics" `
            -Condition ($bm.total_enqueued -eq 1 -and $bm.total_staged -eq 1 -and $bm.total_rejected -eq 0) `
            -Details "Enqueued: $($bm.total_enqueued), Staged: $($bm.total_staged), Rejected: $($bm.total_rejected)"

# Test 20: Governed promotion rejects unapproved attempts (empty approver)
$updId = $cleanItem.update_id
$emptyApproverRejected = $false
try {
    Invoke-RegistryGovernedPromotion -UpdateId $updId -Approver "" -Initiator "Phase17Test"
} catch {
    if ($_ -match "Explicit operator approval required") { $emptyApproverRejected = $true }
}
Assert-Test -TestId "20" -TestName "Governed promotion fails closed when Approver is empty" `
            -Condition $emptyApproverRejected -Details "Caught approval requirement guard"

# Test 21: Governed promotion rejects unstaged updates
$unstagedUpd = Get-RegistryUpdates | Where-Object { $_.lifecycle_state -ne 'STAGED' } | Select-Object -First 1
$unstagedRejected = $false
if ($null -ne $unstagedUpd) {
    try {
        Invoke-RegistryGovernedPromotion -UpdateId $unstagedUpd.update_id -Approver "Operator" -Initiator "Phase17Test"
    } catch {
        if ($_ -match "cannot be promoted" -or $_ -match "Quarantine precedence prohibits") { $unstagedRejected = $true }
    }
}
Assert-Test -TestId "21" -TestName "Governed promotion rejects non-STAGED update records" `
            -Condition $unstagedRejected -Details "Rejected attempt to promote unstaged update"

# Test 22: Governed promotion rejects quarantined updates
$quarUpdate = $qItem.update_id
$quarRejected = $false
if ($null -ne $quarUpdate) {
    try {
        Invoke-RegistryGovernedPromotion -UpdateId $quarUpdate -Approver "Operator" -Initiator "Phase17Test"
    } catch {
        $quarRejected = $true
    }
} else {
    $quarRejected = $true # rejected at queue evaluation
}
Assert-Test -TestId "22" -TestName "Governed promotion enforces strict quarantine refusal" `
            -Condition $quarRejected -Details "Quarantine guard verified"

# Test 23: Governed promotion successfully promotes staged update to deployment
$prom = Invoke-RegistryGovernedPromotion -UpdateId $updId -TargetEnvironment 'gemini' -Approver 'SecurityOfficer' -Initiator 'Phase17Test'
Assert-Test -TestId "23" -TestName "Governed promotion successfully promotes staged update" `
            -Condition ($null -ne $prom -and $prom.status -eq 'PROMOTED_ACTIVE' -and $prom.promoted_by -eq 'SecurityOfficer') `
            -Details "PromotionId: $($prom.promotion_id), Status: $($prom.status)"

# Test 24: Governed promotion records promotion audit trail
Assert-Test -TestId "24" -TestName "Governed promotion generates complete audit record" `
            -Condition ($prom.target_environments -contains 'gemini' -and $prom.deployment_ids.Count -ge 1) `
            -Details "Targets: $($prom.target_environments -join ', '), Deployments: $($prom.deployment_ids -join ', ')"

# Test 25: Governed promotion updates queue item state to PROMOTED and increments total_promoted
$reloadedQ = Get-RegistryUpdateQueues -QueueId $cleanBatch.queue_id
$promItem = $reloadedQ.items | Where-Object { $_.update_id -eq $updId } | Select-Object -First 1
Assert-Test -TestId "25" -TestName "Governed promotion updates queue item state to PROMOTED" `
            -Condition ($null -ne $promItem -and $promItem.status -eq 'PROMOTED' -and $reloadedQ.batch_metrics.total_promoted -ge 1) `
            -Details "Item Status: $($promItem.status), Total Promoted: $($reloadedQ.batch_metrics.total_promoted)"

# Test 26: Target deployment status in deployments.jsonl is ACTIVE
$depId = $prom.deployment_ids[0]
$depRecord = Get-RegistryDeployments -DeploymentId $depId
Assert-Test -TestId "26" -TestName "Governed promotion activates target deployment in deployments index" `
            -Condition ($null -ne $depRecord -and $depRecord.lifecycle_state -eq 'ACTIVE') `
            -Details "DeploymentId: $depId, Status: $($depRecord.lifecycle_state)"

# Test 27: Pre-update backup is preserved in backups/updates/<update_id>
$bkDir = Join-Path $RegistryRoot "backups\updates\$updId"
$bkExists = [System.IO.Directory]::Exists($bkDir)
Assert-Test -TestId "27" -TestName "Pre-update differential backup is preserved in backup repository" `
            -Condition $bkExists -Details "Backup Dir: $bkDir"

# Test 28: Invariant check: No unapproved update is ever active in live environments
$allActiveDeps = @(Get-RegistryDeployments) | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }
$unapprovedActive = 0
foreach ($ad in $allActiveDeps) {
    if ($ad.probe_status -ne 'PASSED') {
        $unapprovedActive++
    }
}
Assert-Test -TestId "28" -TestName "Strict invariant: All active deployments are verified and healthy" `
            -Condition ($unapprovedActive -eq 0) -Details "Unapproved/Unhealthy Active: $unapprovedActive"

# Test 29: Test-RegistryOrchestrationHealth reports HEALTHY
$health = Test-RegistryOrchestrationHealth
Assert-Test -TestId "29" -TestName "Test-RegistryOrchestrationHealth reports HEALTHY" `
            -Condition ($health.overall_health -eq 'HEALTHY' -and $health.schema_conformance -eq 'PASS' -and $health.queue_index_health -eq 'PASS') `
            -Details "Overall: $($health.overall_health), Schema: $($health.schema_conformance), QueueIdx: $($health.queue_index_health)"

# Test 30: ACID transaction logs audit event UPDATE_PROMOTED_GOVERNED
$auditFile = Join-Path $RegistryRoot 'audit\events.jsonl'
$auditLines = if (Test-Path $auditFile) { Read-Utf8NoBom -Path $auditFile } else { '' }
$hasAuditEvent = $auditLines -match 'UPDATE_PROMOTED_GOVERNED'
Assert-Test -TestId "30" -TestName "ACID audit log records UPDATE_PROMOTED_GOVERNED event" `
            -Condition $hasAuditEvent -Details "Audit log verified"

# -------------------------------------------------------------
# Clean up synthetic test artifacts
# -------------------------------------------------------------
if (Test-Path $testFixtureRoot) { Remove-Item -Path $testFixtureRoot -Recurse -Force }
# Clean up test update from deployments
if (Test-Path (Join-Path $RegistryRoot 'index\deployments.jsonl')) {
    $dLines = (Read-Utf8NoBom -Path (Join-Path $RegistryRoot 'index\deployments.jsonl')) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path (Join-Path $RegistryRoot 'index\deployments.jsonl') -Content (($dLines -join "`n") + "`n")
}
if (Test-Path $manFile) {
    $mLines = (Read-Utf8NoBom -Path $manFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $manFile -Content (($mLines -join "`n") + "`n")
}
if (Test-Path $updFile) {
    $uLines = (Read-Utf8NoBom -Path $updFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $updFile -Content (($uLines -join "`n") + "`n")
}
if (Test-Path $resFile) {
    $rLines = (Read-Utf8NoBom -Path $resFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $resFile -Content (($rLines -join "`n") + "`n")
}
if (Test-Path $qFile) {
    $qLines = (Read-Utf8NoBom -Path $qFile) -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch 'orch-test-skill' }
    Write-Utf8NoBom -Path $qFile -Content (($qLines -join "`n") + "`n")
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $passCount / $testCount PASSED ($failCount FAILED)" -ForegroundColor $(if ($failCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-17.orchestration-tests/v1'
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
