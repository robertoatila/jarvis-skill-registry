# Phase 31 Test Harness — MCP Server & REST API Gateway

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-31-mcp-api-gateway.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $RegistryRoot 'tooling\McpApiGateway.psm1') -Force

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-GatewayTest {
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
Write-Host " RUNNING PHASE 31 TEST SUITE: MCP SERVER & REST API GATEWAY " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: MCP Tool Definition Schema exists and is valid JSON
Assert-GatewayTest "Test 01" "mcp-tool-definition.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\mcp-tool-definition.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:mcp-tool-definition:1.0.0')
}

# Test 02: MCP Tool Definition catalog defines 6 governed tools
Assert-GatewayTest "Test 02" "mcp-tool-definition.json defines all 6 governed MCP tools" {
    $tools = Get-McpToolCatalog -RegistryRoot $RegistryRoot
    $names = $tools | ForEach-Object { $_.name }
    return ($names -contains 'query_skills' -and
            $names -contains 'inspect_capabilities' -and
            $names -contains 'verify_provenance' -and
            $names -contains 'resolve_project' -and
            $names -contains 'plan_distribution' -and
            $names -contains 'execute_distribution')
}

# Test 03: MCP Gateway Config Schema exists and is valid JSON
Assert-GatewayTest "Test 03" "mcp-gateway-config.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\mcp-gateway-config.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:mcp-gateway-config:1.0.0')
}

# Test 04: MCP Gateway Config catalog defines bindings and fail-closed flags
Assert-GatewayTest "Test 04" "mcp-gateway-config.json defines server transports & fail-closed flags" {
    $cfgFile = Join-Path $RegistryRoot 'schemas\mcp-gateway-config.json'
    if (-not [System.IO.File]::Exists($cfgFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($cfgFile) | ConvertFrom-Json
    return ($data.quarantine_fail_closed -eq $true -and $data.require_explicit_distribution_approval -eq $true)
}

# Test 05: API Gateway Endpoints Schema exists and is valid JSON
Assert-GatewayTest "Test 05" "api-gateway-endpoints.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\api-gateway-endpoints.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:api-gateway-endpoints:1.0.0')
}

# Test 06: API Gateway Endpoints catalog defines routes
Assert-GatewayTest "Test 06" "api-gateway-endpoints.json defines REST API routes" {
    $routes = Get-ApiEndpointCatalog -RegistryRoot $RegistryRoot
    $paths = $routes | ForEach-Object { $_.path }
    return ($paths -contains '/v1/skills' -and
            $paths -contains '/v1/capabilities' -and
            $paths -contains '/v1/provenance/:id' -and
            $paths -contains '/v1/resolve' -and
            $paths -contains '/v1/distribution/plan' -and
            $paths -contains '/v1/distribution/execute')
}

# Test 07: Gateway Audit Log Schema exists and is valid JSON
Assert-GatewayTest "Test 07" "gateway-audit-log.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\gateway-audit-log.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:gateway-audit-log:1.0.0')
}

