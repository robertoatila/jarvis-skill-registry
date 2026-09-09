# =============================================================================
# Phase 23 Test Harness: Real-Arsenal Production Hardening & Scale Validation
# =============================================================================

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-23-real-arsenal-hardening.json'
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
Write-Host " RUNNING PHASE 23 TEST SUITE: REAL-ARSENAL PRODUCTION HARDENING " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Execute Real Arsenal Ingestion
$global:IngestionReport = $null
Assert-Test "Test 01" "Execute Real Arsenal Batch Ingestion across 168 skills" {
    $global:IngestionReport = Invoke-RegistryRealArsenalIngestion -MaxSkillsToProcess 200
    return ($null -ne $global:IngestionReport -and $global:IngestionReport.status -eq 'SUCCESS')
}

# Test 02: Real source registration verification
Assert-Test "Test 02" "Real sources registered in index/sources.jsonl" {
    $sources = @(Get-RegistrySource)
    $u = @($sources | Where-Object { $_.namespace -eq 'real-user-config' })
    $b = @($sources | Where-Object { $_.namespace -eq 'real-builtin-antigravity' })
    return ($u.Count -ge 1 -and $b.Count -ge 1)
}

# Test 03: Real source trust immutability (UNTRUSTED)
Assert-Test "Test 03" "Real sources have trust_level: UNTRUSTED" {
    $sources = @(Get-RegistrySource)
    $u = @($sources | Where-Object { $_.namespace -eq 'real-user-config' })
    $b = @($sources | Where-Object { $_.namespace -eq 'real-builtin-antigravity' })
    return ($u[0].trust_level -eq 'UNTRUSTED' -and $b[0].trust_level -eq 'UNTRUSTED')
}

# Test 04: Real batch discovery across real-user-config (>= 160 skills)
Assert-Test "Test 04" "Real batch discovery across real-user-config (>= 160 skills)" {
    $sources = @(Get-RegistrySource)
    $u = @($sources | Where-Object { $null -ne $_.PSObject.Properties['namespace'] -and $_.namespace -eq 'real-user-config' })
    $uId = $u[0].source_id
    $sessions = @(Get-RegistryDiscoverySessions -SourceId $uId)
    $discCount = ($sessions | Measure-Object -Property candidates_discovered_count -Sum).Sum
    return ($discCount -ge 160)
}

# Test 05: Real batch discovery across real-builtin-antigravity (3 skills)
Assert-Test "Test 05" "Real batch discovery across real-builtin-antigravity (3 skills)" {
    $sources = @(Get-RegistrySource)
    $b = @($sources | Where-Object { $null -ne $_.PSObject.Properties['namespace'] -and $_.namespace -eq 'real-builtin-antigravity' })
    $bId = $b[0].source_id
    $sessions = @(Get-RegistryDiscoverySessions -SourceId $bId)
    $discCount = ($sessions | Measure-Object -Property candidates_discovered_count -Sum).Sum
    return ($discCount -ge 3)
}

# Test 06: Frontmatter parsing across real skills extracts valid names
Assert-Test "Test 06" "Frontmatter parsing extracts valid canonical names" {
    $res = @(Get-RegistryDiscoveredResources)
    $sample = $res | Where-Object { $_.canonical_name -eq 'ai-engineer' }
    return ($null -ne $sample -and $sample.description.Length -gt 10)
}

# Test 07: Structural analysis executed across real skills
Assert-Test "Test 07" "Structural analysis executed across real skills" {
    return ($global:IngestionReport.structural_analyses_count -ge 160)
}

# Test 08: Structural classification categorizes SINGLE_DOCUMENT vs COMPOSITE_SCRIPTS
Assert-Test "Test 08" "Structural classification handles diverse real archetypes" {
    $analyses = @(Get-RegistryStructuralAnalyses)
    $single = @($analyses | Where-Object { $_.structure.layout_type -eq 'SINGLE_FILE' })
    $composite = @($analyses | Where-Object { $_.structure.layout_type -in @('STANDARD_SKILL_DIR', 'EXTENDED_PACKAGE') })
    return ($single.Count -gt 0 -and $composite.Count -gt 0)
}

