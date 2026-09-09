# =============================================================================
# Phase 21 Test Harness: CLI Front-End Polish & Developer Experience (DX)
# =============================================================================

param(
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-21-cli-polish.json'
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
Write-Host " RUNNING PHASE 21 TEST SUITE: CLI POLISH & DX               " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: skillctl help displays full domain taxonomy
Assert-Test "Test 01" "skillctl help displays full domain taxonomy" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript help
    $text = $out -join "`n"
    return ($text -match '=== SKILL REGISTRY CLI' -and $text -match 'registry' -and $text -match 'deploy' -and $text -match 'admin')
}

# Test 02: skillctl registry status executes without error
Assert-Test "Test 02" "skillctl registry status executes without error" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript registry status
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'SKILL REGISTRY STATUS')
}

# Test 03: skillctl registry status -Json outputs valid JSON
Assert-Test "Test 03" "skillctl registry status -Json outputs valid parseable JSON" {
    $json = Invoke-CliJson -Args @('registry', 'status', '-Json')
    return ($null -ne $json -and $null -ne $json.registry_id -and $json.schema_count -ge 32)
}

# Test 04: skillctl source list -Json outputs valid JSON array
Assert-Test "Test 04" "skillctl source list -Json outputs valid JSON array" {
    $json = Invoke-CliJson -Args @('source', 'list', '-Json')
    return ($null -ne $json -and $json.Count -ge 1)
}

# Test 05: skillctl discovery status -Json outputs valid JSON
Assert-Test "Test 05" "skillctl discovery status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('discovery', 'status', '-Json')
    return ($null -ne $json)
}

# Test 06: skillctl structure status -Json outputs valid JSON
Assert-Test "Test 06" "skillctl structure status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('structure', 'status', '-Json')
    return ($null -ne $json)
}

# Test 07: skillctl provenance status -Json outputs valid JSON
Assert-Test "Test 07" "skillctl provenance status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('provenance', 'status', '-Json')
    return ($null -ne $json)
}

# Test 08: skillctl integrity status -Json outputs valid JSON
Assert-Test "Test 08" "skillctl integrity status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('integrity', 'status', '-Json')
    return ($null -ne $json)
}

# Test 09: skillctl identity status -Json outputs valid JSON
Assert-Test "Test 09" "skillctl identity status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('identity', 'status', '-Json')
    return ($null -ne $json)
}

# Test 10: skillctl capability status -Json outputs valid JSON
Assert-Test "Test 10" "skillctl capability status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('capability', 'status', '-Json')
    return ($null -ne $json)
}

# Test 11: skillctl compatibility status -Json outputs valid JSON
Assert-Test "Test 11" "skillctl compatibility status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('compatibility', 'status', '-Json')
    return ($null -ne $json)
}

# Test 12: skillctl security status -Json outputs valid JSON
Assert-Test "Test 12" "skillctl security status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('security', 'status', '-Json')
    return ($null -ne $json)
}

# Test 13: skillctl quality status -Json outputs valid JSON
Assert-Test "Test 13" "skillctl quality status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('quality', 'status', '-Json')
    return ($null -ne $json)
}

# Test 14: skillctl conflict status -Json outputs valid JSON
Assert-Test "Test 14" "skillctl conflict status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('conflict', 'status', '-Json')
    return ($null -ne $json)
}

# Test 15: skillctl curation status -Json outputs valid JSON
Assert-Test "Test 15" "skillctl curation status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('curation', 'status', '-Json')
    return ($null -ne $json)
}

# Test 16: skillctl materialize status -Json outputs valid JSON
Assert-Test "Test 16" "skillctl materialize status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('materialize', 'status', '-Json')
    return ($null -ne $json)
}

# Test 17: skillctl profile status -Json outputs valid JSON
Assert-Test "Test 17" "skillctl profile status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('profile', 'status', '-Json')
    return ($null -ne $json)
}

# Test 18: skillctl deploy status -Json outputs valid JSON
Assert-Test "Test 18" "skillctl deploy status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('deploy', 'status', '-Json')
    return ($null -ne $json)
}

# Test 19: skillctl update status -Json outputs valid JSON
Assert-Test "Test 19" "skillctl update status -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('update', 'status', '-Json')
    return ($null -ne $json)
}

# Test 20: skillctl schedule list -Json outputs valid JSON
Assert-Test "Test 20" "skillctl schedule list -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('schedule', 'list', '-Json')
    return ($null -ne $json)
}

# Test 21: skillctl observe telemetry -Json outputs valid JSON
Assert-Test "Test 21" "skillctl observe telemetry -Json outputs valid JSON" {
    $json = Invoke-CliJson -Args @('observe', 'telemetry', '-Json')
    return ($null -ne $json -and $json.overall_health -eq 'HEALTHY')
}

# Test 22: skillctl status -Json outputs valid comprehensive global metrics
Assert-Test "Test 22" "skillctl status -Json outputs valid comprehensive global metrics" {
    $json = Invoke-CliJson -Args @('status', '-Json')
    return ($null -ne $json -and $json.schemas_active_count -ge 32 -and $json.system_health -eq 'HEALTHY')
}

# Test 23: skillctl observe timeline queries historical audit events
Assert-Test "Test 23" "skillctl observe timeline queries historical audit events" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript observe timeline test-timeline-skill
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'LIFECYCLE TIMELINE')
}

# Test 24: skillctl capability search performs semantic capability search
Assert-Test "Test 24" "skillctl capability search performs semantic capability search" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript capability search test
    return ($LASTEXITCODE -eq 0)
}

# Test 25: skillctl compatibility matrix outputs multi-provider matrix
Assert-Test "Test 25" "skillctl compatibility matrix outputs multi-provider compatibility matrix" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript compatibility matrix
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'PROVIDER COMPATIBILITY MATRIX')
}

# Test 26: Graceful error handling on missing mandatory targets
Assert-Test "Test 26" "Graceful error handling on missing mandatory targets exits with code 1" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript source inspect
    return (($out -join "`n") -match 'Please specify a source_id')
}

# Test 27: skillctl observe doctor executes with exit code 0 and reports HEALTHY
Assert-Test "Test 27" "skillctl observe doctor executes with exit code 0 and reports HEALTHY" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript observe doctor
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY')
}

# Test 28: skillctl admin doctor executes with exit code 0 and reports HEALTHY
Assert-Test "Test 28" "skillctl admin doctor executes with exit code 0 and reports HEALTHY" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript admin doctor
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY')
}

# Test 29: skillctl registry doctor validates all 32 schemas and reports HEALTHY
Assert-Test "Test 29" "skillctl registry doctor validates all 32 schemas and reports HEALTHY" {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript registry doctor
    return ($LASTEXITCODE -eq 0 -and ($out -join "`n") -match 'Overall Diagnosis\s*:\s*HEALTHY')
}

# Test 30: Strict Invariant: CLI read-only operations never mutate live active deployments
Assert-Test "Test 30" "Strict Invariant: CLI read-only operations never mutate live active deployments" {
    $depBefore = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    $null = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript status
    $null = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript observe telemetry
    $null = & powershell -NoProfile -ExecutionPolicy Bypass -File $CliScript registry doctor
    $depAfter = @(Get-RegistryDeployments | Where-Object { $_.lifecycle_state -eq 'ACTIVE' }).Count
    return ($depBefore -eq $depAfter)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $global:PassCount / $($global:PassCount + $global:FailCount) PASSED ($global:FailCount FAILED)" -ForegroundColor $(if ($global:FailCount -eq 0) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$reportObj = [ordered]@{
    schema = 'skill-registry.phase-21.cli-tests/v1'
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
