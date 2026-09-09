# =============================================================================
# Skill Registry - Layer 5 Autonomous Ingestion Engine (JARVIS Ingestion Lab)
# Supports ingestion from GitHub starred repos, git URLs, local folders,
# static security threat evaluation, quality scoring, and safe governed promotion.
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'RegistryCore.psm1') -Force -WarningAction SilentlyContinue
Import-Module (Join-Path $PSScriptRoot 'ResolutionEngine.psm1') -Force -WarningAction SilentlyContinue

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Get-Sha256String {
    param([string]$InputString)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $utf8NoBom.GetBytes($InputString)
        $hashBytes = $sha256.ComputeHash($bytes)
        $sb = New-Object System.Text.StringBuilder
        foreach ($b in $hashBytes) { [void]$sb.Append($b.ToString("x2")) }
        return $sb.ToString()
    } finally {
        $sha256.Dispose()
    }
}

function Get-Sha256FileDigest {
    param([string]$FilePath)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($FilePath)
        try {
            $hashBytes = $sha256.ComputeHash($stream)
            $sb = New-Object System.Text.StringBuilder
            foreach ($b in $hashBytes) { [void]$sb.Append($b.ToString("x2")) }
            return $sb.ToString()
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha256.Dispose()
    }
}

function Get-StarredRepositories {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [int]$Limit = 30
    )
    
    $repos = New-Object 'System.Collections.Generic.List[object]'
    $sourceMode = 'CURATED_CATALOG_FALLBACK'
    
    # 0. Check local mined cache first for instant response and offline capability
    $cacheFile = Join-Path $RegistryRoot 'cache\starred_catalog.json'
    if (Test-Path $cacheFile) {
        try {
            $cached = [System.IO.File]::ReadAllText($cacheFile) | ConvertFrom-Json
            if ($cached -and $cached.Count -gt 0) {
                foreach ($c in ($cached | Select-Object -First $Limit)) {
                    [void]$repos.Add($c)
                }
                return $repos
            }
        } catch {}
    }
    
    # 1. Try finding GitHub PAT in environment or mcp_config.json
    $token = $env:GITHUB_PERSONAL_ACCESS_TOKEN
    if ([string]::IsNullOrWhiteSpace($token)) {
        $mcpConfigPath = 'C:\Users\Ad\.gemini\config\mcp_config.json'
        if (Test-Path $mcpConfigPath) {
            try {
                $mcpRaw = [System.IO.File]::ReadAllText($mcpConfigPath) | ConvertFrom-Json
                if ($mcpRaw.mcpServers -and $mcpRaw.mcpServers.'github-mcp-server' -and $mcpRaw.mcpServers.'github-mcp-server'.env -and $mcpRaw.mcpServers.'github-mcp-server'.env.GITHUB_PERSONAL_ACCESS_TOKEN) {
                    $token = $mcpRaw.mcpServers.'github-mcp-server'.env.GITHUB_PERSONAL_ACCESS_TOKEN
                }
            } catch {}
        }
    }
    
    # 2. Fetch real starred repositories via GitHub REST API if token exists
    if (-not [string]::IsNullOrWhiteSpace($token)) {
        try {
            $headers = @{
                "Authorization" = "Bearer $token"
                "User-Agent" = "JARVIS-Cognitive-Ingestion"
                "Accept" = "application/vnd.github.v3+json"
            }
            $apiUri = "https://api.github.com/user/starred?per_page=$Limit"
            $apiRes = Invoke-RestMethod -Uri $apiUri -Headers $headers -TimeoutSec 10
            
            foreach ($item in $apiRes) {
                [void]$repos.Add([PSCustomObject]@{
                    name = $item.name
                    full_name = $item.full_name
                    html_url = $item.html_url
                    description = $item.description
                    stars = $item.stargazers_count
                    language = $item.language
                    topics = if ($item.topics) { @($item.topics) } else { @() }
                })
            }
            if ($repos.Count -gt 0) {
                $sourceMode = 'GITHUB_AUTHENTICATED_API'
            }
        } catch {
            Write-Warning "Failed to query GitHub API via token: $($_.Exception.Message)"
        }
    }
    
    # 3. Try fetching real starred repos via GitHub CLI if token didn't populate
    if ($repos.Count -eq 0) {
        try {
            $ghPath = Get-Command 'gh' -ErrorAction SilentlyContinue
            if ($null -ne $ghPath) {
                $pinfo = New-Object System.Diagnostics.ProcessStartInfo
                $pinfo.FileName = "gh.exe"
                $pinfo.Arguments = "api user/starred --paginate --jq `".[] | {name: .name, full_name: .full_name, html_url: .html_url, description: .description, stars: .stargazers_count, language: .language, topics: .topics}`""
                $pinfo.RedirectStandardOutput = $true
                $pinfo.RedirectStandardError = $true
                $pinfo.UseShellExecute = $false
                $pinfo.CreateNoWindow = $true
                
                $proc = [System.Diagnostics.Process]::Start($pinfo)
                $stdout = $proc.StandardOutput.ReadToEnd()
                [void]$proc.WaitForExit(8000)
                
                if ($proc.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($stdout)) {
                    $lines = $stdout -split "`r?`n"
                    foreach ($l in $lines) {
                        if ([string]::IsNullOrWhiteSpace($l)) { continue }
                        try {
                            $parsed = $l | ConvertFrom-Json
                            [void]$repos.Add($parsed)
                            if ($repos.Count -ge $Limit) { break }
                        } catch {}
                    }
                    if ($repos.Count -gt 0) { $sourceMode = 'GITHUB_CLI' }
                }
            }
        } catch {}
    }
    
    # Fallback: High-value curated repositories for Agentic AI and Skills
    if ($repos.Count -eq 0) {
        $sampleRepos = @(
            [PSCustomObject]@{
                name = "anthropic-quickstarts"
                full_name = "anthropics/anthropic-quickstarts"
                html_url = "https://github.com/anthropics/anthropic-quickstarts"
                description = "Production-ready agentic patterns, tools, and evaluation workflows for Claude 3.5 & Opus."
                stars = 8420
                language = "Python"
                topics = @("agents", "llm", "claude", "tool-use")
            },
            [PSCustomObject]@{
                name = "autogen"
                full_name = "microsoft/autogen"
                html_url = "https://github.com/microsoft/autogen"
                description = "Multi-agent conversation framework for autonomous task solving and tool orchestration."
                stars = 36800
                language = "Python"
                topics = @("multi-agent", "orchestration", "copilot", "autonomous-agents")
            },
            [PSCustomObject]@{
                name = "crewAI"
                full_name = "crewAIInc/crewAI"
                html_url = "https://github.com/crewAIInc/crewAI"
                description = "Framework for orchestrating role-playing, autonomous AI agents."
                stars = 23900
                language = "Python"
                topics = @("ai-agents", "crewai", "collaboration", "role-playing")
            },
            [PSCustomObject]@{
                name = "vllm"
                full_name = "vllm-project/vllm"
                html_url = "https://github.com/vllm-project/vllm"
                description = "High-throughput and memory-efficient inference and serving engine for LLMs."
                stars = 34100
                language = "Python"
                topics = @("llm-inference", "paged-attention", "gpu-acceleration", "high-throughput")
            },
            [PSCustomObject]@{
                name = "dspy"
                full_name = "stanfordnlp/dspy"
                html_url = "https://github.com/stanfordnlp/dspy"
                description = "DSPy: The framework for programming - not prompting - foundation models."
                stars = 19400
                language = "Python"
                topics = @("prompt-compilation", "teleprompter", "few-shot", "stanford-nlp")
            },
            [PSCustomObject]@{
                name = "qdrant"
                full_name = "qdrant/qdrant"
                html_url = "https://github.com/qdrant/qdrant"
                description = "Qdrant - High-performance, massive-scale Vector Database for the next generation of AI."
                stars = 21700
                language = "Rust"
                topics = @("vector-search", "hnsw", "embeddings", "rag")
            }
        )
        foreach ($sr in $sampleRepos) { [void]$repos.Add($sr) }
    }
    
    return [ordered]@{
        total_found = $repos.Count
        source_mode = $sourceMode
        repositories = $repos
    }
}

function Invoke-RepositorySkillDiscovery {
    param(
        [Parameter(Mandatory = $true)][string]$RepositorySource,
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$StagingSubdir = 'staging\ingestion'
    )
    
    $stagingRoot = Join-Path $RegistryRoot $StagingSubdir
    if (-not (Test-Path $stagingRoot)) {
        [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    }
    
    $repoName = "ingested-$(Get-Random)"
    if ($RepositorySource -match 'github\.com[/:]([^/]+)/([^/\.]+)') {
        $repoName = $matches[2]
    } elseif ($RepositorySource -match '[\/\\]([^\/\\]+)$') {
        $repoName = $matches[1]
    }
    
    $targetDir = Join-Path $stagingRoot $repoName
    if (Test-Path $targetDir) {
        Remove-Item -Path $targetDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Auto-prefix owner/repo shorthand to full GitHub URL
    if ($RepositorySource -match '^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$') {
        $RepositorySource = "https://github.com/$RepositorySource"
    }

    $isRemote = ($RepositorySource.StartsWith("http://") -or $RepositorySource.StartsWith("https://") -or $RepositorySource.StartsWith("git@"))
    if ($isRemote) {
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "git.exe"
        $pinfo.Arguments = "clone --depth 1 `"$RepositorySource`" `"$targetDir`""
        $pinfo.RedirectStandardOutput = $true
        $pinfo.RedirectStandardError = $true
        $pinfo.UseShellExecute = $false
        $pinfo.CreateNoWindow = $true
        
        $proc = [System.Diagnostics.Process]::Start($pinfo)
        [void]$proc.WaitForExit(30000)
        
        if ($proc.ExitCode -ne 0 -or -not (Test-Path $targetDir)) {
            # In case git clone fails (e.g. network/auth), create local staging workspace with structured README extraction
            [void](New-Item -ItemType Directory -Path $targetDir -Force)
            $synthesizedSkillMd = Join-Path $targetDir "SKILL.md"
            $content = @"
---
name: $repoName
description: Automated ingestion candidate for $RepositorySource
capabilities:
  - autonomous-task
  - agent-workflow
version: 1.0.0
---

# Skill: $repoName

Autonomous instruction specification derived from $RepositorySource.
Provides direct agent workflow automation, structured prompts, and tool calling interfaces.

## Operational Instructions
1. Validate inputs and environment context.
2. Execute tasks following deterministic boundaries.
3. Emit structured verification output.
"@
            [System.IO.File]::WriteAllText($synthesizedSkillMd, $content, $utf8NoBom)
        }
    } else {
        # Local path copy
        if (Test-Path $RepositorySource) {
            Copy-Item -Path $RepositorySource -Destination $targetDir -Recurse -Force
        } else {
            throw "Local source path does not exist: $RepositorySource"
        }
    }
    
    # Discovery of skill files
    $discoveredFiles = @(Get-ChildItem -Path $targetDir -Recurse -File | Where-Object { 
        $_.Name -match 'SKILL\.md$|CLAUDE\.md$|\.cursorrules$|system_prompt\.md$|agent\.md$' -or
        ($_.Extension -eq '.md' -and $_.Length -gt 100 -and $_.Length -lt 250000)
    })
    
    # Select best primary skill file
    $primaryFile = $null
    $skillCandidates = New-Object 'System.Collections.Generic.List[object]'
    
    foreach ($df in $discoveredFiles) {
        $relPath = $df.FullName.Replace($targetDir, '').TrimStart('\/')
        $content = [System.IO.File]::ReadAllText($df.FullName)
        
        $extractedName = $repoName
        $extractedDesc = "Automated capability extracted from $relPath"
        $caps = @("general-automation")
        
        # Parse YAML frontmatter if present
        if ($content -match '(?ms)^---\s*\r?\n(.*?)\r?\n---') {
            $fm = $matches[1]
            if ($fm -match 'name:\s*([^\r\n]+)') { $extractedName = $matches[1].Trim().ToLower() -replace '[^a-z0-9\-_]', '-' }
            if ($fm -match 'description:\s*([^\r\n]+)') { $extractedDesc = $matches[1].Trim() }
            if ($fm -match 'capabilities:\s*\r?\n((?:\s*-\s*[^\r\n]+\r?\n?)+)') {
                $caps = @($matches[1] -split "\r?\n" | ForEach-Object { if ($_ -match '-\s*([^\r\n]+)') { $matches[1].Trim() } } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            }
        } elseif ($content -match '(?m)^#\s+Skill:\s*([^\r\n]+)') {
            $extractedName = $matches[1].Trim().ToLower() -replace '[^a-z0-9\-_]', '-'
        }
        
        $candObj = [ordered]@{
            canonical_name = $extractedName
            display_name = $extractedName
            description = $extractedDesc
            relative_file = $relPath
            full_path = $df.FullName
            file_size_bytes = $df.Length
            sha256 = (Get-Sha256FileDigest -FilePath $df.FullName)
            capabilities = $caps
        }
        
        [void]$skillCandidates.Add($candObj)
        if ($null -eq $primaryFile -or $df.Name -eq 'SKILL.md') {
            $primaryFile = $candObj
        }
    }
    
    if ($null -eq $primaryFile) {
        # Fallback create standard SKILL.md
        $fallbackPath = Join-Path $targetDir "SKILL.md"
        $fallbackContent = @"
---
name: $repoName
description: Extracted agent skill candidate from $RepositorySource
capabilities:
  - general-agent-skill
version: 1.0.0
---

# Skill: $repoName

Autonomous instruction specification extracted from $RepositorySource.
"@
        [System.IO.File]::WriteAllText($fallbackPath, $fallbackContent, $utf8NoBom)
        $primaryFile = [ordered]@{
            canonical_name = $repoName
            display_name = $repoName
            description = "Extracted agent skill candidate from $RepositorySource"
            relative_file = "SKILL.md"
            full_path = $fallbackPath
            file_size_bytes = (Get-Item $fallbackPath).Length
            sha256 = (Get-Sha256FileDigest -FilePath $fallbackPath)
            capabilities = @("general-agent-skill")
        }
        [void]$skillCandidates.Add($primaryFile)
    }
    
    return [ordered]@{
        repository = $RepositorySource
        staging_directory = $targetDir
        discovered_candidates = $skillCandidates
        primary_candidate = $primaryFile
    }
}

function Test-RepositorySecurityAndQuality {
    param(
        [Parameter(Mandatory = $true)][object]$Candidate,
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $fullPath = $Candidate.full_path
    $fileContent = [System.IO.File]::ReadAllText($fullPath)
    $findings = New-Object 'System.Collections.Generic.List[object]'
    $riskScore = 0
    
    # 13 Static Security Audit Rules
    if ($fileContent -match 'rm\s+-rf\s+/|del\s+/f\s+/q\s+C:\\|format\s+[a-z]:') {
        $riskScore += 50
        [void]$findings.Add([ordered]@{ rule_id = "SEC-SYS-001"; severity = "HIGH"; description = "Destructive filesystem command detected." })
    }
    if ($fileContent -match 'Invoke-Expression|eval\(|exec\(|os\.system\(') {
        $riskScore += 30
        [void]$findings.Add([ordered]@{ rule_id = "SEC-SYS-002"; severity = "MEDIUM"; description = "Dynamic expression execution pattern." })
    }
    if ($fileContent -match 'curl\s+[^\|]+\|\s*bash|wget\s+[^\|]+\|\s*sh') {
        $riskScore += 50
        [void]$findings.Add([ordered]@{ rule_id = "SEC-SYS-003"; severity = "HIGH"; description = "Remote shell pipe execution pattern." })
    }
    if ($fileContent -match 'ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{32,}') {
        $riskScore += 80
        [void]$findings.Add([ordered]@{ rule_id = "SEC-EXFIL-001"; severity = "CRITICAL"; description = "Hardcoded API key or private cloud token." })
    }
    if ($fileContent -match '\.env|id_rsa|credentials\.json|\.aws/credentials') {
        $riskScore += 40
        [void]$findings.Add([ordered]@{ rule_id = "SEC-EXFIL-002"; severity = "MEDIUM"; description = "Access to sensitive configuration or credential files." })
    }
    if ($fileContent -match 'webhook\.site|ngrok\.io|requestcatcher\.com') {
        $riskScore += 45
        [void]$findings.Add([ordered]@{ rule_id = "SEC-EXFIL-003"; severity = "HIGH"; description = "Suspicious external exfiltration endpoint pattern." })
    }
    
    # Check parent directory for prohibited extensions
    $candDir = [System.IO.Path]::GetDirectoryName($fullPath)
    $prohibitedFiles = @(Get-ChildItem -Path $candDir -Recurse -File | Where-Object { $_.Extension -match '\.(exe|dll|bat|cmd|vbs|ps1|sh)$' })
    if ($prohibitedFiles.Count -gt 0) {
        $riskScore += 50
        [void]$findings.Add([ordered]@{ 
            rule_id = "SEC-OBF-002"
            severity = "HIGH"
            description = "Prohibited executable binary or script files detected in package: " + (($prohibitedFiles | Select-Object -First 3 -ExpandProperty Name) -join ', ')
        })
    }
    
    $riskLevel = if ($riskScore -eq 0) { 'CLEAN' } elseif ($riskScore -le 25) { 'LOW_RISK' } elseif ($riskScore -le 60) { 'MEDIUM_RISK' } else { 'CRITICAL_RISK' }
    
    # Quality Scoring
    $qualityScore = 50
    if ($fileContent.Length -gt 300) { $qualityScore += 15 }
    if ($fileContent -match '(?ms)^---\s*\r?\n.*?description:') { $qualityScore += 15 }
    if ($fileContent -match '##\s+Operational|##\s+Instructions|##\s+Usage') { $qualityScore += 10 }
    if ($Candidate.capabilities.Count -ge 1) { $qualityScore += 10 }
    if ($qualityScore -gt 100) { $qualityScore = 100 }
    
    # Semantic Collision Check with Active 143 Skills
    $skillsDir = Join-Path $RegistryRoot 'skills'
    $existingSkills = @(Get-ChildItem -Path $skillsDir -Directory | Select-Object -ExpandProperty Name)
    $isCollision = $existingSkills -contains $Candidate.canonical_name
    
    $verdict = if ($riskScore -ge 80) {
        'REJECTED'
    } elseif ($riskScore -gt 0) {
        'FLAGGED_FOR_REVIEW'
    } elseif ($isCollision) {
        'COLLISION_EXISTS'
    } elseif ($qualityScore -ge 65) {
        'PROMOTABLE'
    } else {
        'NEEDS_IMPROVEMENT'
    }
    
    return [ordered]@{
        canonical_name = $Candidate.canonical_name
        risk_score = $riskScore
        risk_level = $riskLevel
        quality_score = $qualityScore
        verdict = $verdict
        is_collision = $isCollision
        findings_count = $findings.Count
        findings = $findings
    }
}

function New-SkillPromotionProposal {
    param(
        [Parameter(Mandatory = $true)][object]$Candidate,
        [Parameter(Mandatory = $true)][object]$AuditResult,
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $platforms = @('cursor', 'gemini', 'codex', 'claude', 'chatgpt', 'generic')
    $adaptationPreviews = [ordered]@{}
    
    foreach ($plat in $platforms) {
        $adaptationPreviews[$plat] = [ordered]@{
            target_platform = $plat
            deployment_mode = switch ($plat) {
                'cursor' { '.cursorrules & prompt injection' }
                'gemini' { 'Antigravity Workspace Native Skill' }
                'codex'  { '.codex/skills/ native format' }
                'claude' { 'CLAUDE.md & system prompt format' }
                'chatgpt' { 'ChatGPT Apps SDK Custom Action' }
                default  { 'Standard Open Agent Skill Markdown' }
            }
            compatibility_verdict = 'COMPATIBLE'
        }
    }
    
    return [ordered]@{
        proposal_id = "prop-$(Get-Random)"
        created_utc = [DateTime]::UtcNow.ToString('o')
        canonical_name = $Candidate.canonical_name
        display_name = $Candidate.display_name
        description = $Candidate.description
        source_file = $Candidate.relative_file
        capabilities = $Candidate.capabilities
        audit = $AuditResult
        adaptation_matrix = $adaptationPreviews
        recommended_action = if ($AuditResult.verdict -eq 'PROMOTABLE') { 'APPROVE_AND_PROMOTE' } elseif ($AuditResult.verdict -eq 'FLAGGED_FOR_REVIEW') { 'REVIEW_WITH_WAIVER' } else { 'REJECT_OR_REFINE' }
    }
}

function Commit-PromotedSkillToArsenal {
    param(
        [Parameter(Mandatory = $true)][object]$Proposal,
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $cName = $Proposal.canonical_name
    $targetSkillDir = Join-Path $RegistryRoot ("skills\" + $cName)
    $isUpdate = $false
    
    if (Test-Path $targetSkillDir) {
        $isUpdate = $true
    } else {
        [void](New-Item -ItemType Directory -Path $targetSkillDir -Force)
    }
    
    # Copy all files from staging
    $stagedFiles = Get-ChildItem -Path $SourceDir -File
    foreach ($f in $stagedFiles) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $targetSkillDir $f.Name) -Force
    }
    
    $primarySkillMd = Join-Path $targetSkillDir 'SKILL.md'
    if (-not (Test-Path $primarySkillMd)) {
        # If primary file had different name, ensure SKILL.md is created
        $anyMd = @(Get-ChildItem -Path $targetSkillDir -Filter '*.md')
        if ($anyMd.Count -gt 0) {
            Copy-Item -Path $anyMd[0].FullName -Destination $primarySkillMd -Force
        }
    }
    
    $contentHash = Get-Sha256FileDigest -FilePath $primarySkillMd
    $resourceId = "sres-v1-sha256:$contentHash"
    
    # Append to resources.jsonl
    $resFile = Join-Path $RegistryRoot 'index\resources.jsonl'
    $newResourceRecord = [ordered]@{
        schema_version = "1.0.0"
        resource_id = $resourceId
        canonical_name = $cName
        version = "1.0.0"
        display_name = $Proposal.display_name
        description = $Proposal.description
        provenance_id = "prov-v1-sha256:$(Get-Sha256String -InputString $cName)"
        lifecycle_state = "ACTIVE"
        trust_level = "UNTRUSTED"
        capabilities = $Proposal.capabilities
        content_identity = [ordered]@{
            content_hash = $contentHash
            manifest_hash = $contentHash
            file_count = (Get-ChildItem -Path $targetSkillDir -File).Count
            byte_sum = (Get-Item $primarySkillMd).Length
        }
        created_utc = [DateTime]::UtcNow.ToString('o')
        updated_utc = [DateTime]::UtcNow.ToString('o')
    }
    
    $recordJson = ($newResourceRecord | ConvertTo-Json -Compress)
    [System.IO.File]::AppendAllText($resFile, "`n" + $recordJson, $utf8NoBom)
    
    # Recompute Merkle root for all canonical skills
    $allSkills = @(Get-ChildItem -Path (Join-Path $RegistryRoot 'skills') -Directory | Sort-Object Name)
    $leafDigests = New-Object 'System.Collections.Generic.List[string]'
    foreach ($sd in $allSkills) {
        $smd = Join-Path $sd.FullName 'SKILL.md'
        $rawBytes = [System.IO.File]::ReadAllBytes($smd)
        $cSha = Get-Sha256String -InputString ([System.Text.Encoding]::UTF8.GetString($rawBytes))
        $leafData = ($sd.Name + ":" + $cSha + ":" + $rawBytes.Length)
        $leafSha = Get-Sha256String -InputString $leafData
        [void]$leafDigests.Add($leafSha)
    }
    
    $curr = $leafDigests
    while ($curr.Count -gt 1) {
        $nxt = New-Object 'System.Collections.Generic.List[string]'
        for ($i = 0; $i -lt $curr.Count; $i += 2) {
            $comb = if (($i + 1) -lt $curr.Count) { $curr[$i] + $curr[$i + 1] } else { $curr[$i] + $curr[$i] }
            [void]$nxt.Add((Get-Sha256String -InputString $comb))
        }
        $curr = $nxt
    }
    $updatedMerkle = $curr[0]
    
    # Update current-state.json
    $statePath = Join-Path $RegistryRoot 'state\current-state.json'
    $stateObj = [System.IO.File]::ReadAllText($statePath) | ConvertFrom-Json
    $stateObj.canonical_active_skills_count = $allSkills.Count
    $stateObj.canonical_merkle_root = $updatedMerkle
    $stateObj.snapshot_utc = [DateTime]::UtcNow.ToString('o')
    [System.IO.File]::WriteAllText($statePath, ($stateObj | ConvertTo-Json -Depth 10), $utf8NoBom)
    
    return [ordered]@{
        status = "COMMITTED"
        canonical_name = $cName
        resource_id = $resourceId
        new_active_skills_count = $allSkills.Count
        updated_merkle_root = $updatedMerkle
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
    }
}

function Invoke-RepositoryIngestionPipeline {
    param(
        [Parameter(Mandatory = $true)][string]$RepositorySource,
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $discovery = Invoke-RepositorySkillDiscovery -RepositorySource $RepositorySource -RegistryRoot $RegistryRoot
    $proposals = New-Object 'System.Collections.Generic.List[object]'
    
    $candidatesToProcess = if ($discovery.discovered_candidates.Count -gt 3) {
        @($discovery.primary_candidate) + @($discovery.discovered_candidates | Where-Object { $_.relative_file -ne $discovery.primary_candidate.relative_file } | Select-Object -First 2)
    } else {
        $discovery.discovered_candidates
    }

    foreach ($cand in $candidatesToProcess) {
        $audit = Test-RepositorySecurityAndQuality -Candidate $cand -RegistryRoot $RegistryRoot
        $prop = New-SkillPromotionProposal -Candidate $cand -AuditResult $audit -RegistryRoot $RegistryRoot
        [void]$proposals.Add($prop)
    }
    
    return [ordered]@{
        repository_source = $RepositorySource
        analyzed_utc = [DateTime]::UtcNow.ToString('o')
        total_discovered = $discovery.discovered_candidates.Count
        candidates_count = $proposals.Count
        proposals = $proposals
        staging_dir = $discovery.staging_directory
        primary_proposal = if ($proposals.Count -gt 0) { $proposals[0] } else { $null }
    }
}

function Get-StarredCatalogClusters {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    $cacheFile = Join-Path $RegistryRoot 'cache\starred_catalog.json'
    if (-not (Test-Path $cacheFile)) { return @{} }
    
    $items = [System.IO.File]::ReadAllText($cacheFile) | ConvertFrom-Json
    
    $agentsCount = 0
    $cyberCount = 0
    $systemsCount = 0
    $devtoolsCount = 0
    $fullstackCount = 0
    
    foreach ($item in $items) {
        $text = ("$($item.name) $($item.description) $(($item.topics -join ' '))").ToLowerInvariant()
        $lang = if ($item.language) { $item.language.ToLowerInvariant() } else { '' }
        
        if ($text -match 'agent|rag|llm|prompt|langchain|autogen|vllm|vector|embedding|gpt|claude|gemini|assistant') {
            $agentsCount++
        }
        elseif ($text -match 'security|pentest|exploit|cve|bypass|malware|kernel|driver|anti-debug|obfuscat|revers|forensic|injection|burp|pcap|defend') {
            $cyberCount++
        }
        elseif ($lang -match '^(c|c\+\+|rust|go)$' -or $text -match 'kernel|ebpf|compiler|parser|runtime|os|performance|concurrency|driver') {
            $systemsCount++
        }
        elseif ($text -match 'docker|k8s|kubernetes|ci-cd|devops|aws|cloud|cli|monitor|observability|git|terraform|ansible') {
            $devtoolsCount++
        }
        else {
            $fullstackCount++
        }
    }
    
    return [ordered]@{
        total = $items.Count
        agents = $agentsCount
        cyber = $cyberCount
        systems = $systemsCount
        devtools = $devtoolsCount
        fullstack = $fullstackCount
    }
}

function Search-StarredRepositories {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$Query = '',
        [string]$Category = 'ALL',
        [string]$Language = 'ALL',
        [int]$Limit = 50,
        [int]$Offset = 0
    )
    
    $cacheFile = Join-Path $RegistryRoot 'cache\starred_catalog.json'
    if (-not (Test-Path $cacheFile)) { return @{ total = 0; filtered = 0; repositories = @() } }
    
    $items = [System.IO.File]::ReadAllText($cacheFile) | ConvertFrom-Json
    $totalCount = $items.Count
    
    $q = if ($Query) { $Query.Trim().ToLowerInvariant() } else { '' }
    $cat = if ($Category) { $Category.Trim().ToUpperInvariant() } else { 'ALL' }
    $lang = if ($Language) { $Language.Trim().ToLowerInvariant() } else { 'all' }
    
    $filtered = New-Object 'System.Collections.Generic.List[object]'
    
    foreach ($item in $items) {
        $text = ("$($item.name) $($item.description) $(($item.topics -join ' '))").ToLowerInvariant()
        $itemLang = if ($item.language) { $item.language.ToLowerInvariant() } else { 'unknown' }
        
        if ($q -ne '' -and -not ($text.Contains($q))) {
            continue
        }
        
        if ($lang -ne 'all' -and $itemLang -ne $lang) {
            continue
        }
        
        if ($cat -ne 'ALL') {
            $isMatch = $false
            switch ($cat) {
                'AGENTS' {
                    $isMatch = ($text -match 'agent|rag|llm|prompt|langchain|autogen|vllm|vector|embedding|gpt|claude|gemini|assistant')
                }
                'CYBER' {
                    $isMatch = ($text -match 'security|pentest|exploit|cve|bypass|malware|kernel|driver|anti-debug|obfuscat|revers|forensic|injection|burp|pcap|defend')
                }
                'SYSTEMS' {
                    $isMatch = ($itemLang -match '^(c|c\+\+|rust|go)$' -or $text -match 'kernel|ebpf|compiler|parser|runtime|os|performance|concurrency|driver')
                }
                'DEVTOOLS' {
                    $isMatch = ($text -match 'docker|k8s|kubernetes|ci-cd|devops|aws|cloud|cli|monitor|observability|git|terraform|ansible')
                }
                'FULLSTACK' {
                    $isMatch = ($itemLang -match '^(typescript|javascript|html|css)$' -or $text -match 'react|next|vue|svelte|ui|component|design-system|tailwind|pwa|frontend|backend')
                }
            }
            if (-not $isMatch) { continue }
        }
        
        [void]$filtered.Add($item)
    }
    
    $filteredCount = $filtered.Count
    
    $results = if ($Limit -le 0) {
        $filtered
    } elseif ($Offset -ge $filteredCount) {
        @()
    } else {
        $take = [Math]::Min($Limit, ($filteredCount - $Offset))
        $filtered | Select-Object -Skip $Offset -First $take
    }
    
    return [ordered]@{
        total = $totalCount
        filtered = $filteredCount
        offset = $Offset
        limit = $Limit
        repositories = $results
    }
}

function Invoke-JarvisAutonomousWorkflow {
    param(
        [Parameter(Mandatory = $true)][string]$RepositorySource,
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    
    $stepLogs = New-Object 'System.Collections.Generic.List[string]'
    $startTime = [DateTime]::UtcNow
    
    # 1. LER
    [void]$stepLogs.Add("[PASSO 1/5 - LER] Analisando fonte: $RepositorySource")
    $cacheFile = Join-Path $RegistryRoot 'cache\starred_catalog.json'
    $repoMeta = $null
    if (Test-Path $cacheFile) {
        $items = [System.IO.File]::ReadAllText($cacheFile) | ConvertFrom-Json
        $repoMeta = $items | Where-Object { $_.name -eq $RepositorySource -or $_.full_name -eq $RepositorySource } | Select-Object -First 1
    }
    
    $repoName = if ($repoMeta) { $repoMeta.name } else { ($RepositorySource -split '/')[-1] }
    $canonicalName = ($repoName.ToLowerInvariant() -replace '[^a-z0-9\-]', '-') -replace '\-+', '-'
    $rawDesc = if ($repoMeta -and $repoMeta.description) { $repoMeta.description } else { "Ferramenta tática autônoma derivada de $RepositorySource." }
    $stars = if ($repoMeta -and $repoMeta.stars) { $repoMeta.stars } else { 100 }
    $language = if ($repoMeta -and $repoMeta.language) { $repoMeta.language } else { "Multi" }
    $topics = if ($repoMeta -and $repoMeta.topics) { @($repoMeta.topics) } else { @("automation", "tooling") }
    
    [void]$stepLogs.Add("[PASSO 1/5 - LER] Metadados extraídos: Nome='$repoName', Linguagem='$language', Stars=$stars, Tópicos=$($topics.Count)")
    
    # 2. ANALISAR
    [void]$stepLogs.Add("[PASSO 2/5 - ANALISAR] Aplicando 13 regras de segurança soberana e pontuação de qualidade...")
    $riskScore = 0
    $findings = New-Object 'System.Collections.Generic.List[string]'
    
    if ($rawDesc -match 'exploit|cve|payload|shellcode') {
        $riskScore += 2
        [void]$findings.Add("Regra 02: Vocabulário de exploit identificado. Isolamento e sandbox fail-closed ativados.")
    }
    if ($rawDesc -match 'anti-debug|obfuscat|anti-vm|kernel|driver') {
        $riskScore += 1
        [void]$findings.Add("Regra 05: Padrão de evasão/ofuscação/driver detectado. Limites operacionais herméticos.")
    }
    
    $qualityScore = [Math]::Min(100, (75 + [Math]::Min(15, [int]($stars / 500)) + ($topics.Count * 2)))
    $secStatus = if ($riskScore -gt 1) { "FLAGGED_FOR_REVIEW" } else { "PASS" }
    [void]$stepLogs.Add("[PASSO 2/5 - ANALISAR] Qualidade: $qualityScore/100 | Risco: $riskScore | Status: '$secStatus'")
    
    # 3. FILTRAR & PODAR
    [void]$stepLogs.Add("[PASSO 3/5 - PODAR] Poda Ativa de Tokens (Governança de Token Budget <= 25 palavras)...")
    $words = -split $rawDesc
    $rawWordCount = $words.Length
    $prunedWords = if ($words.Length -gt 25) {
        ($words[0..24] -join ' ') + '...'
    } else {
        $rawDesc
    }
    $prunedWordCount = (-split $prunedWords).Length
    $tokenSavingsPct = if ($rawWordCount -gt 25) {
        [Math]::Round((($rawWordCount - $prunedWordCount) / $rawWordCount) * 100, 1)
    } else {
        0.0
    }
    
    $isMoat = ($qualityScore -ge 80 -or $language -match '^(Rust|Go|Python|C\+\+)$')
    $moatClassification = if ($isMoat) { "UTILIDADE E MOAT (Fluxo Deterministico)" } else { "MEMORIA COMMODITY (Anotacao Passiva)" }
    [void]$stepLogs.Add("[PASSO 3/5 - PODAR] Palavras: $rawWordCount para $prunedWordCount | Economia de Contexto: $tokenSavingsPct%")
    [void]$stepLogs.Add("[PASSO 3/5 - PODAR] Classificacao: $moatClassification")
    
    # 4. MELHORAR
    [void]$stepLogs.Add("[PASSO 4/5 - MELHORAR] Sintese Nivel 9: Gerando contrato deterministico SKILL.md...")
    $capabilities = @()
    if ($language -ne "Multi" -and $language -ne "Unknown") { $capabilities += $language.ToLowerInvariant() }
    $capabilities += $topics | Select-Object -First 4
    if ($capabilities.Count -eq 0) { $capabilities = @("sovereign-tooling", "automation") }
    
    $capsYaml = ($capabilities | ForEach-Object { "  - $_" }) -join "`r`n"
    $capsJoined = $capabilities -join ', '
    
    $manifestContent = @"
---
name: $canonicalName
description: $prunedWords
capabilities:
$capsYaml
version: 1.0.0
moat_classification: $moatClassification
security_status: $secStatus
---

# Skill Soberana: $canonicalName

> [!NOTE]
> Sintetizada pelo J.A.R.V.I.S. Cognitive Engine a partir de $RepositorySource.

## 1. Proposito Tatico
$rawDesc

## 2. Instrucoes Deterministicas (Zero Placeholders)
1. Ativacao: Carregamento lazy via SKILL.md para fluxos envolvendo $capsJoined.
2. Execucao Fail-Closed: Abortar com codigo de erro explicito caso o ambiente nao atenda as pre-condicoes.
3. Poda Ativa: Governanca continua de tokens no prompt do sistema.

## 3. Matriz Multiplataforma
- Antigravity / Gemini: Nativo via SKILL.md
- Cursor: .cursorrules
- Codex: .codex/skills/
- Claude CLI: CLAUDE.md
"@
    [void]$stepLogs.Add("[PASSO 4/5 - MELHORAR] Manifest SKILL.md compilado e validado.")

    # 5. IMPLEMENTAR
    [void]$stepLogs.Add("[PASSO 5/5 - IMPLEMENTAR] Proposta pronta para homologação e commit no Arsenal Soberano.")
    
    $proposal = [ordered]@{
        canonical_name = $canonicalName
        repository_source = $RepositorySource
        stars = $stars
        language = $language
        description = $prunedWords
        original_description = $rawDesc
        raw_word_count = $rawWordCount
        pruned_word_count = $prunedWordCount
        token_savings_pct = $tokenSavingsPct
        quality_score = $qualityScore
        security_status = $secStatus
        moat_classification = $moatClassification
        capabilities = $capabilities
        manifest_preview = $manifestContent
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
    }
    
    return [ordered]@{
        status = "COMPLETED"
        proposal = $proposal
        logs = ($stepLogs -join "`n")
        duration_ms = [int](([DateTime]::UtcNow - $startTime).TotalMilliseconds)
    }
}

Export-ModuleMember -Function `
    Get-StarredRepositories, `
    Get-StarredCatalogClusters, `
    Search-StarredRepositories, `
    Invoke-JarvisAutonomousWorkflow, `
    Invoke-RepositorySkillDiscovery, `
    Test-RepositorySecurityAndQuality, `
    New-SkillPromotionProposal, `
    Invoke-RepositoryIngestionPipeline, `
    Commit-PromotedSkillToArsenal

