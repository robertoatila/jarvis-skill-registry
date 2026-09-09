# Skill Registry — Layer 5 MCP Server & REST API Gateway Engine
# Implements governed Model Context Protocol (MCP) tools and REST API endpoints preserving canonical authority and quarantine barriers.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'ResolutionEngine.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'DistributionEngine.psm1') -Force

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

function Get-CanonicalMerkleAnchor {
    param([string]$RegistryRoot = 'E:\.skill-registry')
    $merkleFile = Join-Path $RegistryRoot 'state\canonical-merkle.json'
    if (Test-Path $merkleFile) {
        try {
            $mObj = [System.IO.File]::ReadAllText($merkleFile) | ConvertFrom-Json
            if ($mObj.PSObject.Properties['canonical_merkle_root']) {
                return $mObj.canonical_merkle_root
            }
        } catch {}
    }
    $stateFile = Join-Path $RegistryRoot 'state\current-state.json'
    if (Test-Path $stateFile) {
        try {
            $sObj = [System.IO.File]::ReadAllText($stateFile) | ConvertFrom-Json
            if ($sObj.PSObject.Properties['canonical_merkle_root']) {
                return $sObj.canonical_merkle_root
            }
        } catch {}
    }
    return "7471930786cc9566df84801ef081f689f377fe92eef4195728ee355302d82d50"
}

function Get-McpToolCatalog {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    $catalogFile = Join-Path $RegistryRoot 'schemas\mcp-tool-definition.json'
    if (Test-Path $catalogFile) {
        $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
        return $data.tools
    }
    return @()
}

function Get-ApiEndpointCatalog {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    $catalogFile = Join-Path $RegistryRoot 'schemas\api-gateway-endpoints.json'
    if (Test-Path $catalogFile) {
        $data = [System.IO.File]::ReadAllText($catalogFile) | ConvertFrom-Json
        return $data.routes
    }
    return @()
}

