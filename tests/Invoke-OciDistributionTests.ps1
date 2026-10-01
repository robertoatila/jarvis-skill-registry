# Safe, isolated contract tests. The legacy OCI creation and intake flows must fail closed.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$passed = 0
$failed = 0
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$fixtureRoot = Join-Path $tempBase ("jarvis-oci-test-" + [Guid]::NewGuid().ToString('N'))

function Assert-OciTest {
    param([string]$Name, [scriptblock]$Check)
    try {
        if (-not (& $Check)) { throw 'Assertion returned false.' }
        Write-Host "[PASS] $Name" -ForegroundColor Green
        $script:passed++
    } catch {
        Write-Host "[FAIL] $Name — $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

try {
    [void][System.IO.Directory]::CreateDirectory($fixtureRoot)
    $modulePath = (Resolve-Path (Join-Path $PSScriptRoot '..\tooling\OciDistributionEngine.psm1')).Path
    Import-Module $modulePath -Force

    $targetOutput = Join-Path $fixtureRoot 'must-not-be-created'
    Assert-OciTest 'OCI bundle generation stops before creating output' {
        $rejected = $false
        try { $null = New-OciSkillBundle -RegistryRoot $fixtureRoot -CanonicalName 'example-skill' -StagingOutputDir $targetOutput }
        catch { $rejected = $_.Exception.Message -like 'OCI_DISTRIBUTION_DISABLED:*' }
        $rejected -and -not (Test-Path -LiteralPath $targetOutput)
    }

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $bundlePath = Join-Path $fixtureRoot 'digest-consistency-only'
    [void][System.IO.Directory]::CreateDirectory($bundlePath)
    $configPath = Join-Path $bundlePath 'config.json'
    $payloadPath = Join-Path $bundlePath 'layer-payload.tar'
    $provenancePath = Join-Path $bundlePath 'layer-provenance.json'
    [System.IO.File]::WriteAllText($configPath, '{"example":true}', $utf8)
    [System.IO.File]::WriteAllText($payloadPath, 'not a real tar archive', $utf8)
    [System.IO.File]::WriteAllText($provenancePath, '{"example":true}', $utf8)
    $manifestPath = Join-Path $bundlePath 'oci-manifest.json'
    $manifest = [ordered]@{
        schemaVersion = 2
        mediaType = 'application/vnd.oci.image.manifest.v1+json'
        config = @{ digest = 'sha256:' + (Get-Sha256FileHash -FilePath $configPath) }
        layers = @(
            @{ digest = 'sha256:' + (Get-Sha256FileHash -FilePath $payloadPath) },
            @{ digest = 'sha256:' + (Get-Sha256FileHash -FilePath $provenancePath) }
        )
    }
    [System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 6), $utf8)
    $manifestDigest = 'sha256:' + (Get-Sha256FileHash -FilePath $manifestPath)
    [System.IO.File]::WriteAllText((Join-Path $bundlePath 'oci-signature.json'), (@{
        algorithm = 'ed25519'
        signer_identity = 'untrusted-example'
        signature_base64 = 'not-a-real-signature'
        manifest_digest = $manifestDigest
        verification_status = 'VALID'
    } | ConvertTo-Json), $utf8)

    Assert-OciTest 'Matching hashes are reported as unauthenticated, even with a forged VALID label' {
        $result = Test-OciPackageVerification -BundleDirectory $bundlePath
        $result.integrity_passed -eq $true -and $result.passed -eq $false -and $result.signature_verified -eq $false -and $result.verdict -eq 'INTEGRITY_MATCH_UNAUTHENTICATED'
    }
    Assert-OciTest 'Layer mutation is detected independently of signature status' {
        [System.IO.File]::AppendAllText($payloadPath, 'changed')
        $result = Test-OciPackageVerification -BundleDirectory $bundlePath
        $result.integrity_passed -eq $false -and $result.signature_verified -eq $false -and $result.verdict -eq 'INTEGRITY_FAILED'
    }
    Assert-OciTest 'OCI pull staging stops before copying or creating staging paths' {
        $staging = Join-Path $fixtureRoot 'staging'
        $rejected = $false
        try { $null = Invoke-OciPullStaging -RegistryRoot $fixtureRoot -SourceBundleDirectory $bundlePath }
        catch { $rejected = $_.Exception.Message -like 'OCI_INTAKE_DISABLED:*' }
        $rejected -and -not (Test-Path -LiteralPath $staging)
    }

    $signatureExample = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\schemas\oci-signature.json') -Raw | ConvertFrom-Json
    $intakeExample = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\schemas\oci-pull-intake.json') -Raw | ConvertFrom-Json
    Assert-OciTest 'Public signature and intake examples do not claim verification' {
        $signatureExample.algorithm -eq 'none' -and $signatureExample.verification_status -eq 'UNSIGNED' -and
        $intakeExample.signature_verified -eq $false -and $intakeExample.quarantine_assessment.status -eq 'SUSPECT'
    }
} finally {
    Remove-Module OciDistributionEngine -ErrorAction SilentlyContinue
    $resolvedTemp = [System.IO.Path]::GetFullPath($tempBase).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $resolvedFixture = [System.IO.Path]::GetFullPath($fixtureRoot)
    if ($resolvedFixture.StartsWith($resolvedTemp, [System.StringComparison]::OrdinalIgnoreCase) -and [System.IO.Path]::GetFileName($resolvedFixture).StartsWith('jarvis-oci-test-', [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
    }
}

Write-Host "OCI boundary tests: $passed passed; $failed failed."
if ($failed -gt 0) { exit 1 }
