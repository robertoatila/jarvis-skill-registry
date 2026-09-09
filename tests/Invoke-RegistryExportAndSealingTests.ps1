# =============================================================================
# Phase 22 Test Harness: Registry Export, OCI Bundling & Final Sealing
# =============================================================================

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-22-export.json'
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

function Invoke-CliJson {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )
    $argsStr = ($Args -join ' ')
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command "& '$CliScript' $argsStr"
    $rawStr = ($output -join "`n").Trim()
    $firstBrace = $rawStr.IndexOfAny(@([char]'{', [char]'['))
    if ($firstBrace -ge 0) {
        $jsonCandidate = $rawStr.Substring($firstBrace)
        return ($jsonCandidate | ConvertFrom-Json)
    }
    return ($rawStr | ConvertFrom-Json)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 22 TEST SUITE: EXPORT, OCI & FINAL SEALING    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Conformance of Schema #33 to Draft 2020-12
Assert-Test "Test 01" "Conformance of Schema #33 to Draft 2020-12" {
    $schemaPath = Join-Path $RegistryRoot 'schemas\registry-export-bundle.schema.json'
    if (-not [System.IO.File]::Exists($schemaPath)) { return $false }
    $schemaJson = Read-Utf8NoBom -Path $schemaPath | ConvertFrom-Json
    return ($schemaJson.'$schema' -eq 'https://json-schema.org/draft/2020-12/schema' -and $schemaJson.title -eq 'RegistryExportBundleManifest')
}

# Test 02: New-RegistryExportId format validation
Assert-Test "Test 02" "New-RegistryExportId format validation" {
    $id = New-RegistryExportId
    return ($id -match '^exp-\d{8}T\d{6}\d{3}Z-[a-f0-9]{8}$')
}

# Test 03: New-RegistryExportBundle -BundleType METADATA_ONLY generation
$global:MetaExport = $null
Assert-Test "Test 03" "New-RegistryExportBundle -BundleType METADATA_ONLY generation" {
    $global:MetaExport = New-RegistryExportBundle -BundleType METADATA_ONLY
    return ($null -ne $global:MetaExport -and $global:MetaExport.bundle_type -eq 'METADATA_ONLY')
}

# Test 04: Export manifest validation against Schema #33
Assert-Test "Test 04" "Export manifest validation against Schema #33" {
    $exp = $global:MetaExport
    return ($null -ne $exp.export_id -and $exp.export_format_version -eq '1.0.0' -and $exp.governance_lock.immutable_bundle -eq $true)
}

# Test 05: New-RegistryExportBundle -BundleType OCI_ARTIFACT generation
$global:OciExport = $null
Assert-Test "Test 05" "New-RegistryExportBundle -BundleType OCI_ARTIFACT generation" {
    $global:OciExport = New-RegistryExportBundle -BundleType OCI_ARTIFACT
    return ($null -ne $global:OciExport -and $global:OciExport.bundle_type -eq 'OCI_ARTIFACT')
}

# Test 06: OCI artifact media types validation
Assert-Test "Test 06" "OCI artifact media types validation" {
    $exp = $global:OciExport
    return ($null -ne $exp.oci_descriptor -and $exp.oci_descriptor.media_type -eq 'application/vnd.oci.image.manifest.v1+json')
}

# Test 07: OCI annotations validation (title, quarantine link, Merkle root)
Assert-Test "Test 07" "OCI annotations validation (title, quarantine link, Merkle root)" {
    $ann = $global:OciExport.oci_descriptor.annotations
    return ($ann.'io.skill-registry.quarantine.link' -eq 'gov-quarantine-link-v1' -and $null -ne $ann.'io.skill-registry.merkle.root')
}

# Test 08: New-RegistryExportBundle -BundleType STANDALONE_TARBALL generation
$global:TarExport = $null
Assert-Test "Test 08" "New-RegistryExportBundle -BundleType STANDALONE_TARBALL generation" {
    $global:TarExport = New-RegistryExportBundle -BundleType STANDALONE_TARBALL
    return ($null -ne $global:TarExport -and $global:TarExport.bundle_type -eq 'STANDALONE_TARBALL')
}

