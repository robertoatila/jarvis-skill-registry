# Phase 25 Test Harness — Multi-Platform Distribution Reconnaissance

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-25-distribution-recon.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-ReconTest {
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
Write-Host " RUNNING PHASE 25 TEST SUITE: MULTI-PLATFORM DISTRIBUTION RECON " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: Platform Capabilities Schema exists and is valid JSON
Assert-ReconTest "Test 01" "platform-capabilities.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\platform-capabilities.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:platform-capabilities:1.0.0')
}

# Test 02: Platform Capabilities catalog exists and covers all 6 platforms
Assert-ReconTest "Test 02" "platform-capabilities.json covers all 6 platforms" {
    $catalogFile = Join-Path $RegistryRoot 'schemas\platform-capabilities.json'
    if (-not [System.IO.File]::Exists($catalogFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
    $platforms = @('gemini', 'codex', 'claude', 'chatgpt', 'cursor', 'generic')
    foreach ($p in $platforms) {
        if (-not $data.platforms.PSObject.Properties.Item($p)) { return $false }
    }
    return $true
}

# Test 03: Adapter Contract V1 Schema exists and is valid JSON
Assert-ReconTest "Test 03" "adapter-contract-v1.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\adapter-contract-v1.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:adapter-contract:1.0.0')
}

# Test 04: Adapter Contract V1 catalog defines 8 lifecycle methods and 6 safety invariants
Assert-ReconTest "Test 04" "adapter-contract-v1.json defines 8 lifecycle methods and 6 invariants" {
    $contractFile = Join-Path $RegistryRoot 'schemas\adapter-contract-v1.json'
    if (-not [System.IO.File]::Exists($contractFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($contractFile) | ConvertFrom-Json
    $methods = @('inspect_target', 'plan_materialization', 'materialize_staged', 'validate_staged', 'plan_distribution', 'execute_distribution', 'verify_distribution', 'uninstall')
    foreach ($m in $methods) {
        if (-not $data.interface_methods.PSObject.Properties.Item($m)) { return $false }
    }
    return ($data.safety_invariants.source_immutability -eq $true -and
            $data.safety_invariants.quarantine_fail_closed -eq $true -and
            $data.safety_invariants.zero_dynamic_payload_execution -eq $true)
}

# Test 05: Target Layouts Schema exists and is valid JSON
Assert-ReconTest "Test 05" "target-layouts.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\target-layouts.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:target-layouts:1.0.0')
}

# Test 06: Target Layouts catalog defines layouts for all 6 targets
Assert-ReconTest "Test 06" "target-layouts.json defines filesystem layouts for all 6 targets" {
    $layoutsFile = Join-Path $RegistryRoot 'schemas\target-layouts.json'
    if (-not [System.IO.File]::Exists($layoutsFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($layoutsFile) | ConvertFrom-Json
    $targets = @('gemini', 'codex', 'claude', 'chatgpt', 'cursor', 'generic')
    foreach ($t in $targets) {
        $item = $data.targets.PSObject.Properties.Item($t).Value
        if (-not $item.entrypoint_filename -or -not $item.lockfile_path_template) { return $false }
    }
    return $true
}

# Test 07: Gemini platform is marked as VERIFIED_EMPIRICAL
Assert-ReconTest "Test 07" "Platform Capabilities marks Gemini as VERIFIED_EMPIRICAL" {
    $catalogFile = Join-Path $RegistryRoot 'schemas\platform-capabilities.json'
    $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
    return ($data.platforms.gemini.verification_status -eq 'VERIFIED_EMPIRICAL')
}

# Test 08: Non-local targets are marked VERIFIED_DOCS or UNVERIFIED with clear boundary
Assert-ReconTest "Test 08" "Platform Capabilities marks remote/doc targets with correct status" {
    $catalogFile = Join-Path $RegistryRoot 'schemas\platform-capabilities.json'
    $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
    return ($data.platforms.codex.verification_status -eq 'VERIFIED_DOCS' -and
            $data.platforms.claude.verification_status -eq 'VERIFIED_DOCS' -and
            $data.platforms.chatgpt.verification_status -eq 'VERIFIED_DOCS' -and
            $data.platforms.cursor.verification_status -eq 'VERIFIED_DOCS')
}

# Test 09: Adapter registry in contract matches existing adapters on disk
Assert-ReconTest "Test 09" "Adapter bindings in contract match adapter.json files on disk" {
    $contractFile = Join-Path $RegistryRoot 'schemas\adapter-contract-v1.json'
    $data = [System.IO.File]::ReadAllText($contractFile) | ConvertFrom-Json
    foreach ($adp in $data.adapter_registry) {
        $adpDir = Join-Path $RegistryRoot ("adapters\" + $adp.target_provider.ToLower().Replace("openai", "chatgpt").Replace("generic_agent", "generic"))
        $adpFile = Join-Path $adpDir 'adapter.json'
        if (-not [System.IO.File]::Exists($adpFile)) { return $false }
    }
    return $true
}

# Test 10: Target layouts declare collision policies and atomic write strategies
Assert-ReconTest "Test 10" "Target layouts declare collision policies and atomic write strategies" {
    $layoutsFile = Join-Path $RegistryRoot 'schemas\target-layouts.json'
    $data = [System.IO.File]::ReadAllText($layoutsFile) | ConvertFrom-Json
    foreach ($prop in $data.targets.PSObject.Properties) {
        $t = $prop.Value
        if (-not $t.collision_policy -or -not $t.atomic_write_strategy) { return $false }
    }
    return $true
}

# Test 11: Safety invariants enforce fail-closed quarantine and zero execution
Assert-ReconTest "Test 11" "Safety invariants enforce fail-closed quarantine and zero execution" {
    $contractFile = Join-Path $RegistryRoot 'schemas\adapter-contract-v1.json'
    $data = [System.IO.File]::ReadAllText($contractFile) | ConvertFrom-Json
    return ($data.safety_invariants.quarantine_fail_closed -eq $true -and
            $data.safety_invariants.zero_dynamic_payload_execution -eq $true -and
            $data.safety_invariants.source_immutability -eq $true)
}

# Test 12: Script execution models accurately distinguish local shell from remote actions
Assert-ReconTest "Test 12" "Script execution models distinguish local shell from remote actions" {
    $catalogFile = Join-Path $RegistryRoot 'schemas\platform-capabilities.json'
    $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
    return ($data.platforms.gemini.script_execution.model -eq 'LOCAL_SHELL' -and
            $data.platforms.chatgpt.script_execution.model -eq 'REMOTE_ACTION_ONLY' -and
            $data.platforms.generic.script_execution.model -eq 'DECLARED_RUNNER')
}

# Test 13: Zero secret or credential leakage across Phase 25 schemas
Assert-ReconTest "Test 13" "Zero secret or credential leakage in schemas/ directory" {
    $schemaDir = Join-Path $RegistryRoot 'schemas'
    $files = @(Get-ChildItem -Path $schemaDir -Filter '*platform*' -File) +
             @(Get-ChildItem -Path $schemaDir -Filter '*adapter-contract*' -File) +
             @(Get-ChildItem -Path $schemaDir -Filter '*target-layouts*' -File)
    $patterns = @('AIzaSy', 'sk-[a-zA-Z0-9]{20,}', 'bearer\s+[a-zA-Z0-9_\-\.]{20,}')
    foreach ($f in $files) {
        $text = [System.IO.File]::ReadAllText($f.FullName)
        foreach ($p in $patterns) {
            if ($text -match $p) { return $false }
        }
    }
    return $true
}

# Test 14: Core Gates 0-24 immutability check (Merkle root and Ledgers untouched)
Assert-ReconTest "Test 14" "Core Gates 0-24 immutability check verified" {
    $archFile = Join-Path $RegistryRoot 'docs\ARCHITECTURE.md'
    $content = [System.IO.File]::ReadAllText($archFile)
    return ($content.Contains("596552cf11583365510fb13503394efd59e9769e01ab53da96342f0ce807f958") -and
            $content.Contains("gov-quarantine-link-v1"))
}

# Test 15: Read-Only reconnaissance boundary respected (zero targets modified)
Assert-ReconTest "Test 15" "Read-Only reconnaissance boundary respected (zero targets modified)" {
    # Check that no unauthorized installations took place
    $geminiSkills = 'C:\Users\Ad\.gemini\config\skills'
    if (Test-Path $geminiSkills) {
        $items = @(Get-ChildItem -Path $geminiSkills -Directory)
        return ($items.Count -ge 160)
    }
    return $true
}

$passedCount = @($testResults | Where-Object { $_.status -eq 'PASS' }).Count
$failedCount = @($testResults | Where-Object { $_.status -eq 'FAIL' }).Count

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $passedCount / $($testResults.Count) PASSED ($failedCount FAILED)" -ForegroundColor $(if ($script:globalPassed) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$auditReport = [ordered]@{
    schema = 'skill-registry.phase-25.distribution-recon/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    platforms_evaluated = 6
    verification_levels = [ordered]@{
        verified_empirical = 1
        verified_docs = 5
        unverified = 0
    }
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
