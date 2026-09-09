# Skill Registry - Layer 2 Intelligence Verification Script (Baseline 143 / Batch 22)
# Audits full coverage across Layer 2 indexes without orphans or regressions (143 Active, 326 Total Resources)

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VERIFY LAYER 2 INTELLIGENCE RE-SYNC (BASELINE 143 / B22)   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$resFile = Join-Path $RegistryRoot 'index\resources.jsonl'
$capsFile = Join-Path $RegistryRoot 'index\capabilities.jsonl'
$skillsDir = Join-Path $RegistryRoot 'skills'
$merkleFile = Join-Path $RegistryRoot 'state\canonical-merkle.json'

$canonicalDirs = @(Get-ChildItem -LiteralPath $skillsDir -Directory | Select-Object -ExpandProperty Name)
$allResources = @()
foreach ($line in (Get-Content $resFile)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $obj = $line | ConvertFrom-Json
    if ($obj.PSObject.Properties['resource_id']) { $allResources += $obj }
}
$canonicalResources = @($allResources | Where-Object { $_.lifecycle_state -eq 'ACTIVE' })

$tests = [ordered]@{}

# Test 1: Structural Analyses Coverage (143/143)
$structFile = Join-Path $RegistryRoot 'index\structural-analyses.jsonl'
$structIds = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $structFile) {
    foreach ($line in (Get-Content $structFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $obj = $line | ConvertFrom-Json
        if ($obj.PSObject.Properties['resource_id']) { [void]$structIds.Add($obj.resource_id) }
    }
}
$structMissing = @($canonicalResources | Where-Object { -not $structIds.Contains($_.resource_id) })
$tests['01_StructuralAnalysisCoverage143'] = if ($structMissing.Count -eq 0 -and $canonicalResources.Count -eq 143) { 'PASS' } else { 'FAIL' }
Write-Host "  [01] Structural Analyses Coverage   : $($tests['01_StructuralAnalysisCoverage143']) (Missing: $($structMissing.Count)/143)" -ForegroundColor $(if ($structMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 2: Capability Profiles Coverage (143/143)
$profFile = Join-Path $RegistryRoot 'index\capability-profiles.jsonl'
$profIds = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $profFile) {
    foreach ($line in (Get-Content $profFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $obj = $line | ConvertFrom-Json
        if ($obj.PSObject.Properties['resource_id']) { [void]$profIds.Add($obj.resource_id) }
    }
}
$profMissing = @($canonicalResources | Where-Object { -not $profIds.Contains($_.resource_id) })
$tests['02_CapabilityProfilesCoverage143'] = if ($profMissing.Count -eq 0 -and $canonicalResources.Count -eq 143) { 'PASS' } else { 'FAIL' }
Write-Host "  [02] Capability Profiles Coverage  : $($tests['02_CapabilityProfilesCoverage143']) (Missing: $($profMissing.Count)/143)" -ForegroundColor $(if ($profMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 3: Compatibility Matrix Coverage (143/143)
$compatFile = Join-Path $RegistryRoot 'index\compatibility.jsonl'
$compatIds = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $compatFile) {
    foreach ($line in (Get-Content $compatFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $obj = $line | ConvertFrom-Json
        if ($obj.PSObject.Properties['resource_id']) { [void]$compatIds.Add($obj.resource_id) }
    }
}
$compatMissing = @($canonicalResources | Where-Object { -not $compatIds.Contains($_.resource_id) })
$tests['03_CompatibilityMatrixCoverage143'] = if ($compatMissing.Count -eq 0 -and $canonicalResources.Count -eq 143) { 'PASS' } else { 'FAIL' }
Write-Host "  [03] Compatibility Matrix Coverage : $($tests['03_CompatibilityMatrixCoverage143']) (Missing: $($compatMissing.Count)/143)" -ForegroundColor $(if ($compatMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 4: Static Security Reports Coverage (143/143)
$secFile = Join-Path $RegistryRoot 'index\security-reports.jsonl'
$secIds = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $secFile) {
    foreach ($line in (Get-Content $secFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $obj = $line | ConvertFrom-Json
        if ($obj.PSObject.Properties['resource_id']) { [void]$secIds.Add($obj.resource_id) }
    }
}
$secMissing = @($canonicalResources | Where-Object { -not $secIds.Contains($_.resource_id) })
$tests['04_SecurityReportsCoverage143'] = if ($secMissing.Count -eq 0 -and $canonicalResources.Count -eq 143) { 'PASS' } else { 'FAIL' }
Write-Host "  [04] Security Reports Coverage     : $($tests['04_SecurityReportsCoverage143']) (Missing: $($secMissing.Count)/143)" -ForegroundColor $(if ($secMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 5: Identity Clusters Full Ledger Partition (326/326)
$clusterFile = Join-Path $RegistryRoot 'index\identity-clusters.jsonl'
$clusteredMemberIds = New-Object 'System.Collections.Generic.HashSet[string]'
$totalClusters = 0
if (Test-Path $clusterFile) {
    foreach ($line in (Get-Content $clusterFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $obj = $line | ConvertFrom-Json
        if ($obj.PSObject.Properties['cluster_id']) {
            $totalClusters++
            foreach ($m in $obj.members) {
                [void]$clusteredMemberIds.Add($m.resource_id)
            }
        }
    }
}
$clusterMissing = @($allResources | Where-Object { -not $clusteredMemberIds.Contains($_.resource_id) })
$tests['05_IdentityClustersLedgerPartition326'] = if ($clusterMissing.Count -eq 0 -and $totalClusters -ge 143) { 'PASS' } else { 'FAIL' }
Write-Host "  [05] Identity Clusters Partition   : $($tests['05_IdentityClustersLedgerPartition326']) (Clusters: $totalClusters, Missing: $($clusterMissing.Count)/326)" -ForegroundColor $(if ($clusterMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 6: Invariants
$pRes = @(Get-Content $resFile | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 327
$pCaps = @(Get-Content $capsFile | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 23
$pSkills = $canonicalDirs.Count -ge 143
$activeMerkle = (Get-Content $merkleFile | ConvertFrom-Json).merkle_root
$pMerkle = ($activeMerkle -eq '8a8d2be7d354536f86d196b5d751b22450301650f81b54b93b5e746330d98d07')

$tests['06_LedgerResourcesCount327'] = if ($pRes) { 'PASS' } else { 'FAIL' }
$tests['07_CanonicalTaxonomyCount23'] = if ($pCaps) { 'PASS' } else { 'FAIL' }
$tests['08_CanonicalSkillsCount143'] = if ($pSkills) { 'PASS' } else { 'FAIL' }
$tests['09_MerkleRootImmutable'] = if ($pMerkle) { 'PASS' } else { 'FAIL' }

Write-Host "  [06] resources.jsonl = 327 lines   : $($tests['06_LedgerResourcesCount327'])" -ForegroundColor $(if ($pRes) { 'Green' } else { 'Red' })
Write-Host "  [07] capabilities.jsonl = 23 lines : $($tests['07_CanonicalTaxonomyCount23'])" -ForegroundColor $(if ($pCaps) { 'Green' } else { 'Red' })
Write-Host "  [08] skills/ = 143 canonical dirs  : $($tests['08_CanonicalSkillsCount143'])" -ForegroundColor $(if ($pSkills) { 'Green' } else { 'Red' })
Write-Host "  [09] Merkle Root Inviolado         : $($tests['09_MerkleRootImmutable']) ($activeMerkle)" -ForegroundColor $(if ($pMerkle) { 'Green' } else { 'Red' })

$allPass = $true
foreach ($k in $tests.Keys) {
    if ($tests[$k] -ne 'PASS') { $allPass = $false }
}

Write-Host "============================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host " AUDITORIA DA CAMADA 2 (B22): 100% PASS! SINCRONIZADA       " -ForegroundColor Green
} else {
    Write-Host " AUDITORIA DA CAMADA 2 (B22): FALHAS DETECTADAS!            " -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan

if (-not $allPass) { exit 1 }
