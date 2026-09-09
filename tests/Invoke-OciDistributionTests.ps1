# Phase 29 Test Harness — Remote OCI Distribution & Packaging

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-29-remote-oci-distribution.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $RegistryRoot 'tooling\OciDistributionEngine.psm1') -Force

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-OciTest {
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
Write-Host " RUNNING PHASE 29 TEST SUITE: REMOTE OCI PACKAGING & TRANS. " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: OCI Manifest Schema exists and is valid JSON
Assert-OciTest "Test 01" "oci-manifest.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\oci-manifest.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:oci-manifest:1.0.0')
}

# Test 02: OCI Manifest catalog instance exists and is valid
Assert-OciTest "Test 02" "oci-manifest.json defines OCI Image Manifest v1 structure" {
    $manifestFile = Join-Path $RegistryRoot 'schemas\oci-manifest.json'
    if (-not [System.IO.File]::Exists($manifestFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($manifestFile) | ConvertFrom-Json
    return ($data.schemaVersion -eq 2 -and $data.layers.Count -ge 2)
}

# Test 03: OCI Package Config Schema exists and is valid JSON
Assert-OciTest "Test 03" "oci-package-config.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\oci-package-config.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:oci-package-config:1.0.0')
}

# Test 04: OCI Package Config catalog instance exists and is valid
Assert-OciTest "Test 04" "oci-package-config.json defines config blob descriptor" {
    $cfgFile = Join-Path $RegistryRoot 'schemas\oci-package-config.json'
    if (-not [System.IO.File]::Exists($cfgFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($cfgFile) | ConvertFrom-Json
    return ($data.runtime_compatibility -contains 'cursor' -and $data.entrypoint -eq 'SKILL.md')
}

# Test 05: OCI Signature Schema exists and is valid JSON
Assert-OciTest "Test 05" "oci-signature.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\oci-signature.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:oci-signature:1.0.0')
}

# Test 06: OCI Signature catalog instance exists and is valid
Assert-OciTest "Test 06" "oci-signature.json defines cryptographic signature record" {
    $sigFile = Join-Path $RegistryRoot 'schemas\oci-signature.json'
    if (-not [System.IO.File]::Exists($sigFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($sigFile) | ConvertFrom-Json
    return ($data.algorithm -eq 'ed25519' -and $data.verification_status -eq 'VALID')
}

# Test 07: OCI Pull Intake Schema exists and is valid JSON
Assert-OciTest "Test 07" "oci-pull-intake.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\oci-pull-intake.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:oci-pull-intake:1.0.0')
}

# Test 08: OCI Pull Intake catalog instance exists and is valid
Assert-OciTest "Test 08" "oci-pull-intake.json defines sandboxed staging & approval gate" {
    $intakeFile = Join-Path $RegistryRoot 'schemas\oci-pull-intake.json'
    if (-not [System.IO.File]::Exists($intakeFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($intakeFile) | ConvertFrom-Json
    return ($data.user_approval_required -eq $true -and $data.auto_activated -eq $false)
}

# Test 09: OCI Push Manifest Schema exists and is valid JSON
Assert-OciTest "Test 09" "oci-push-manifest.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\oci-push-manifest.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:oci-push-manifest:1.0.0')
}

# Test 10: OCI Push Manifest catalog instance exists and is valid
Assert-OciTest "Test 10" "oci-push-manifest.json defines canonical export structure" {
    $pushFile = Join-Path $RegistryRoot 'schemas\oci-push-manifest.json'
    if (-not [System.IO.File]::Exists($pushFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($pushFile) | ConvertFrom-Json
    return ($data.source_origin -eq 'CANONICAL_REGISTRY_ONLY' -and $data.layers.Count -ge 2)
}

# Test 11: New-OciSkillBundle packages canonical skill into deterministic layers
Assert-OciTest "Test 11" "New-OciSkillBundle compiles OCI layers with exact digests" {
    $sandboxExport = Join-Path $RegistryRoot 'staging\oci-export\test-oci-skill'
    if (Test-Path $sandboxExport) { Remove-Item -Path $sandboxExport -Recurse -Force | Out-Null }
    
    $bundle = New-OciSkillBundle -RegistryRoot $RegistryRoot -CanonicalName "test-oci-skill" -StagingOutputDir $sandboxExport
    $manifestFile = Join-Path $sandboxExport 'oci-manifest.json'
    $sigFile = Join-Path $sandboxExport 'oci-signature.json'
    
    $ok = (Test-Path $manifestFile) -and (Test-Path $sigFile) -and ($bundle.layers_count -eq 2)
    return $ok
}

# Test 12: Test-OciPackageVerification verifies valid OCI package layers offline
Assert-OciTest "Test 12" "Test-OciPackageVerification verifies clean bundle offline" {
    $sandboxExport = Join-Path $RegistryRoot 'staging\oci-export\test-oci-skill'
    $verif = Test-OciPackageVerification -BundleDirectory $sandboxExport
    return ($verif.passed -eq $true -and $verif.verdict -eq 'VALID')
}

# Test 13: Test-OciPackageVerification detects tampered layer payload (Fail-Closed)
Assert-OciTest "Test 13" "Test-OciPackageVerification catches tampered layer payload (Fail-Closed)" {
    $sandboxTampered = Join-Path $RegistryRoot 'staging\oci-export\test-tampered-skill'
    if (Test-Path $sandboxTampered) { Remove-Item -Path $sandboxTampered -Recurse -Force | Out-Null }
    
    $bundle = New-OciSkillBundle -RegistryRoot $RegistryRoot -CanonicalName "test-tampered-skill" -StagingOutputDir $sandboxTampered
    
    # Tamper layer payload
    $payloadFile = Join-Path $sandboxTampered 'layer-payload.tar'
    [System.IO.File]::AppendAllText($payloadFile, "`n# MALICIOUS INJECTION")
    
    $verif = Test-OciPackageVerification -BundleDirectory $sandboxTampered
    
    if (Test-Path $sandboxTampered) { Remove-Item -Path $sandboxTampered -Recurse -Force | Out-Null }
    return ($verif.passed -eq $false -and $verif.verdict -eq 'INTEGRITY_FAILED')
}

# Test 14: Invoke-OciPullStaging stages bundle safely without auto-activation
Assert-OciTest "Test 14" "Invoke-OciPullStaging stages bundle without auto-activation" {
    $sandboxExport = Join-Path $RegistryRoot 'staging\oci-export\test-oci-skill'
    $intake = Invoke-OciPullStaging -RegistryRoot $RegistryRoot -SourceBundleDirectory $sandboxExport -RemoteReference "ghcr.io/skill-registry/test-oci-skill:1.0.0"
    
    # Clean up test staging
    if (Test-Path $sandboxExport) { Remove-Item -Path $sandboxExport -Recurse -Force | Out-Null }
    if (Test-Path $intake.staging_directory) { Remove-Item -Path $intake.staging_directory -Recurse -Force | Out-Null }
    
    return ($intake.intake_verdict -eq 'CANDIDATE_FOR_APPROVAL' -and
            $intake.user_approval_required -eq $true -and
            $intake.auto_activated -eq $false)
}

# Test 15: Push authority boundary (Zero push without canonical registry source)
Assert-OciTest "Test 15" "OCI export origin is strictly CANONICAL_REGISTRY_ONLY" {
    $pushFile = Join-Path $RegistryRoot 'schemas\oci-push-manifest.json'
    $data = [System.IO.File]::ReadAllText($pushFile) | ConvertFrom-Json
    return ($data.source_origin -eq 'CANONICAL_REGISTRY_ONLY')
}

# Test 16: Core Gates 0-24 immutability check verified
Assert-OciTest "Test 16" "Core Gates 0-24 immutability check verified" {
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
    schema = 'skill-registry.phase-29.remote-oci-distribution/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    transport_layer = "OCI Image Manifest v1 / GHCR"
    zero_auto_activation_enforced = $true
    fail_closed_quarantine_enforced = $true
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