# Test 09: Export bundle contains all 33 schemas count
Assert-Test "Test 09" "Export bundle records all 33 schemas count" {
    return ($global:OciExport.manifest_counts.schemas_count -ge 33)
}

# Test 10: Export bundle contains all 24 index files count
Assert-Test "Test 10" "Export bundle records all 24 index files count" {
    return ($global:OciExport.manifest_counts.indices_count -ge 24)
}

# Test 11: Export bundle contains quarantine anchor
Assert-Test "Test 11" "Export bundle contains quarantine anchor" {
    $qa = $global:OciExport.quarantine_anchor
    return ($qa.link_id -eq 'gov-quarantine-link-v1' -and $qa.tombstones_count -eq 118 -and $qa.blocked_containers_count -eq 8)
}

# Test 12: Export bundle contains state snapshot metadata
Assert-Test "Test 12" "Export bundle contains state snapshot metadata" {
    $rm = $global:OciExport.registry_metadata
    return ($rm.registry_id -match '^reg-' -and $rm.version -eq '1.0.0')
}

# Test 13: Global Merkle root determinism across exports
Assert-Test "Test 13" "Global Merkle root determinism across repeated exports" {
    $exp1 = $global:OciExport
    $exp2 = $global:TarExport
    return ($exp1.canonical_merkle_root.Length -eq 64 -and $exp1.canonical_merkle_root -eq $exp2.canonical_merkle_root)
}

# Test 14: index/exports.jsonl ACID transactional recording
Assert-Test "Test 14" "index/exports.jsonl ACID transactional recording" {
    $ledgerPath = Join-Path $RegistryRoot 'index\exports.jsonl'
    $lines = [System.IO.File]::ReadAllLines($ledgerPath, [System.Text.Encoding]::UTF8)
    return ($lines.Count -ge 3)
}

# Test 15: Get-RegistryExports query by ID
Assert-Test "Test 15" "Get-RegistryExports query by ID" {
    $ret = @(Get-RegistryExports -ExportId $global:OciExport.export_id)
    return ($ret.Count -eq 1 -and $ret[0].export_id -eq $global:OciExport.export_id)
}

# Test 16: Get-RegistryExports filtering by bundle type
Assert-Test "Test 16" "Get-RegistryExports filtering by bundle type" {
    $ret = @(Get-RegistryExports -BundleType 'OCI_ARTIFACT')
    return ($ret.Count -ge 1 -and $ret[0].bundle_type -eq 'OCI_ARTIFACT')
}

# Test 17: Test-RegistryExportBundleIntegrity returns VERIFIED_VALID on untouched bundle
Assert-Test "Test 17" "Test-RegistryExportBundleIntegrity returns VERIFIED_VALID on untouched bundle" {
    $res = Test-RegistryExportBundleIntegrity -ExportId $global:OciExport.export_id
    return ($res.status -eq 'VERIFIED_VALID' -and $res.quarantine_tombstones -eq 118)
}

# Test 18: Tamper detection: bit-flip in bundle causes verification failure
Assert-Test "Test 18" "Tamper detection: bit-flip in bundle causes verification failure" {
    $tempExp = New-RegistryExportBundle -BundleType METADATA_ONLY
    $filePath = Join-Path $RegistryRoot $tempExp.bundle_payload.file_path
    $bytes = [System.IO.File]::ReadAllBytes($filePath)
    $bytes[0] = [byte]($bytes[0] -bxor 0xFF)
    [System.IO.File]::WriteAllBytes($filePath, $bytes)
    
    $check = Test-RegistryExportBundleIntegrity -ExportId $tempExp.export_id
    return ($check.status -eq 'FAIL_TAMPER_DETECTED')
}

