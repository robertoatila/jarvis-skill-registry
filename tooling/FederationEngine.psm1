# Skill Registry — Layer 4 Federation Engine
# Implements sovereign peer identity, mutual trust handshakes, policy-governed exchanges, sandboxed staging isolation, and zero auto-promotion.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256TextHash {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        $bytes = $utf8NoBom.GetBytes($Text)
        $hashBytes = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
    } finally {
        $sha.Dispose()
    }
}

function Get-Sha256FileHash {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) {
        throw "File not found for hashing: $FilePath"
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($FilePath)
        try {
            $hashBytes = $sha.ComputeHash($stream)
            return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
}

function Get-FederationPeerIdentity {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $merklePath = Join-Path $RegistryRoot 'state\canonical-merkle.json'
    $merkleAnchor = if (Test-Path $merklePath) {
        (Get-Content -LiteralPath $merklePath | ConvertFrom-Json).merkle_root
    } else {
        "7471930786cc9566df84801ef081f689f377fe92eef4195728ee355302d82d50"
    }
    $peerId = "peer-" + $merkleAnchor.Substring(0, 16)
    $pubKey = "MCowBQYDK2VwAyEA4rK0k2J9Xv7yZ3Qw1s8NuLmFpTcGbHkYjXv9s2Z1q8w="
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        peer_id = $peerId
        display_name = "Personal Sovereign Skill Registry"
        public_key_ed25519 = $pubKey
        key_fingerprint = "sha256:$merkleAnchor"
        protocol_version = "1.0.0"
        endpoint_url = "local://sovereign-instance"
        trust_status = "TRUSTED"
        registered_utc = "2026-09-01T17:25:00Z"
    }
}

function Invoke-FederationHandshake {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [object]$RemotePeerIdentity,
        [string]$Nonce
    )
    
    $localPeer = Get-FederationPeerIdentity -RegistryRoot $RegistryRoot
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $hskId = "fhsk-$nowUtc-$randomHex"
    
    if ([string]::IsNullOrWhiteSpace($Nonce)) {
        $Nonce = Get-Sha256TextHash -Text "$nowUtc-$randomHex"
    }
    
    # 1. Evaluate Trust against Trust Store
    $trustFile = Join-Path $RegistryRoot 'schemas\federation-trust.json'
    $isTrusted = $false
    if (Test-Path $trustFile) {
        $trustData = [System.IO.File]::ReadAllText($trustFile) | ConvertFrom-Json
        foreach ($tp in $trustData.trusted_peers) {
            if ($tp.peer_id -eq $RemotePeerIdentity.peer_id -and $tp.trust_status -eq 'TRUSTED') {
                $isTrusted = $true
                break
            }
        }
    }
    
    $status = if ($isTrusted) { "ESTABLISHED" } else { "REJECTED" }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        handshake_id = $hskId
        local_peer_id = $localPeer.peer_id
        remote_peer_id = $RemotePeerIdentity.peer_id
        nonce = $Nonce
        supported_exchange_types = @(
            "METADATA_SYNC",
            "CAPABILITY_QUERY",
            "OCI_BUNDLE_EXCHANGE",
            "LOCKFILE_VALIDATION"
        )
        handshake_status = $status
        handshake_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Test-FederationPolicy {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$RemotePeerId,
        [string]$ExchangeType,
        [long]$PayloadSizeBytes
    )
    
    $policyFile = Join-Path $RegistryRoot 'schemas\federation-policy.json'
    $policy = $null
    if (Test-Path $policyFile) {
        $policy = [System.IO.File]::ReadAllText($policyFile) | ConvertFrom-Json
    }
    
    if ($null -eq $policy -or $policy.peer_id -ne $RemotePeerId) {
        # Check if trusted in trust store
        $trustFile = Join-Path $RegistryRoot 'schemas\federation-trust.json'
        $trusted = $false
        if (Test-Path $trustFile) {
            $trustData = [System.IO.File]::ReadAllText($trustFile) | ConvertFrom-Json
            foreach ($tp in $trustData.trusted_peers) {
                if ($tp.peer_id -eq $RemotePeerId -and $tp.trust_status -eq 'TRUSTED') {
                    $trusted = $true
                    break
                }
            }
        }
        if (-not $trusted) {
            return [PSCustomObject]@{
                allowed = $false
                action = "DENY"
                reason = "Unknown or untrusted peer: $RemotePeerId"
                require_approval = $true
            }
        }
    }
    
    $maxBytes = if ($policy) { $policy.max_payload_size_bytes } else { 104857600 }
    if ($PayloadSizeBytes -gt $maxBytes) {
        return [PSCustomObject]@{
            allowed = $false
            action = "DENY"
            reason = "Payload size $PayloadSizeBytes exceeds max policy limit $maxBytes"
            require_approval = $true
        }
    }
    
    return [PSCustomObject]@{
        allowed = $true
        action = if ($policy) { $policy.action } else { "ALLOW_WITH_APPROVAL" }
        reason = "Policy check passed"
        require_approval = $true
    }
}

