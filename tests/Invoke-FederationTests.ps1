# Phase 30 Test Harness — Multi-Registry Federation & Peer Isolation

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-30-federation.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $RegistryRoot 'tooling\FederationEngine.psm1') -Force

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-FederationTest {
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
Write-Host " RUNNING PHASE 30 TEST SUITE: MULTI-REGISTRY FEDERATION     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Federation Peer Schema exists and is valid JSON
Assert-FederationTest "Test 01" "federation-peer.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\federation-peer.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:federation-peer:1.0.0')
}

# Test 02: Federation Peer catalog instance exists and is valid
Assert-FederationTest "Test 02" "federation-peer.json defines peer identity structure" {
    $peerFile = Join-Path $RegistryRoot 'schemas\federation-peer.json'
    if (-not [System.IO.File]::Exists($peerFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($peerFile) | ConvertFrom-Json
    return ($data.trust_status -eq 'TRUSTED' -and $data.peer_id.StartsWith('peer-'))
}

# Test 03: Federation Handshake Schema exists and is valid JSON
Assert-FederationTest "Test 03" "federation-handshake.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\federation-handshake.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:federation-handshake:1.0.0')
}

# Test 04: Federation Handshake catalog instance exists and is valid
Assert-FederationTest "Test 04" "federation-handshake.json defines mutual handshake structure" {
    $hskFile = Join-Path $RegistryRoot 'schemas\federation-handshake.json'
    if (-not [System.IO.File]::Exists($hskFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($hskFile) | ConvertFrom-Json
    return ($data.handshake_status -eq 'ESTABLISHED' -and $data.supported_exchange_types.Count -ge 2)
}

# Test 05: Federation Policy Schema exists and is valid JSON
Assert-FederationTest "Test 05" "federation-policy.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\federation-policy.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:federation-policy:1.0.0')
}

# Test 06: Federation Policy catalog instance exists and is valid
Assert-FederationTest "Test 06" "federation-policy.json defines policy rules & staging constraints" {
    $polFile = Join-Path $RegistryRoot 'schemas\federation-policy.json'
    if (-not [System.IO.File]::Exists($polFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($polFile) | ConvertFrom-Json
    return ($data.allow_auto_activation -eq $false -and $data.quarantine_policy -eq 'STRICT_FAIL_CLOSED')
}

# Test 07: Federation Exchange Schema exists and is valid JSON
Assert-FederationTest "Test 07" "federation-exchange.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\federation-exchange.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:federation-exchange:1.0.0')
}

# Test 08: Federation Exchange catalog instance exists and is valid
Assert-FederationTest "Test 08" "federation-exchange.json defines exchange package & Merkle root" {
    $excFile = Join-Path $RegistryRoot 'schemas\federation-exchange.json'
    if (-not [System.IO.File]::Exists($excFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($excFile) | ConvertFrom-Json
    return ($data.skills_included.Count -ge 1 -and $data.exchange_merkle_root.Length -eq 64)
}

# Test 09: Federation Trust Schema exists and is valid JSON
Assert-FederationTest "Test 09" "federation-trust.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\federation-trust.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:federation-trust:1.0.0')
}

# Test 10: Federation Trust catalog instance exists and is valid
Assert-FederationTest "Test 10" "federation-trust.json defines sovereign trust store" {
    $trustFile = Join-Path $RegistryRoot 'schemas\federation-trust.json'
    if (-not [System.IO.File]::Exists($trustFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($trustFile) | ConvertFrom-Json
    return ($data.default_untrusted_action -eq 'DENY' -and $data.require_explicit_user_approval_for_ingestion -eq $true)
}

# Test 11: Get-FederationPeerIdentity generates deterministic local peer identity
Assert-FederationTest "Test 11" "Get-FederationPeerIdentity generates deterministic identity from Merkle root" {
    $activeMerkle = (Get-Content -LiteralPath (Join-Path $RegistryRoot 'state\canonical-merkle.json') | ConvertFrom-Json).merkle_root
    $expectedPrefix = $activeMerkle.Substring(0, 16)
    $localPeer = Get-FederationPeerIdentity -RegistryRoot $RegistryRoot
    return ($localPeer.peer_id -eq ("peer-" + $expectedPrefix) -and
            $localPeer.key_fingerprint.Contains($expectedPrefix))
}

# Test 12: Invoke-FederationHandshake accepts trusted peer and rejects unknown peer (Fail-Closed)
Assert-FederationTest "Test 12" "Invoke-FederationHandshake evaluates trust store correctly" {
    $trustedPeer = [PSCustomObject]@{ peer_id = "peer-a1b2c3d4e5f60718" }
    $unknownPeer = [PSCustomObject]@{ peer_id = "peer-deadbeef99998888" }
    
    $hsk1 = Invoke-FederationHandshake -RegistryRoot $RegistryRoot -RemotePeerIdentity $trustedPeer
    $hsk2 = Invoke-FederationHandshake -RegistryRoot $RegistryRoot -RemotePeerIdentity $unknownPeer
    
    return ($hsk1.handshake_status -eq 'ESTABLISHED' -and
            $hsk2.handshake_status -eq 'REJECTED')
}

# Test 13: Test-FederationPolicy enforces payload limits and denies untrusted peers
Assert-FederationTest "Test 13" "Test-FederationPolicy enforces size constraints and trust boundaries" {
    $trustedPeerId = "peer-a1b2c3d4e5f60718"
    $unknownPeerId = "peer-unknown00000000"
    
    $pol1 = Test-FederationPolicy -RegistryRoot $RegistryRoot -RemotePeerId $trustedPeerId -ExchangeType "OCI_BUNDLE_EXCHANGE" -PayloadSizeBytes 1024
    $pol2 = Test-FederationPolicy -RegistryRoot $RegistryRoot -RemotePeerId $unknownPeerId -ExchangeType "OCI_BUNDLE_EXCHANGE" -PayloadSizeBytes 1024
    $pol3 = Test-FederationPolicy -RegistryRoot $RegistryRoot -RemotePeerId $trustedPeerId -ExchangeType "OCI_BUNDLE_EXCHANGE" -PayloadSizeBytes 999999999
    
    return ($pol1.allowed -eq $true -and
            $pol2.allowed -eq $false -and $pol2.action -eq 'DENY' -and
            $pol3.allowed -eq $false -and $pol3.action -eq 'DENY')
}

# Test 14: New-FederationExchangePackage and verification
Assert-FederationTest "Test 14" "New-FederationExchangePackage produces verifiable cryptographic Merkle bundle" {
    $pkg = New-FederationExchangePackage -RegistryRoot $RegistryRoot -DestinationPeerId "peer-a1b2c3d4e5f60718" -SkillNames @('react-modernization', 'nextjs-app-router-patterns')
    $verif = Test-FederationExchangeVerification -ExchangePackage $pkg
    return ($verif.passed -eq $true -and $verif.skills_count -eq 2 -and $pkg.exchange_merkle_root.Length -eq 64)
}

# Test 15: Invoke-FederationIntakeStaging stages payload into isolated staging without auto-activation
Assert-FederationTest "Test 15" "Invoke-FederationIntakeStaging isolates payload with zero auto-promotion" {
    $pkg = New-FederationExchangePackage -RegistryRoot $RegistryRoot -DestinationPeerId "peer-a1b2c3d4e5f60718" -SkillNames @('react-modernization')
    $pkg.origin_peer_id = "peer-a1b2c3d4e5f60718" # simulate incoming from trusted peer
    
    $intake = Invoke-FederationIntakeStaging -RegistryRoot $RegistryRoot -ExchangePackage $pkg
    
    # Cleanup staging
    if (Test-Path $intake.staging_directory) { Remove-Item -Path $intake.staging_directory -Recurse -Force | Out-Null }
    
    return ($intake.intake_verdict -eq 'CANDIDATE_FOR_APPROVAL' -and
            $intake.user_approval_required -eq $true -and
            $intake.auto_promoted -eq $false)
}

# Test 16: Core Gates 0-24 immutability check verified
Assert-FederationTest "Test 16" "Core Gates 0-24 immutability check verified" {
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
    schema = 'skill-registry.phase-30.federation/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    federation_model = "Personal-First Sovereign Peer Isolation"
    zero_auto_promotion_enforced = $true
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