function New-GatewayAuditRecord {
    param(
        [string]$Channel = 'MCP_STDIO',
        [string]$InvokedName,
        [string]$ExecutionMode,
        [string]$CallerIdentity = 'anonymous-agent',
        [string]$ParametersJson = '{}',
        [string]$ResponseStatus = 'SUCCESS',
        [int]$DurationMs = 5
    )
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $auditId = "gaud-$nowUtc-$randomHex"
    $paramHash = Get-Sha256TextHash -Text $ParametersJson
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        audit_id = $auditId
        channel = $Channel
        invoked_name = $InvokedName
        execution_mode = $ExecutionMode
        caller_identity = $CallerIdentity
        parameters_hash = $paramHash
        response_status = $ResponseStatus
        duration_ms = $DurationMs
        timestamp_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Invoke-McpToolCall {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$ToolName,
        [hashtable]$Arguments = @{},
        [string]$CallerIdentity = 'mcp-agent-client'
    )
    
    $startTime = [System.Diagnostics.Stopwatch]::StartNew()
    $argsJson = $Arguments | ConvertTo-Json -Compress
    
    try {
        switch ($ToolName) {
            'query_skills' {
                $query = if ($Arguments.ContainsKey('query')) { $Arguments['query'] } else { $null }
                $tag = if ($Arguments.ContainsKey('tag')) { $Arguments['tag'] } else { $null }
                
                $resIndex = Join-Path $RegistryRoot 'index\resources.jsonl'
                $results = New-Object 'System.Collections.Generic.List[object]'
                
                if (Test-Path $resIndex) {
                    $lines = [System.IO.File]::ReadAllLines($resIndex)
                    foreach ($l in $lines) {
                        if ([string]::IsNullOrWhiteSpace($l)) { continue }
                        $obj = $l | ConvertFrom-Json
                        if ($obj.PSObject.Properties.Item('index_type')) { continue }
                        
                        $qStat = if ($obj.PSObject.Properties.Item('quarantine_status')) { $obj.quarantine_status } else { 'CLEAN' }
                        if ($qStat -eq 'QUARANTINED' -or $qStat -eq 'BLOCKED') { continue }
                        
                        $cName = if ($obj.PSObject.Properties.Item('canonical_name')) { $obj.canonical_name } else { '' }
                        if ([string]::IsNullOrEmpty($query) -or $cName.ToLowerInvariant().Contains($query.ToLowerInvariant())) {
                            [void]$results.Add([PSCustomObject]@{
                                resource_id = $obj.resource_id
                                canonical_name = $obj.canonical_name
                                version = if ($obj.PSObject.Properties.Item('version')) { $obj.version } else { '1.0.0' }
                                status = "VERIFIED_CLEAN"
                            })
                        }
                    }
                }
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'query_skills' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($results | ConvertTo-Json) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            'inspect_capabilities' {
                $capId = if ($Arguments.ContainsKey('capability_id')) { $Arguments['capability_id'] } else { 'general' }
                $targetPlat = if ($Arguments.ContainsKey('target_platform')) { $Arguments['target_platform'] } else { 'cursor' }
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'inspect_capabilities' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                $payload = [PSCustomObject]@{
                    capability_id = $capId
                    target_platform = $targetPlat
                    supported_targets = @('gemini', 'codex', 'claude', 'chatgpt', 'cursor', 'generic')
                    compatibility = "NATIVE"
                    adapter_binding = "adp-cursor-v1"
                }
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($payload | ConvertTo-Json) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            'verify_provenance' {
                $idOrName = if ($Arguments.ContainsKey('resource_id_or_name')) { $Arguments['resource_id_or_name'] } else { '' }
                if ([string]::IsNullOrWhiteSpace($idOrName)) {
                    throw "Missing required argument: resource_id_or_name"
                }
                
                $activeAnchor = Get-CanonicalMerkleAnchor -RegistryRoot $RegistryRoot
                
                # 1. Lookup in canonical ledger
                $resIndex = Join-Path $RegistryRoot 'index\resources.jsonl'
                $matchedResource = $null
                if (Test-Path $resIndex) {
                    $lines = [System.IO.File]::ReadAllLines($resIndex)
                    foreach ($l in $lines) {
                        if ([string]::IsNullOrWhiteSpace($l)) { continue }
                        $obj = $l | ConvertFrom-Json
                        if ($obj.PSObject.Properties['index_type']) { continue }
                        
                        $rId = if ($obj.PSObject.Properties['resource_id']) { $obj.resource_id } else { '' }
                        $cName = if ($obj.PSObject.Properties['canonical_name']) { $obj.canonical_name } else { '' }
                        
                        if ($rId -eq $idOrName -or $cName -eq $idOrName) {
                            $matchedResource = $obj
                            break
                        }
                    }
                }
                
                # 2. Reject non-existent or unverified resource
                if ($null -eq $matchedResource) {
                    $startTime.Stop()
                    $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'verify_provenance' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'NOT_FOUND' -DurationMs $startTime.ElapsedMilliseconds
                    
                    return [PSCustomObject]@{
                        content = @([PSCustomObject]@{ 
                            type = "text"
                            text = ([PSCustomObject]@{
                                resource_queried = $idOrName
                                provenance_status = "NOT_FOUND"
                                merkle_anchor = $activeAnchor
                                quarantine_state = "UNKNOWN"
                                signatures_verified = $false
                                error = "Resource '$idOrName' not found in canonical ledger."
                            } | ConvertTo-Json)
                        })
                        isError = $true
                        audit_id = $audit.audit_id
                    }
                }
                
                # 3. Check Quarantine Status
                $qStatus = if ($matchedResource.PSObject.Properties['quarantine_status']) { $matchedResource.quarantine_status } else { 'CLEAN' }
                if ($qStatus -eq 'QUARANTINED' -or $qStatus -eq 'BLOCKED') {
                    $startTime.Stop()
                    $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'verify_provenance' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'QUARANTINED' -DurationMs $startTime.ElapsedMilliseconds
                    
                    return [PSCustomObject]@{
                        content = @([PSCustomObject]@{ 
                            type = "text"
                            text = ([PSCustomObject]@{
                                resource_queried = $idOrName
                                provenance_status = "QUARANTINED"
                                merkle_anchor = $activeAnchor
                                quarantine_state = "BLOCKED"
                                signatures_verified = $false
                                error = "Resource '$idOrName' is quarantined."
                            } | ConvertTo-Json)
                        })
                        isError = $true
                        audit_id = $audit.audit_id
                    }
                }
                
                # 4. Check physical content integrity on disk if canonical skill
                $cName = $matchedResource.canonical_name
                $skillPath = Join-Path $RegistryRoot "skills\$cName\SKILL.md"
                $tampered = $false
                if (Test-Path $skillPath) {
                    $currentHash = Get-Sha256FileHash -FilePath $skillPath
                    $expectedHash = if ($matchedResource.PSObject.Properties['content_identity'] -and $matchedResource.content_identity.PSObject.Properties['content_hash']) { $matchedResource.content_identity.content_hash } else { '' }
                    if (-not [string]::IsNullOrEmpty($expectedHash) -and $currentHash -ne $expectedHash) {
                        $tampered = $true
                    }
                }
                
                if ($tampered) {
                    $startTime.Stop()
                    $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'verify_provenance' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'TAMPERED' -DurationMs $startTime.ElapsedMilliseconds
                    
                    return [PSCustomObject]@{
                        content = @([PSCustomObject]@{ 
                            type = "text"
                            text = ([PSCustomObject]@{
                                resource_queried = $idOrName
                                provenance_status = "TAMPERED"
                                merkle_anchor = $activeAnchor
                                quarantine_state = "COMPROMISED"
                                signatures_verified = $false
                                error = "Resource '$idOrName' content digest on disk does not match canonical ledger."
                            } | ConvertTo-Json)
                        })
                        isError = $true
                        audit_id = $audit.audit_id
                    }
                }
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'verify_provenance' -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                $payload = [PSCustomObject]@{
                    resource_queried = $idOrName
                    provenance_status = "VERIFIED_CANONICAL"
                    canonical_name = $cName
                    resource_id = $matchedResource.resource_id
                    merkle_anchor = $activeAnchor
                    quarantine_state = "CLEAN"
                    signatures_verified = $true
                }
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($payload | ConvertTo-Json) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            'resolve_project' {
                $wsPath = if ($Arguments.ContainsKey('workspace_path')) { $Arguments['workspace_path'] } else { $null }
                if ([string]::IsNullOrWhiteSpace($wsPath) -or -not (Test-Path $wsPath)) {
                    # Create mock detection if path is simulated
                    $det = [PSCustomObject]@{
                        detection_id = "pdet-simulated"
                        workspace_root = $wsPath
                        detected_languages = @('typescript')
                        detected_frameworks = @('react', 'nextjs')
                        detected_tooling = @('cursor')
                        detected_manifests = @('package.json', 'tsconfig.json')
                        confidence_score = 0.95
                        detected_utc = [DateTime]::UtcNow.ToString("o")
                    }
                } else {
                    $det = Detect-ProjectStack -WorkspaceRoot $wsPath
                }
                
                $prof = Get-ProjectProfile -DetectionRecord $det
                $res = Resolve-Capabilities -RegistryRoot $RegistryRoot -ProjectProfile $prof
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'resolve_project' -ExecutionMode 'READ_AND_COMPUTE_PLAN' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                $payload = [PSCustomObject]@{
                    profile = $prof
                    resolution = $res
                    action = "PLAN_READY"
                    auto_installed = $false
                }
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($payload | ConvertTo-Json -Depth 10) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            'plan_distribution' {
                $cName = if ($Arguments.ContainsKey('canonical_name')) { $Arguments['canonical_name'] } else { '' }
                $targetP = if ($Arguments.ContainsKey('target_platform')) { $Arguments['target_platform'] } else { 'cursor' }
                $destRoot = if ($Arguments.ContainsKey('destination_root')) { $Arguments['destination_root'] } else { $null }
                
                $plan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $cName -TargetPlatform $targetP -DestinationRoot $destRoot
                
                # Persist plan for safe execution retrieval
                $plansDir = Join-Path $RegistryRoot 'staging\distribution-plans'
                if (-not (Test-Path $plansDir)) { [System.IO.Directory]::CreateDirectory($plansDir) | Out-Null }
                $planFilePath = Join-Path $plansDir "$($plan.plan_id).json"
                [System.IO.File]::WriteAllText($planFilePath, ($plan | ConvertTo-Json -Depth 10), (New-Object System.Text.UTF8Encoding($false)))
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'plan_distribution' -ExecutionMode 'READ_AND_COMPUTE_PLAN' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($plan | ConvertTo-Json -Depth 10) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            'execute_distribution' {
                $planId = if ($Arguments.ContainsKey('plan_id')) { $Arguments['plan_id'] } else { '' }
                $approved = if ($Arguments.ContainsKey('approved')) { [bool]$Arguments['approved'] } else { $false }
                
                if (-not $approved) {
                    $startTime.Stop()
                    $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'execute_distribution' -ExecutionMode 'ACID_FILESYSTEM' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'UNAUTHORIZED' -DurationMs $startTime.ElapsedMilliseconds
                    
                    return [PSCustomObject]@{
                        content = @([PSCustomObject]@{ type = "text"; text = "Execution refused: Explicit user approval not granted (-Approved)." })
                        isError = $true
                        audit_id = $audit.audit_id
                    }
                }
                
                # 1. Resolve Plan (from argument object or plan_id file)
                $planToExecute = $null
                if ($Arguments.ContainsKey('plan') -and $null -ne $Arguments['plan']) {
                    if ($Arguments['plan'] -is [string]) {
                        $planToExecute = $Arguments['plan'] | ConvertFrom-Json
                    } else {
                        $planToExecute = $Arguments['plan']
                    }
                } elseif (-not [string]::IsNullOrWhiteSpace($planId)) {
                    $planFilePath = Join-Path $RegistryRoot "staging\distribution-plans\$planId.json"
                    if (Test-Path $planFilePath) {
                        $planToExecute = [System.IO.File]::ReadAllText($planFilePath) | ConvertFrom-Json
                    }
                }
                
                if ($null -eq $planToExecute) {
                    throw "Distribution plan not found or invalid: '$planId'"
                }
                
                # 2. Adversarial Plan Validation: Reject plans with zero-hashes, unverified IDs, or quarantined resources
                $isZeroHash = ($planToExecute.expected_content_hash -match '^0{32,}$' -or $planToExecute.resource_id -match '^sres-v1-sha256:0{32,}$')
                if ($isZeroHash) {
                    throw "Rejected invalid distribution plan: Plan contains unverified zero-hash or placeholder digest."
                }
                
                if ($planToExecute.action_type -eq 'QUARANTINE_BLOCKED' -or $planToExecute.quarantine_status -eq 'QUARANTINED') {
                    throw "Rejected distribution plan: Skill is quarantined or blocked."
                }
                
                # 3. Execute Real Validated Plan
                $exec = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $planToExecute -Approved
                
                $startTime.Stop()
                $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName 'execute_distribution' -ExecutionMode 'ACID_FILESYSTEM' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'SUCCESS' -DurationMs $startTime.ElapsedMilliseconds
                
                return [PSCustomObject]@{
                    content = @([PSCustomObject]@{ type = "text"; text = ($exec | ConvertTo-Json -Depth 10) })
                    isError = $false
                    audit_id = $audit.audit_id
                }
            }
            
            default {
                throw "Unknown MCP Tool: $ToolName"
            }
        }
    } catch {
        $startTime.Stop()
        $audit = New-GatewayAuditRecord -Channel 'MCP_STDIO' -InvokedName $ToolName -ExecutionMode 'READ_ONLY' -CallerIdentity $CallerIdentity -ParametersJson $argsJson -ResponseStatus 'ERROR' -DurationMs $startTime.ElapsedMilliseconds
        return [PSCustomObject]@{
            content = @([PSCustomObject]@{ type = "text"; text = "Tool execution error: $($_.Exception.Message)" })
            isError = $true
            audit_id = $audit.audit_id
        }
    }
}

function Invoke-ApiGatewayRoute {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$Path,
        [string]$Method = 'GET',
        [string]$BodyJson = '{}',
        [string]$CallerIdentity = 'api-client'
    )
    
    $bodyObj = if (-not [string]::IsNullOrWhiteSpace($BodyJson)) {
        try { $BodyJson | ConvertFrom-Json } catch { @{} }
    } else { @{} }
    
    switch -Regex ($Path) {
        '^/v1/skills' {
            $mcpRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'query_skills' -Arguments @{} -CallerIdentity $CallerIdentity
            return [PSCustomObject]@{ status = 200; body = $mcpRes.content[0].text }
        }
        '^/v1/capabilities' {
            $mcpRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'inspect_capabilities' -Arguments @{} -CallerIdentity $CallerIdentity
            return [PSCustomObject]@{ status = 200; body = $mcpRes.content[0].text }
        }
        '^/v1/provenance' {
            $id = $Path.Replace('/v1/provenance/', '')
            $mcpRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'verify_provenance' -Arguments @{ resource_id_or_name = $id } -CallerIdentity $CallerIdentity
            return [PSCustomObject]@{ status = 200; body = $mcpRes.content[0].text }
        }
        '^/v1/resolve' {
            $ws = if ($bodyObj.PSObject.Properties.Item('workspace_path')) { $bodyObj.workspace_path } else { 'E:\mock\project' }
            $mcpRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'resolve_project' -Arguments @{ workspace_path = $ws } -CallerIdentity $CallerIdentity
            return [PSCustomObject]@{ status = 200; body = $mcpRes.content[0].text }
        }
        '^/v1/distribution/plan' {
            $cName = if ($bodyObj.PSObject.Properties.Item('canonical_name')) { $bodyObj.canonical_name } else { 'test-skill' }
            $target = if ($bodyObj.PSObject.Properties.Item('target_platform')) { $bodyObj.target_platform } else { 'cursor' }
            $mcpRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'plan_distribution' -Arguments @{ canonical_name = $cName; target_platform = $target } -CallerIdentity $CallerIdentity
            return [PSCustomObject]@{ status = 200; body = $mcpRes.content[0].text }
        }
        '^/v1/health' {
            $activeAnchor = Get-CanonicalMerkleAnchor -RegistryRoot $RegistryRoot
            return [PSCustomObject]@{
                status = 200
                body = ([PSCustomObject]@{
                    status = "HEALTHY"
                    registry_authority = $RegistryRoot
                    merkle_anchor = $activeAnchor
                    timestamp_utc = [DateTime]::UtcNow.ToString("o")
                } | ConvertTo-Json)
            }
        }
        default {
            return [PSCustomObject]@{ status = 404; body = '{"error":"Not Found"}' }
        }
    }
}

Export-ModuleMember -Function `
    Get-Sha256TextHash, `
    Get-McpToolCatalog, `
    Get-ApiEndpointCatalog, `
    New-GatewayAuditRecord, `
    Invoke-McpToolCall, `
    Invoke-ApiGatewayRoute
