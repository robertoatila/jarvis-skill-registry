# Skill Registry - Layer 2 Intelligence Re-Sync Verification Script
# Audits full coverage across Layer 2 indexes without orphans or regressions (Baseline 137 / B21)

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VERIFY LAYER 2 INTELLIGENCE RE-SYNC (BASELINE 137 / B21)   " -ForegroundColor Cyan
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

# Test 1: Structural Analyses Coverage (137/137)
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
$tests['01_StructuralAnalysisCoverage137'] = if ($structMissing.Count -eq 0) { 'PASS' } else { 'FAIL' }
Write-Host "  [01] Structural Analyses Coverage   : $($tests['01_StructuralAnalysisCoverage137']) (Missing: $($structMissing.Count)/137)" -ForegroundColor $(if ($structMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 2: Capability Profiles Coverage (137/137)
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
$tests['02_CapabilityProfilesCoverage137'] = if ($profMissing.Count -eq 0) { 'PASS' } else { 'FAIL' }
Write-Host "  [02] Capability Profiles Coverage  : $($tests['02_CapabilityProfilesCoverage137']) (Missing: $($profMissing.Count)/137)" -ForegroundColor $(if ($profMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 3: Compatibility Matrix Coverage (137/137)
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
$tests['03_CompatibilityMatrixCoverage137'] = if ($compatMissing.Count -eq 0) { 'PASS' } else { 'FAIL' }
Write-Host "  [03] Compatibility Matrix Coverage : $($tests['03_CompatibilityMatrixCoverage137']) (Missing: $($compatMissing.Count)/137)" -ForegroundColor $(if ($compatMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 4: Static Security Reports Coverage (137/137)
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
$tests['04_SecurityReportsCoverage137'] = if ($secMissing.Count -eq 0) { 'PASS' } else { 'FAIL' }
Write-Host "  [04] Security Reports Coverage     : $($tests['04_SecurityReportsCoverage137']) (Missing: $($secMissing.Count)/137)" -ForegroundColor $(if ($secMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 5: Identity Clusters Full Ledger Partition (320/320)
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
$tests['05_IdentityClustersLedgerPartition320'] = if ($clusterMissing.Count -eq 0 -and $totalClusters -ge 137) { 'PASS' } else { 'FAIL' }
Write-Host "  [05] Identity Clusters Partition   : $($tests['05_IdentityClustersLedgerPartition320']) (Clusters: $totalClusters, Missing: $($clusterMissing.Count)/320)" -ForegroundColor $(if ($clusterMissing.Count -eq 0) { 'Green' } else { 'Red' })

# Test 6: Invariants
$pRes = @(Get-Content $resFile | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 321
$pCaps = @(Get-Content $capsFile | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 23
$pSkills = $canonicalDirs.Count -eq 137
$activeMerkle = (Get-Content $merkleFile | ConvertFrom-Json).merkle_root
$pMerkle = ($activeMerkle -eq 'bd1a5b7dfb1f45b2135aa56a2f8727f1390d83c3766023915a83f6bd22aa83a4')

$tests['06_LedgerResourcesCount321'] = if ($pRes) { 'PASS' } else { 'FAIL' }
$tests['07_CanonicalTaxonomyCount23'] = if ($pCaps) { 'PASS' } else { 'FAIL' }
$tests['08_CanonicalSkillsCount137'] = if ($pSkills) { 'PASS' } else { 'FAIL' }
$tests['09_MerkleRootImmutable'] = if ($pMerkle) { 'PASS' } else { 'FAIL' }

Write-Host "  [06] resources.jsonl = 321 lines   : $($tests['06_LedgerResourcesCount321'])" -ForegroundColor $(if ($pRes) { 'Green' } else { 'Red' })
Write-Host "  [07] capabilities.jsonl = 23 lines : $($tests['07_CanonicalTaxonomyCount23'])" -ForegroundColor $(if ($pCaps) { 'Green' } else { 'Red' })
Write-Host "  [08] skills/ = 137 canonical dirs  : $($tests['08_CanonicalSkillsCount137'])" -ForegroundColor $(if ($pSkills) { 'Green' } else { 'Red' })
Write-Host "  [09] Merkle Root Inviolado         : $($tests['09_MerkleRootImmutable']) ($activeMerkle)" -ForegroundColor $(if ($pMerkle) { 'Green' } else { 'Red' })

$allPass = $true
foreach ($k in $tests.Keys) {
    if ($tests[$k] -ne 'PASS') { $allPass = $false }
}

Write-Host "============================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host " AUDITORIA DA CAMADA 2 (B21): 100% PASS! SINCRONIZADA       " -ForegroundColor Green
} else {
    Write-Host " AUDITORIA DA CAMADA 2 (B21): FALHAS DETECTADAS!            " -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan

if (-not $allPass) { exit 1 }