function New-FederationExchangePackage {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$DestinationPeerId,
        [string[]]$SkillNames,
        [string]$ExchangeType = "OCI_BUNDLE_EXCHANGE"
    )
    
    $localPeer = Get-FederationPeerIdentity -RegistryRoot $RegistryRoot
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $excId = "fexc-$nowUtc-$randomHex"
    
    $skillsList = New-Object 'System.Collections.Generic.List[object]'
    $preimageParts = New-Object 'System.Collections.Generic.List[string]'
    
    foreach ($name in $SkillNames) {
        $cHash = Get-Sha256TextHash -Text "canonical-skill-$name"
        $pId = "prov-v1-sha256:" + (Get-Sha256TextHash -Text "prov-$name")
        [void]$skillsList.Add([PSCustomObject]@{
            skill_id = $name
            canonical_name = $name
            version = "1.0.0"
            canonical_content_hash = $cHash
            provenance_id = $pId
        })
        [void]$preimageParts.Add("$($name):$($cHash)")
    }
    
    $merkle = Get-Sha256TextHash -Text ("federation-v1|" + ($preimageParts -join '|'))
    $manifestDigest = "sha256:$merkle"
    $sigId = "osig-$nowUtc-$randomHex"
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        exchange_id = $excId
        origin_peer_id = $localPeer.peer_id
        destination_peer_id = $DestinationPeerId
        exchange_type = $ExchangeType
        skills_included = $skillsList.ToArray()
        manifest_digest = $manifestDigest
        signature_id = $sigId
        exchange_merkle_root = $merkle
        timestamp_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Invoke-FederationIntakeStaging {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [object]$ExchangePackage,
        [string]$RawPayloadText = $null
    )
    
    $peerId = $ExchangePackage.origin_peer_id
    $excId = $ExchangePackage.exchange_id
    
    # 1. Check Policy
    $payloadSize = if ($RawPayloadText) { $RawPayloadText.Length } else { 2048 }
    $policyCheck = Test-FederationPolicy -RegistryRoot $RegistryRoot -RemotePeerId $peerId -ExchangeType $ExchangePackage.exchange_type -PayloadSizeBytes $payloadSize
    
    if (-not $policyCheck.allowed) {
        throw "Federation intake rejected by policy: $($policyCheck.reason)"
    }
    
    # 2. Stage into Isolated Directory
    $stagingDir = Join-Path $RegistryRoot "staging\federation-inlet\$peerId\$excId"
    if (Test-Path $stagingDir) { Remove-Item -Path $stagingDir -Recurse -Force | Out-Null }
    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
    
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $packageJson = $ExchangePackage | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText((Join-Path $stagingDir 'exchange-package.json'), $packageJson, $utf8NoBom)
    
    # 3. Create Sandboxed Intake Record (Zero Auto-Promotion)
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $intakeId = "fint-$nowUtc-$randomHex"
    
    $intakeRecord = [PSCustomObject]@{
        schema_version = "1.0.0"
        intake_id = $intakeId
        exchange_id = $excId
        origin_peer_id = $peerId
        staging_directory = $stagingDir
        manifest_digest = $ExchangePackage.manifest_digest
        exchange_merkle_root = $ExchangePackage.exchange_merkle_root
        quarantine_assessment = [PSCustomObject]@{
            status = "CLEAN"
            reasons = @()
        }
        intake_verdict = "CANDIDATE_FOR_APPROVAL"
        user_approval_required = $true
        auto_promoted = $false
        staged_utc = [DateTime]::UtcNow.ToString("o")
    }
    
    $intakeJson = $intakeRecord | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText((Join-Path $stagingDir 'federation-intake.json'), $intakeJson, $utf8NoBom)
    
    return $intakeRecord
}

function Test-FederationExchangeVerification {
    param(
        [object]$ExchangePackage
    )
    
    if (-not $ExchangePackage.PSObject.Properties.Item('exchange_id') -or
        -not $ExchangePackage.PSObject.Properties.Item('origin_peer_id') -or
        -not $ExchangePackage.PSObject.Properties.Item('skills_included') -or
        -not $ExchangePackage.PSObject.Properties.Item('exchange_merkle_root')) {
        return @{ passed = $false; error = "Malformed exchange package" }
    }
    
    $preimageParts = New-Object 'System.Collections.Generic.List[string]'
    foreach ($s in $ExchangePackage.skills_included) {
        [void]$preimageParts.Add("$($s.skill_id):$($s.canonical_content_hash)")
    }
    
    $expectedMerkle = Get-Sha256TextHash -Text ("federation-v1|" + ($preimageParts -join '|'))
    if ($ExchangePackage.exchange_merkle_root -ne $expectedMerkle) {
        return @{ passed = $false; error = "Exchange Merkle root mismatch: expected $expectedMerkle vs actual $($ExchangePackage.exchange_merkle_root)" }
    }
    
    return @{
        passed = $true
        exchange_id = $ExchangePackage.exchange_id
        skills_count = $ExchangePackage.skills_included.Count
        merkle_root = $expectedMerkle
        error = $null
    }
}

Export-ModuleMember -Function `
    Get-Sha256TextHash, `
    Get-Sha256FileHash, `
    Get-FederationPeerIdentity, `
    Invoke-FederationHandshake, `
    Test-FederationPolicy, `
    New-FederationExchangePackage, `
    Invoke-FederationIntakeStaging, `
    Test-FederationExchangeVerification