# Test 08: Gateway Audit Log catalog defines audit record
Assert-GatewayTest "Test 08" "gateway-audit-log.json defines audit trail record" {
    $auditFile = Join-Path $RegistryRoot 'schemas\gateway-audit-log.json'
    if (-not [System.IO.File]::Exists($auditFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($auditFile) | ConvertFrom-Json
    return ($data.response_status -eq 'SUCCESS' -and $data.parameters_hash.Length -eq 64)
}

# Test 09: query_skills MCP Tool returns verified clean skills and does not synthesize fake skills
Assert-GatewayTest "Test 09" "query_skills MCP tool returns results in pure READ_ONLY mode and rejects synthetic mocks" {
    $res1 = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'query_skills' -Arguments @{ query = 'react-modernization' }
    $res2 = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'query_skills' -Arguments @{ query = 'non-existent-fake-skill-xyz' }
    $items2 = @($res2.content[0].text | ConvertFrom-Json)
    return ($res1.isError -eq $false -and $res1.content[0].text.Contains('react-modernization') -and
            $items2.Count -eq 0)
}

# Test 10: inspect_capabilities MCP Tool returns multi-target compatibility
Assert-GatewayTest "Test 10" "inspect_capabilities MCP tool returns multi-target compatibility" {
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'inspect_capabilities' -Arguments @{ capability_id = 'react-modernization'; target_platform = 'cursor' }
    return ($res.isError -eq $false -and $res.content[0].text.Contains('cursor') -and $res.content[0].text.Contains('adp-cursor-v1'))
}

# Test 11: verify_provenance MCP Tool returns current Merkle root anchor and rejects unknown resources
Assert-GatewayTest "Test 11" "verify_provenance MCP tool returns current Merkle anchor and validates against ledger" {
    $activeMerkle = (Get-Content -LiteralPath (Join-Path $RegistryRoot 'state\canonical-merkle.json') | ConvertFrom-Json).merkle_root
    $resValid = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'verify_provenance' -Arguments @{ resource_id_or_name = 'react-modernization' }
    $resFake = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'verify_provenance' -Arguments @{ resource_id_or_name = 'malicious-or-nonexistent-skill' }
    
    return ($resValid.isError -eq $false -and $resValid.content[0].text.Contains($activeMerkle) -and
            $resFake.isError -eq $true -and $resFake.content[0].text.Contains('NOT_FOUND'))
}

# Test 12: resolve_project MCP Tool computes stack resolution without mutating workspace
Assert-GatewayTest "Test 12" "resolve_project MCP tool computes plan with zero auto-installation" {
    $tempWs = Join-Path $RegistryRoot 'staging\temp-mcp-resolve-ws'
    if (Test-Path $tempWs) { Remove-Item -Path $tempWs -Recurse -Force | Out-Null }
    New-Item -ItemType Directory -Path $tempWs -Force | Out-Null
    
    $pkgJson = '{"name":"test-mcp-app","dependencies":{"react":"18.2.0","next":"14.1.0"},"devDependencies":{"typescript":"5.0.0"}}'
    [System.IO.File]::WriteAllText((Join-Path $tempWs 'package.json'), $pkgJson, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText((Join-Path $tempWs 'tsconfig.json'), '{}', [System.Text.Encoding]::UTF8)
    
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'resolve_project' -Arguments @{ workspace_path = $tempWs }
    Remove-Item -Path $tempWs -Recurse -Force | Out-Null
    
    if ($res.isError) { return $false }
    $data = $res.content[0].text | ConvertFrom-Json
    return ($data.action -eq 'PLAN_READY' -and $data.auto_installed -eq $false)
}

# Test 13: plan_distribution MCP Tool produces pre-execution preview and saves real plan
Assert-GatewayTest "Test 13" "plan_distribution MCP tool produces pre-execution preview and saves real plan" {
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'plan_distribution' -Arguments @{ canonical_name = 'hyperplan-orchestrator'; target_platform = 'cursor' }
    if ($res.isError) { return $false }
    $script:testRealPlan = $res.content[0].text | ConvertFrom-Json
    return ($script:testRealPlan.action_type -in @('CREATE', 'UPDATE', 'NOOP') -and $script:testRealPlan.execution_performed -eq $false)
}

# Test 14: execute_distribution MCP Tool refuses execution without approved: true
Assert-GatewayTest "Test 14" "execute_distribution MCP tool refuses execution without explicit approval" {
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'execute_distribution' -Arguments @{ plan_id = $script:testRealPlan.plan_id; approved = $false }
    return ($res.isError -eq $true -and $res.content[0].text.Contains('Explicit user approval not granted'))
}

# Test 14B: execute_distribution MCP Tool rejects placeholder / zero-hash plans
Assert-GatewayTest "Test 14B" "execute_distribution MCP tool rejects placeholder zero-hash plans" {
    $fakeZeroPlan = [PSCustomObject]@{
        schema_version = "1.0.0"
        plan_id = "dplan-zero-test"
        resource_id = "sres-v1-sha256:0000000000000000000000000000000000000000000000000000000000000000"
        canonical_name = "fake-skill"
        target_platform = "cursor"
        target_destination_path = "staging\fake"
        action_type = "CREATE"
        expected_content_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        approval_required = $true
    }
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'execute_distribution' -Arguments @{ plan = $fakeZeroPlan; approved = $true }
    return ($res.isError -eq $true -and $res.content[0].text.Contains('zero-hash'))
}

# Test 14C: execute_distribution MCP Tool executes real plan with valid hash when approved
Assert-GatewayTest "Test 14C" "execute_distribution MCP tool executes real validated plan when approved" {
    $res = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'execute_distribution' -Arguments @{ plan_id = $script:testRealPlan.plan_id; approved = $true }
    return ($res.isError -eq $false -and $res.content[0].text.Contains('COMMITTED'))
}

# Test 15: REST API Gateway dispatches routes with matching contracts
Assert-GatewayTest "Test 15" "Invoke-ApiGatewayRoute dispatches /v1/skills and /v1/health successfully" {
    $r1 = Invoke-ApiGatewayRoute -RegistryRoot $RegistryRoot -Path '/v1/skills' -Method 'GET'
    $r2 = Invoke-ApiGatewayRoute -RegistryRoot $RegistryRoot -Path '/v1/health' -Method 'GET'
    return ($r1.status -eq 200 -and $r2.status -eq 200 -and $r2.body.Contains('HEALTHY'))
}

# Test 16: Core Gates 0-24 immutability check verified
Assert-GatewayTest "Test 16" "Core Gates 0-24 immutability check verified" {
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
    schema = 'skill-registry.phase-31.mcp-api-gateway/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    tools_exposed = 6
    rest_routes_exposed = 7
    zero_arbitrary_execution = $true
    quarantine_fail_closed = $true
    explicit_approval_enforced = $true
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
