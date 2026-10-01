# Safe, isolated contract tests for metadata-only registry exports.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$passed = 0
$failed = 0
$oldRegistryRoot = $env:SKILL_REGISTRY_ROOT
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$fixtureRoot = Join-Path $tempBase ("jarvis-export-test-" + [Guid]::NewGuid().ToString('N'))

function Assert-ExportTest {
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
    foreach ($directory in @('schemas', 'governance', 'config', 'state', 'index', 'audit', 'transactions', 'exports')) {
        [void][System.IO.Directory]::CreateDirectory((Join-Path $fixtureRoot $directory))
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $fixtureRoot 'schemas\registry-export-bundle.schema.json'), '{"title":"RegistryMetadataExportManifest","properties":{"export_format_version":{"const":"2.0.0"}}}', $utf8)
    [System.IO.File]::WriteAllText((Join-Path $fixtureRoot 'governance\quarantine-link.json'), '{"link_id":"test-link","snapshot_id":"test-snapshot","tombstones_count":118,"blocked_containers_count":8}', $utf8)
    [System.IO.File]::WriteAllText((Join-Path $fixtureRoot 'config\registry.json'), '{"registry_id":"reg-test","registry_name":"Test Registry","version":"0.0.0","mode":"test"}', $utf8)
    [System.IO.File]::WriteAllText((Join-Path $fixtureRoot 'state\current-state.json'), '{}', $utf8)
    foreach ($index in @('exports.jsonl', 'deployments.jsonl', 'sources.jsonl', 'resources.jsonl')) {
        [System.IO.File]::WriteAllText((Join-Path $fixtureRoot "index\$index"), '', $utf8)
    }

    $env:SKILL_REGISTRY_ROOT = $fixtureRoot
    $modulePath = (Resolve-Path (Join-Path $PSScriptRoot '..\tooling\RegistryCore.psm1')).Path
    Import-Module $modulePath -Force

    $manifest = New-RegistryExportBundle
    $payloadPath = Join-Path $fixtureRoot $manifest.bundle_payload.file_path
    $payload = [System.IO.File]::ReadAllText($payloadPath) | ConvertFrom-Json
    Assert-ExportTest 'Default export is a parseable metadata-only JSON document' {
        $manifest.bundle_type -eq 'METADATA_ONLY' -and $manifest.export_format_version -eq '2.0.0' -and $payload.document_type -eq 'skill-registry-metadata-export'
    }
    Assert-ExportTest 'Export does not claim signature or Merkle verification' {
        $manifest.trust.signature_verified -eq $false -and $manifest.trust.canonical_merkle_verified -eq $false -and $manifest.catalog_snapshot.algorithm -like 'SHA-256*'
    }
    Assert-ExportTest 'Health output distinguishes header checks from schema validation and authenticity' {
        $health = Test-RegistryExportHealth
        $health.overall_health -eq 'LIMITED' -and
            $health.schema_descriptor_status -eq 'HEADER_FIELDS_MATCH' -and
            $health.schema_validation -eq 'NOT_RUN' -and
            $health.exports_ledger_status -eq 'PRESENT_NOT_VALIDATED' -and
            $health.quarantine_anchor_status -eq 'COUNTS_MATCH_NOT_AUTHENTICATED' -and
            $health.signature_verification -eq 'NOT_IMPLEMENTED'
    }
    Assert-ExportTest 'Local checks report consistency without authenticity' {
        $verification = Test-RegistryExportBundleIntegrity -ExportId $manifest.export_id
        $verification.status -eq 'CONTENT_CHECKS_MATCH' -and $verification.signature_verified -eq $false -and $verification.authenticity_established -eq $false
    }
    Assert-ExportTest 'OCI and tar requests fail before writing files' {
        $beforeLedger = [System.IO.File]::ReadAllText((Join-Path $fixtureRoot 'index\exports.jsonl'))
        $beforeFiles = @(Get-ChildItem -LiteralPath (Join-Path $fixtureRoot 'exports') -File).Count
        $rejected = $false
        try { $null = New-RegistryExportBundle -BundleType OCI_ARTIFACT } catch { $rejected = $_.Exception.Message -like 'EXPORT_FORMAT_UNAVAILABLE:*' }
        try { $null = New-RegistryExportBundle -BundleType STANDALONE_TARBALL } catch { $rejected = $rejected -and $_.Exception.Message -like 'EXPORT_FORMAT_UNAVAILABLE:*' }
        $rejected -and $beforeFiles -eq @(Get-ChildItem -LiteralPath (Join-Path $fixtureRoot 'exports') -File).Count -and $beforeLedger -eq [System.IO.File]::ReadAllText((Join-Path $fixtureRoot 'index\exports.jsonl'))
    }
    Assert-ExportTest 'Verifier detects payload changes against the local ledger' {
        [System.IO.File]::AppendAllText($payloadPath, 'tamper')
        (Test-RegistryExportBundleIntegrity -ExportId $manifest.export_id).status -eq 'FAIL_PAYLOAD_HASH_MISMATCH'
    }
    Assert-ExportTest 'Existing output paths are never overwritten' {
        $existingPath = Join-Path $fixtureRoot 'exports\preserve.json'
        [System.IO.File]::WriteAllText($existingPath, 'keep-me', $utf8)
        $rejected = $false
        try { $null = New-RegistryExportBundle -BundleType METADATA_ONLY -OutPath $existingPath } catch { $rejected = $_.Exception.Message -like 'EXPORT_PATH_EXISTS:*' }
        $rejected -and [System.IO.File]::ReadAllText($existingPath) -eq 'keep-me'
    }
} finally {
    if ($oldRegistryRoot) { $env:SKILL_REGISTRY_ROOT = $oldRegistryRoot } else { Remove-Item Env:\SKILL_REGISTRY_ROOT -ErrorAction SilentlyContinue }
    Remove-Module RegistryCore -ErrorAction SilentlyContinue
    $resolvedTemp = [System.IO.Path]::GetFullPath($tempBase).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $resolvedFixture = [System.IO.Path]::GetFullPath($fixtureRoot)
    if ($resolvedFixture.StartsWith($resolvedTemp, [System.StringComparison]::OrdinalIgnoreCase) -and [System.IO.Path]::GetFileName($resolvedFixture).StartsWith('jarvis-export-test-', [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
    }
}

Write-Host "Export tests: $passed passed; $failed failed."
if ($failed -gt 0) { exit 1 }
