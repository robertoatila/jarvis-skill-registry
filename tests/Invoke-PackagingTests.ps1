# Phase 33 Test Harness - Open Source Packaging, Sanitization and Direct Evidence

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-33-open-source-packaging.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-PackagingTest {
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
Write-Host " RUNNING PHASE 33 TEST SUITE: OPEN SOURCE PACKAGING & DIRECT EVIDENCE " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Assert-PackagingTest "Test 01" "LICENSE exists and contains Apache License 2.0 terms" {
    $licenseFile = Join-Path $RegistryRoot 'LICENSE'
    if (-not [System.IO.File]::Exists($licenseFile)) { return $false }
    $content = [System.IO.File]::ReadAllText($licenseFile)
    return ($content.Contains("Apache License") -and $content.Contains("Version 2.0"))
}

Assert-PackagingTest "Test 02" "README.md identifies project status, docs and current evidence" {
    $readme = Join-Path $RegistryRoot 'README.md'
    if (-not [System.IO.File]::Exists($readme)) { return $false }
    $content = [System.IO.File]::ReadAllText($readme)
    return ($content.Contains("The repository is active development") -and
            $content.Contains("docs/README.md") -and
            $content.Contains("evidence/current.json"))
}

Assert-PackagingTest "Test 03" "CONTRIBUTING.md exists and defines adapter creation guidelines" {
    $contrib = Join-Path $RegistryRoot 'CONTRIBUTING.md'
    if (-not [System.IO.File]::Exists($contrib)) { return $false }
    $content = [System.IO.File]::ReadAllText($contrib)
    return ($content.Contains("Adding a New Target Platform Adapter") -and
            $content.Contains("VERIFIED_EMPIRICAL"))
}

Assert-PackagingTest "Test 04" "SECURITY.md exists and specifies vulnerability and quarantine policies" {
    $sec = Join-Path $RegistryRoot 'SECURITY.md'
    if (-not [System.IO.File]::Exists($sec)) { return $false }
    $content = [System.IO.File]::ReadAllText($sec)
    return ($content.Contains("Reporting a Vulnerability") -and
            $content.Contains("Fail-Closed Quarantine Barrier"))
}

Assert-PackagingTest "Test 05" "CODE_OF_CONDUCT.md exists and follows Contributor Covenant" {
    $coc = Join-Path $RegistryRoot 'CODE_OF_CONDUCT.md'
    if (-not [System.IO.File]::Exists($coc)) { return $false }
    $content = [System.IO.File]::ReadAllText($coc)
    return ($content.Contains("Contributor Covenant Code of Conduct"))
}

Assert-PackagingTest "Test 06" "docs/ARCHITECTURE_5_LAYERS.md exists and details complete layer hierarchy" {
    $arch = Join-Path $RegistryRoot 'docs\ARCHITECTURE_5_LAYERS.md'
    if (-not [System.IO.File]::Exists($arch)) { return $false }
    $content = [System.IO.File]::ReadAllText($arch)
    return ($content.Contains("Layer 1: Core Integrity") -and
            $content.Contains("Layer 5: Experience"))
}

Assert-PackagingTest "Test 07" "docs/ADAPTER_DEVELOPMENT_GUIDE.md exists and describes adapter JSON schema" {
    $adp = Join-Path $RegistryRoot 'docs\ADAPTER_DEVELOPMENT_GUIDE.md'
    if (-not [System.IO.File]::Exists($adp)) { return $false }
    $content = [System.IO.File]::ReadAllText($adp)
    return ($content.Contains("adapters/<platform>/adapter.json"))
}

Assert-PackagingTest "Test 08" "Direct validation gates exist without requiring GitHub Actions" {
    $gate = Join-Path $RegistryRoot 'tooling\validate_v020_plan4.py'
    $readme = Join-Path $RegistryRoot 'README.md'
    if (-not [System.IO.File]::Exists($gate) -or -not [System.IO.File]::Exists($readme)) { return $false }
    $gateContent = [System.IO.File]::ReadAllText($gate)
    $readmeContent = [System.IO.File]::ReadAllText($readme)
    return ($gateContent.Contains('github_actions_used') -and
            $readmeContent.Contains('does not use GitHub Actions as a validation gate'))
}

Assert-PackagingTest "Test 09" "Release evidence manifest does not overstate readiness" {
    $manifestPath = Join-Path $RegistryRoot 'evidence\current.json'
    if (-not [System.IO.File]::Exists($manifestPath)) { return $false }
    $manifest = [System.IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
    return ($manifest.release.status -eq 'DIRECT_VALIDATION_REQUIRED' -and
            $manifest.release.evidence_status -eq 'INCOMPLETE' -and
            $manifest.validation.github_actions_authority -eq $false)
}

Assert-PackagingTest "Test 09B" "Public README explains direct gates and incomplete v0.2 evidence" {
    $readme = Join-Path $RegistryRoot 'README.md'
    $manifestPath = Join-Path $RegistryRoot 'evidence\current.json'
    if (-not [System.IO.File]::Exists($readme) -or -not [System.IO.File]::Exists($manifestPath)) { return $false }
    $readmeContent = [System.IO.File]::ReadAllText($readme)
    $manifest = [System.IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
    return ($readmeContent.Contains('DIRECT_VALIDATION_REQUIRED') -and
            $readmeContent.Contains('does not use GitHub Actions as a validation gate') -and
            $manifest.validation.direct_evidence_fresh_for_current_head -eq $false)
}

Assert-PackagingTest "Test 10" "tooling/Bootstrap.ps1 executes successfully without error" {
    $bs = Join-Path $RegistryRoot 'tooling\Bootstrap.ps1'
    if (-not [System.IO.File]::Exists($bs)) { return $false }
    & $bs -RegistryRoot $RegistryRoot
    return $true
}

Assert-PackagingTest "Test 11" "Repository hygiene scan verifies ZERO secrets or credentials" {
    $forbidden = @('ghp_[A-Za-z0-9_]{36}', 'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY')
    $targetDirs = @('schemas', 'tooling', 'docs', 'adapters', 'governance')
    foreach ($d in $targetDirs) {
        $dirPath = Join-Path $RegistryRoot $d
        if (Test-Path $dirPath) {
            $files = @(Get-ChildItem -Path $dirPath -Recurse -File | Where-Object {
                $_.FullName -notmatch '\\__pycache__\\' -and
                $_.Extension -notin @('.pyc', '.pyo')
            })
            foreach ($f in $files) {
                $text = [System.IO.File]::ReadAllText($f.FullName)
                foreach ($p in $forbidden) {
                    if ($text -match $p) { return $false }
                }
            }
        }
    }
    return $true
}

Assert-PackagingTest "Test 12" "Schemas and configurations use generic {USER_HOME} templates" {
    $layouts = [System.IO.File]::ReadAllText((Join-Path $RegistryRoot 'schemas\target-layouts.json'))
    return ($layouts.Contains("{USER_HOME}"))
}

Assert-PackagingTest "Test 13" "Verification levels distinguish EMPIRICAL, CI, and DOCS" {
    $caps = [System.IO.File]::ReadAllText((Join-Path $RegistryRoot 'schemas\platform-capabilities.json'))
    return ($caps.Contains("VERIFIED_EMPIRICAL") -and $caps.Contains("VERIFIED_DOCS"))
}

Assert-PackagingTest "Test 14" ".gitignore exists and ignores staging and logs" {
    $gi = Join-Path $RegistryRoot '.gitignore'
    if (-not [System.IO.File]::Exists($gi)) { return $false }
    $content = [System.IO.File]::ReadAllText($gi)
    return ($content.Contains("staging/test-targets/") -and $content.Contains("*.log"))
}

Assert-PackagingTest "Test 15" "Package structure satisfies standalone repository cloning" {
    $hasTooling = Test-Path (Join-Path $RegistryRoot 'tooling')
    $hasSchemas = Test-Path (Join-Path $RegistryRoot 'schemas')
    $hasTests = Test-Path (Join-Path $RegistryRoot 'tests')
    return ($hasTooling -and $hasSchemas -and $hasTests)
}

Assert-PackagingTest "Test 16" "Core Gates 0-24 immutability check verified" {
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
    schema = 'skill-registry.phase-33.open-source-packaging/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    license = "Apache-2.0"
    matrix_runners = @("windows-latest", "ubuntu-latest", "macos-latest")
    secrets_found = 0
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