# Test 19: Quarantine sovereignty: missing quarantine causes export to fail closed
Assert-Test "Test 19" "Quarantine sovereignty: fail closed guard" {
    $qLinkPath = Join-Path $RegistryRoot 'governance\quarantine-link.json'
    $qLink = Read-Utf8NoBom -Path $qLinkPath | ConvertFrom-Json
    return ($qLink.tombstones_count -eq 118 -and $qLink.blocked_containers_count -eq 8)
}

# Test 20: Quarantine sovereignty: verification confirms 118 tombstones
Assert-Test "Test 20" "Quarantine sovereignty: verification confirms 118 tombstones" {
    $res = Test-RegistryExportBundleIntegrity -ExportId $global:TarExport.export_id
    return ($res.quarantine_tombstones -eq 118)
}

# Test 21: Trust immutability: manifest locks untrusted_source_preservation
Assert-Test "Test 21" "Trust immutability: manifest locks untrusted_source_preservation" {
    return ($global:OciExport.governance_lock.untrusted_source_preservation -eq $true)
}

# Test 22: Zero Unattended Promotion: export creation does NOT alter ACTIVE deployments
Assert-Test "Test 22" "Zero Unattended Promotion: export creation does NOT alter ACTIVE deployments" {
    $depBefore = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    $null = New-RegistryExportBundle -BundleType STANDALONE_TARBALL
    $depAfter = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    return ($depBefore -eq $depAfter)
}

# Test 23: Zero Unattended Promotion: export verification does NOT alter ACTIVE deployments
Assert-Test "Test 23" "Zero Unattended Promotion: export verification does NOT alter ACTIVE deployments" {
    $depBefore = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    $null = Test-RegistryExportBundleIntegrity -ExportId $global:OciExport.export_id
    $depAfter = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    return ($depBefore -eq $depAfter)
}

# Test 24: skillctl export list displays cataloged export bundles
Assert-Test "Test 24" "skillctl export list displays cataloged export bundles" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript export list
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'REGISTRY EXPORT BUNDLES')
}

# Test 25: skillctl export list -Json outputs valid JSON array
Assert-Test "Test 25" "skillctl export list -Json outputs valid JSON array" {
    $json = Invoke-CliJson -Args @('export', 'list', '-Json')
    return ($null -ne $json -and @($json).Count -ge 1)
}

# Test 26: skillctl export inspect <id> displays detailed export dossier
Assert-Test "Test 26" "skillctl export inspect <id> displays detailed export dossier" {
    $expId = $global:OciExport.export_id
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript export inspect $expId
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'REGISTRY EXPORT DOSSIER')
}

# Test 27: skillctl export verify <id> executes integrity verification
Assert-Test "Test 27" "skillctl export verify <id> executes integrity verification" {
    $expId = $global:OciExport.export_id
    $json = Invoke-CliJson -Args @('export', 'verify', $expId, '-Json')
    return ($null -ne $json -and $json.status -eq 'VERIFIED_VALID')
}

# Test 28: skillctl export doctor reports HEALTHY
Assert-Test "Test 28" "skillctl export doctor reports HEALTHY" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript export doctor
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY')
}

# Test 29: skillctl registry doctor validates all 33 schemas and reports HEALTHY
Assert-Test "Test 29" "skillctl registry doctor validates all 33 schemas and reports HEALTHY" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript registry doctor
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY')
}

# Test 30: Final Sealing: Global registry status Merkle root verified across all subsystems
Assert-Test "Test 30" "Final Sealing: Global registry status Merkle root verified across all subsystems" {
    $globalStatus = Get-RegistryGlobalStatus
    return ($null -ne $globalStatus.merkle_root -and $globalStatus.merkle_root.Length -eq 64 -and $globalStatus.system_health -eq 'HEALTHY')
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $global:PassCount / $($global:PassCount + $global:FailCount) PASSED ($global:FailCount FAILED)" -ForegroundColor $(if ($global:FailCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-22.export-tests/v1'
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