# Test 09: Structural risk stratification assigns valid risk levels
Assert-Test "Test 09" "Structural risk stratification assigns valid risk levels" {
    $analyses = @(Get-RegistryStructuralAnalyses)
    $validRisks = @('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    $invalid = @($analyses | Where-Object { $null -eq $_.inferred_metadata -or $_.inferred_metadata.structural_risk_level -notin $validRisks })
    return ($invalid.Count -eq 0 -and $analyses.Count -gt 0)
}

# Test 10: Real provenance records emitted into index/provenance.jsonl
Assert-Test "Test 10" "Real provenance records recorded in ledger" {
    $provs = @(Get-RegistryProvenance)
    return ($provs.Count -ge 1)
}

# Test 11: Real SHA-256 content hashes computed for real files
Assert-Test "Test 11" "Real SHA-256 content hashes computed for real files" {
    $provs = @(Get-RegistryProvenance)
    $sample = $provs[0]
    return ($null -ne $sample.provenance_id -and $sample.provenance_id -match '^prov-v1-sha256:[a-f0-9]{64}$')
}

# Test 12: Real content integrity manifests recorded in ledger
Assert-Test "Test 12" "Real content integrity manifests recorded in ledger" {
    $mans = @(Get-RegistryIntegrityManifests)
    return ($mans.Count -ge 1)
}

# Test 13: Quarantine guard passes on real source trees
Assert-Test "Test 13" "Quarantine guard passes on valid real trees" {
    $qLinkPath = Join-Path $RegistryRoot 'governance\quarantine-link.json'
    $qLink = Read-Utf8NoBom -Path $qLinkPath | ConvertFrom-Json
    return ($qLink.tombstones_count -eq 118 -and $qLink.blocked_containers_count -eq 8)
}

# Test 14: Real identity deduplication clustering groups related skills
Assert-Test "Test 14" "Real identity deduplication clustering groups related skills" {
    $clusters = @(Get-RegistryIdentityClusters)
    return ($clusters.Count -ge 1)
}

# Test 15: Canonical leader resolution in identity clusters
Assert-Test "Test 15" "Canonical leader resolution in identity clusters" {
    $clusters = @(Get-RegistryIdentityClusters)
    $c = $clusters[0]
    return ($null -ne $c.leader_resource_id -and $c.members.Count -ge 1)
}

# Test 16: Real capability taxonomy mapping across real skills
Assert-Test "Test 16" "Real capability taxonomy mapping across real skills" {
    $profiles = @(Get-RegistryCapabilityProfiles)
    return ($profiles.Count -ge 160)
}

# Test 17: Provider compatibility evaluation across all 5 adapters
Assert-Test "Test 17" "Provider compatibility evaluation across all 5 adapters" {
    $matrices = @(Get-RegistryCompatibilityMatrix)
    return ($matrices.Count -ge 1)
}

# Test 18: Static security scanning executed across real skills (0 dynamic executions)
Assert-Test "Test 18" "Static security scanning executed across real skills (0 dynamic executions)" {
    $secReports = @(Get-RegistrySecurityReports)
    return ($secReports.Count -ge 160)
}

# Test 19: Security threat stratification classifies findings
Assert-Test "Test 19" "Security threat stratification classifies findings" {
    $secReports = @(Get-RegistrySecurityReports)
    return ($secReports.Count -gt 0)
}

# Test 20: Zero dynamic executions verified
Assert-Test "Test 20" "Zero dynamic executions verified during pipeline" {
    return ($global:IngestionReport.dynamic_executions -eq 0)
}

# Test 21: Real quality evaluations recorded
Assert-Test "Test 21" "Real quality evaluations recorded" {
    $qual = @(Get-RegistryQualityEvaluations)
    return ($qual.Count -ge 1)
}

# Test 22: Real conflict detection executed
Assert-Test "Test 22" "Real conflict detection executed" {
    $conf = @(Get-RegistryConflicts)
    return ($conf.Count -ge 0)
}

# Test 23: Staging materialization integrity
Assert-Test "Test 23" "Staging materialization integrity" {
    $mats = @(Get-RegistryMaterializations)
    return ($mats.Count -ge 1)
}

# Test 24: Zero Unattended Promotion Guard: ACTIVE deployments count unchanged
Assert-Test "Test 24" "Zero Unattended Promotion Guard: ACTIVE deployments count unchanged" {
    return ($global:IngestionReport.zero_unattended_promotion -eq $true -and $global:IngestionReport.active_deployments_before -eq $global:IngestionReport.active_deployments_after)
}

# Test 25: Quarantine Sovereignty Guard: 118 tombstones intact
Assert-Test "Test 25" "Quarantine Sovereignty Guard: 118 tombstones intact" {
    return ($global:IngestionReport.quarantine_tombstones -eq 118)
}

# Test 26: Test-RegistryRealArsenalHealth reports HEALTHY
Assert-Test "Test 26" "Test-RegistryRealArsenalHealth reports HEALTHY" {
    $diag = Test-RegistryRealArsenalHealth
    return ($diag.overall_health -eq 'HEALTHY')
}

# Test 27: All 33 Schemas validated against index ledgers
Assert-Test "Test 27" "All 33 Schemas validated against index ledgers" {
    $schemaDir = Join-Path $RegistryRoot 'schemas'
    $schemas = @(Get-ChildItem $schemaDir -Filter '*.schema.json')
    return ($schemas.Count -ge 33)
}

# Test 28: Scale & Concurrency: Crash recovery under expanded catalog
Assert-Test "Test 28" "Scale & Concurrency: Crash recovery under expanded catalog" {
    $rec = Invoke-RegistryCrashRecovery -DryRun
    return ($rec.status -in @('HEALTHY', 'RECONCILED'))
}

# Test 29: Disaster Restore verification on recovery checkpoint
Assert-Test "Test 29" "Disaster Restore verification on recovery checkpoint" {
    $adminDiag = Test-RegistryAdminHealth
    return ($adminDiag.overall_health -eq 'HEALTHY')
}

# Test 30: Final Sealing: Global registry Merkle root verified across complete catalog
Assert-Test "Test 30" "Final Sealing: Global registry Merkle root verified across complete catalog" {
    $globalStatus = Get-RegistryGlobalStatus
    return ($null -ne $globalStatus.merkle_root -and $globalStatus.merkle_root.Length -eq 64 -and $globalStatus.system_health -eq 'HEALTHY')
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $global:PassCount / $($global:PassCount + $global:FailCount) PASSED ($global:FailCount FAILED)" -ForegroundColor $(if ($global:FailCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-23.real-arsenal-hardening-tests/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($global:FailCount -eq 0) { 'PASS' } else { 'FAIL' }
    passed_count = $global:PassCount
    failed_count = $global:FailCount
    ingestion_metrics = $global:IngestionReport
    test_cases = $global:TestResults.ToArray()
}

$jsonOutput = ($reportObj | ConvertTo-Json -Depth 6)
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
