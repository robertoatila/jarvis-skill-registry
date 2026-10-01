# Skill Registry — OCI Distribution Boundary
# Package creation and intake remain disabled until real OCI serialization, source binding,
# and a trusted signature verifier are implemented and covered by isolated tests.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

function New-OciSkillBundle {
    param(
        [string]$RegistryRoot = $(if ($env:SKILL_REGISTRY_ROOT) { $env:SKILL_REGISTRY_ROOT } else { 'E:\.skill-registry' }),
        [string]$CanonicalName,
        [string]$TargetRepository = "ghcr.io/skill-registry/$CanonicalName",
        [string]$StagingOutputDir
    )
    throw 'OCI_DISTRIBUTION_DISABLED: current code cannot create a real OCI layer or cryptographically sign it. No files were written.'
}

function Test-OciPackageVerification {
    param(
        [string]$BundleDirectory
    )
    
    $errors = New-Object 'System.Collections.Generic.List[string]'
    $manifestPath = Join-Path $BundleDirectory 'oci-manifest.json'
    $configPath = Join-Path $BundleDirectory 'config.json'
    $sigPath = Join-Path $BundleDirectory 'oci-signature.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) { return [PSCustomObject]@{ passed = $false; integrity_passed = $false; signature_verified = $false; verdict = 'MISSING_MANIFEST'; errors = @('Missing oci-manifest.json') } }
    foreach ($requiredPath in @($configPath, $sigPath, (Join-Path $BundleDirectory 'layer-payload.tar'), (Join-Path $BundleDirectory 'layer-provenance.json'))) {
        if (-not (Test-Path -LiteralPath $requiredPath)) { [void]$errors.Add("Missing component: $(Split-Path -Leaf $requiredPath)") }
    }
    if ($errors.Count -gt 0) { return [PSCustomObject]@{ passed = $false; integrity_passed = $false; signature_verified = $false; verdict = 'MISSING_COMPONENTS'; errors = $errors.ToArray() } }

    try {
        $manifest = [System.IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
        $signature = [System.IO.File]::ReadAllText($sigPath) | ConvertFrom-Json
        $actualCfgHash = 'sha256:' + (Get-Sha256FileHash -FilePath $configPath)
        if ($manifest.config.digest -ne $actualCfgHash) { [void]$errors.Add('Config digest mismatch.') }
        $payloadPath = Join-Path $BundleDirectory 'layer-payload.tar'
        $provPath = Join-Path $BundleDirectory 'layer-provenance.json'
        if ($manifest.layers.Count -lt 2) { [void]$errors.Add('Manifest must declare both payload and provenance layers.') }
        else {
            if ($manifest.layers[0].digest -ne ('sha256:' + (Get-Sha256FileHash -FilePath $payloadPath))) { [void]$errors.Add('Payload layer digest mismatch.') }
            if ($manifest.layers[1].digest -ne ('sha256:' + (Get-Sha256FileHash -FilePath $provPath))) { [void]$errors.Add('Provenance layer digest mismatch.') }
        }
        $actualManifestDigest = 'sha256:' + (Get-Sha256FileHash -FilePath $manifestPath)
        if ($signature.manifest_digest -ne $actualManifestDigest) { [void]$errors.Add('Signature descriptor manifest digest mismatch.') }
    } catch { [void]$errors.Add("Parse or read error: $($_.Exception.Message)") }

    $integrityPassed = ($errors.Count -eq 0)
    return [PSCustomObject]@{
        passed = $false
        integrity_passed = $integrityPassed
        signature_verified = $false
        signature_status = 'UNVERIFIED_NO_TRUSTED_VERIFIER'
        verdict = if ($integrityPassed) { 'INTEGRITY_MATCH_UNAUTHENTICATED' } else { 'INTEGRITY_FAILED' }
        manifest_digest = if (Test-Path -LiteralPath $manifestPath) { 'sha256:' + (Get-Sha256FileHash -FilePath $manifestPath) } else { $null }
        errors = $errors.ToArray()
        message = 'Digest consistency cannot authenticate a publisher. No trusted public key or cryptographic signature verification was performed.'
    }
}

function Invoke-OciPullStaging {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$SourceBundleDirectory,
        [string]$RemoteReference = "ghcr.io/skill-registry/imported-skill:1.0.0"
    )
    
    throw 'OCI_INTAKE_DISABLED: current verification does not authenticate publishers or establish a complete quarantine decision. No files were copied or modified.'
}

Export-ModuleMember -Function `
    Get-Sha256FileHash, `
    Get-Sha256TextHash, `
    New-OciSkillBundle, `
    Test-OciPackageVerification, `
    Invoke-OciPullStaging
