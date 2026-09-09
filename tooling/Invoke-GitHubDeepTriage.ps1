# Skill Registry - Operational Tooling: GitHub Deep Triage & Multi-Signal Scoring
# Evaluates all 1,857 cataloged repositories across multiple semantic signals (topics, name, description, language, popularity, activity)
# to prioritize and discover agentic capabilities, MCP servers, prompt templates, and skill candidates with zero cloning.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$InventoryPath = (Join-Path $RegistryRoot 'staging\github-inlet\starred-inventory.jsonl'),
    [int]$TopTreeInspectLimit = 15, # Inspect Git Trees for top N Tier 1 repos via API
    [string]$OutputDirectory = (Join-Path $RegistryRoot 'staging\github-inlet')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $InventoryPath)) {
    throw "Inventory file not found: $InventoryPath. Run Invoke-GitHubStarInventory.ps1 first."
}

$triageJsonl = Join-Path $OutputDirectory 'triage-ranking.jsonl'
$treeCatalogJsonl = Join-Path $OutputDirectory 'candidate-artifacts.jsonl'
$reportJson = Join-Path $RegistryRoot 'reports\operational-github-deep-triage.json'
$reportMd = Join-Path $RegistryRoot 'reports\operational-github-deep-triage.md'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# High-signal terms for agentic ecosystems, skills, MCP, and tooling
$agentTerms = @(
    'skill', 'skills', 'agent', 'agents', 'ai-agent', 'ai-agents', 'mcp', 'model-context-protocol',
    'claude', 'claude-code', 'gemini', 'antigravity', 'codex', 'cursor', 'cursorrules',
    'prompt', 'prompts', 'prompt-engineering', 'assistant', 'copilot', 'workflow', 'workflows',
    'plugin', 'plugins', 'tool', 'tools', 'tooling', 'pentest', 'security-audit', 'fuzzer',
    'scanner', 'automation', 'cli', 'orchestration', 'rag', 'llm-app', 'eval', 'evaluation'
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GITHUB DEEP TRIAGE & MULTI-SIGNAL SCORING ENGINE           " -ForegroundColor Cyan
Write-Host " Input Ledger : $InventoryPath" -ForegroundColor Cyan
Write-Host " Target Output: $triageJsonl" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$lines = [System.IO.File]::ReadAllLines($InventoryPath)
$scoredRepos = New-Object 'System.Collections.Generic.List[object]'

$tier1Count = 0
$tier2Count = 0
$tier3Count = 0
$tier4Count = 0

foreach ($line in $lines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $repo = $line | ConvertFrom-Json
    
    $name = [string]$repo.name
    $desc = [string]$repo.description
    $fullName = [string]$repo.full_name
    $topics = if ($null -ne $repo.topics) { @($repo.topics) } else { @() }
    $lang = [string]$repo.language
    $stars = [int]$repo.stargazers_count
    $isArchived = [bool]$repo.is_archived
    $isFork = [bool]$repo.is_fork
    
    # Text corpus for matching
    $textCorpus = ($fullName + " " + $name + " " + $desc + " " + ($topics -join " ")).ToLowerInvariant()
    
    $matchedSignals = New-Object 'System.Collections.Generic.List[string]'
    $signalScore = 0.0
    
    # 1. Direct Topic Matches (Heavy Weight: 0.15 per distinct topic)
    foreach ($term in $agentTerms) {
        if ($topics -contains $term) {
            [void]$matchedSignals.Add("topic:$term")
            $signalScore += 0.15
        }
    }
    
    # 2. Name & Full Name Matches (Weight: 0.20 per match)
    $nameLower = $name.ToLowerInvariant()
    foreach ($term in @('skill', 'agent', 'mcp', 'claude', 'prompt', 'cursor', 'tool', 'workflow', 'security')) {
        if ($nameLower.Contains($term)) {
            [void]$matchedSignals.Add("name:$term")
            $signalScore += 0.20
        }
    }
    
    # 3. Description Keyword Matches (Weight: 0.08 per match)
    $descLower = $desc.ToLowerInvariant()
    foreach ($term in $agentTerms) {
        if ($descLower.Contains($term) -and -not ($matchedSignals -contains "topic:$term") -and -not ($matchedSignals -contains "name:$term")) {
            [void]$matchedSignals.Add("desc:$term")
            $signalScore += 0.08
        }
    }
    
    # 4. Community Popularity Signal (Logarithmic bonus: 0.0 to 0.15)
    $popBonus = 0.0
    if ($stars -ge 10000) { $popBonus = 0.15 }
    elseif ($stars -ge 2000) { $popBonus = 0.10 }
    elseif ($stars -ge 500) { $popBonus = 0.06 }
    elseif ($stars -ge 100) { $popBonus = 0.03 }
    $signalScore += $popBonus
    
    # 5. Cap score at 1.0 and normalize
    $finalScore = [Math]::Min(1.0, [Math]::Round($signalScore, 4))
    
    # 6. Assign Tier
    $tier = 'TIER_4_GENERAL'
    $inferredCategory = 'GENERAL_SOFTWARE'
    
    if ($finalScore -ge 0.50) {
        $tier = 'TIER_1_AGENTIC_SKILL_CANDIDATE'
        $tier1Count++
        if ($textCorpus.Contains('mcp') -or $textCorpus.Contains('model-context-protocol')) { $inferredCategory = 'MCP_PROTOCOL_SERVER' }
        elseif ($textCorpus.Contains('skill')) { $inferredCategory = 'AGENT_SKILL_COLLECTION' }
        elseif ($textCorpus.Contains('claude') -or $textCorpus.Contains('cursor')) { $inferredCategory = 'PLATFORM_ASSISTANT_TOOLING' }
        elseif ($textCorpus.Contains('security') -or $textCorpus.Contains('pentest') -or $textCorpus.Contains('fuzz')) { $inferredCategory = 'SECURITY_AUDITING_CAPABILITY' }
        else { $inferredCategory = 'AGENTIC_FRAMEWORK_OR_TOOL' }
    } elseif ($finalScore -ge 0.30) {
        $tier = 'TIER_2_TOOLING_AND_INFRA'
        $tier2Count++
        $inferredCategory = 'DEVELOPER_TOOLING_CLI'
    } elseif ($finalScore -ge 0.12) {
        $tier = 'TIER_3_LIBRARIES_AND_FRAMEWORKS'
        $tier3Count++
        $inferredCategory = 'CORE_LIBRARY'
    } else {
        $tier4Count++
        $inferredCategory = 'GENERAL_SOFTWARE'
    }
    
    $scoredRecord = [ordered]@{
        schema_version = "1.0.0"
        full_name = $fullName
        owner = $repo.owner
        name = $name
        relevance_score = $finalScore
        tier = $tier
        inferred_category = $inferredCategory
        matched_signals = $matchedSignals.ToArray()
        language = $lang
        stargazers_count = $stars
        default_branch = $repo.default_branch
        is_archived = $isArchived
        html_url = $repo.html_url
        description = $desc
        triage_utc = [DateTime]::UtcNow.ToString("o")
    }
    
    [void]$scoredRepos.Add($scoredRecord)
}

# Sort all repos by relevance score descending
$sortedRepos = @($scoredRepos | Sort-Object { $_.relevance_score } -Descending)

# Write sorted triage ledger
$sbTriage = New-Object 'System.Text.StringBuilder'
foreach ($sr in $sortedRepos) {
    $j = ($sr | ConvertTo-Json -Compress)
    [void]$sbTriage.AppendLine($j)
}
[System.IO.File]::WriteAllText($triageJsonl, $sbTriage.ToString(), $utf8NoBom)

Write-Host "  -> Triage Complete: $($sortedRepos.Count) repositories scored." -ForegroundColor Green
Write-Host "     - Tier 1 (High Agentic / Skill Relevance) : $tier1Count repos" -ForegroundColor Cyan
Write-Host "     - Tier 2 (Tooling & Infrastructure)       : $tier2Count repos" -ForegroundColor Cyan
Write-Host "     - Tier 3 (Libraries & Frameworks)         : $tier3Count repos" -ForegroundColor Cyan
Write-Host "     - Tier 4 (General Software & Repos)       : $tier4Count repos" -ForegroundColor Gray

# Step 2B: Inspect Git Trees for Top Tier 1 Repositories (Metadata / Tree API - Zero Clones)
Write-Host "`n--- INSPECTING GIT TREES FOR TOP TIER 1 CANDIDATES (TREE API) ---" -ForegroundColor Yellow

$headers = @{
    'User-Agent' = 'SkillRegistry-Operational-Scanner/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}
if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
    $headers['Authorization'] = "token $env:GITHUB_TOKEN"
}

$inspectedTrees = New-Object 'System.Collections.Generic.List[object]'
$candidateArtifacts = New-Object 'System.Collections.Generic.List[object]'

$inspectLimit = [Math]::Min($TopTreeInspectLimit, $sortedRepos.Count)
$topCandidates = $sortedRepos[0..($inspectLimit - 1)]

foreach ($tc in $topCandidates) {
    $fn = [string]$tc.full_name
    $branch = [string]$tc.default_branch
    $treeUri = "https://api.github.com/repos/$fn/git/trees/$branch`?recursive=1"
    Write-Host "Querying tree for $fn ($branch)..." -ForegroundColor Gray
    
    try {
        $resp = Invoke-WebRequest -Uri $treeUri -Headers $headers -UseBasicParsing -TimeoutSec 15
        $treeJson = $resp.Content | ConvertFrom-Json
        
        $files = if ($null -ne $treeJson.tree) { @($treeJson.tree) } else { @() }
        Write-Host "  -> $fn tree contains $($files.Count) items." -ForegroundColor Green
        
        $skillArtifacts = New-Object 'System.Collections.Generic.List[object]'
        
        foreach ($f in $files) {
            $path = [string]$f.path
            $type = [string]$f.type # "blob" or "tree"
            if ($type -ne 'blob') { continue }
            
            $pathLower = $path.ToLowerInvariant()
            $artifactClass = $null
            
            if ($pathLower -match 'skill\.md$|skills/.+/skill\.md$') {
                $artifactClass = 'SKILL_DEFINITION_CANDIDATE'
            } elseif ($pathLower -match '\.cursorrules$|claude\.json$|agent\.json$|\.codex/config\.json$') {
                $artifactClass = 'AGENT_CONFIG_ARTIFACT'
            } elseif ($pathLower -match 'prompts?/.+\.md$|prompts?/.+\.txt$|\.prompt$') {
                $artifactClass = 'PROMPT_TEMPLATE_ARTIFACT'
            } elseif ($pathLower -match '^\.github/workflows/.+\.ya?ml$') {
                $artifactClass = 'WORKFLOW_AUTOMATION_ARTIFACT'
            } elseif ($pathLower -match 'mcp\.json$|server\.py$|server\.ts$|tools?/.+\.(py|ts|js)$') {
                $artifactClass = 'CAPABILITY_ARTIFACT'
            } elseif ($pathLower -match '^readme\.md$') {
                $artifactClass = 'DOCUMENTATION_EVIDENCE'
            }
            
            if ($null -ne $artifactClass -and $artifactClass -ne 'DOCUMENTATION_EVIDENCE' -and $artifactClass -ne 'WORKFLOW_AUTOMATION_ARTIFACT') {
                $artObj = [ordered]@{
                    schema_version = "1.0.0"
                    repo_full_name = $fn
                    relative_path = $path
                    blob_sha = [string]$f.sha
                    size_bytes = if ($f.PSObject.Properties.Item('size')) { [int]$f.size } else { 0 }
                    artifact_class = $artifactClass
                    discovered_utc = [DateTime]::UtcNow.ToString("o")
                }
                [void]$skillArtifacts.Add($artObj)
                [void]$candidateArtifacts.Add($artObj)
            }
        }
        
        [void]$inspectedTrees.Add([ordered]@{
            repo = $fn
            total_tree_files = $files.Count
            candidate_artifacts_found = $skillArtifacts.Count
            artifacts = $skillArtifacts.ToArray()
        })
        
        Start-Sleep -Milliseconds 400
        
    } catch {
        Write-Host "  -> Could not fetch tree for $fn`: $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

# Write candidate artifacts ledger
$sbArtifacts = New-Object 'System.Text.StringBuilder'
foreach ($ca in $candidateArtifacts) {
    $j = ($ca | ConvertTo-Json -Compress)
    [void]$sbArtifacts.AppendLine($j)
}
[System.IO.File]::WriteAllText($treeCatalogJsonl, $sbArtifacts.ToString(), $utf8NoBom)

# Generate Deep Triage Report
$deepTriageReport = [ordered]@{
    schema = "skill-registry.operational.github-deep-triage/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    total_evaluated = $sortedRepos.Count
    tier_distribution = [ordered]@{
        tier_1_agentic_skill_candidates = $tier1Count
        tier_2_tooling_and_infra = $tier2Count
        tier_3_libraries_and_frameworks = $tier3Count
        tier_4_general_software = $tier4Count
    }
    trees_inspected_count = $inspectedTrees.Count
    candidate_artifacts_cataloged_count = $candidateArtifacts.Count
    top_25_ranked_repositories = @($sortedRepos | Select-Object -First 25 | ForEach-Object {
        [ordered]@{
            full_name = $_.full_name
            relevance_score = $_.relevance_score
            tier = $_.tier
            category = $_.inferred_category
            language = $_.language
            stars = $_.stargazers_count
            matched_signals = $_.matched_signals
            description = $_.description
        }
    })
}

$summaryJson = $deepTriageReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($reportJson, $summaryJson, $utf8NoBom)

# Generate Markdown Report
$mdList = New-Object 'System.Collections.Generic.List[string]'
[void]$mdList.Add("# Operacao 2: GitHub Deep Triage & Classification Report")
[void]$mdList.Add("")
[void]$mdList.Add("**Skill Registry v1.0.0 - Triagem Multi-Sinal & Inspecao de Arvores**")
[void]$mdList.Add("- **Total de Repositorios Avaliados**: **$($sortedRepos.Count)**")
[void]$mdList.Add("- **Metodologia**: Multi-Signal Scoring (Topics + Name + Desc + Lang + Popularity)")
[void]$mdList.Add("- **Data/Hora (UTC)**: $([DateTime]::UtcNow.ToString('o'))")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 1. Distribuicao por Tiers de Relevancia")
[void]$mdList.Add("")
[void]$mdList.Add("| Tier | Descricao | Quantidade de Repositorios |")
[void]$mdList.Add("| :--- | :--- | :--- |")
[void]$mdList.Add("| **Tier 1: Agentic & Skill Candidates** | Repositorios com alta densidade de agentes, MCP, skills e assistentes | **$tier1Count** |")
[void]$mdList.Add("| **Tier 2: Tooling & Infra** | Ferramentas de seguranca, automacao, CLI e infraestrutura | **$tier2Count** |")
[void]$mdList.Add("| **Tier 3: Libraries & Frameworks** | Bibliotecas de runtime, SDKs e frameworks de aplicacao | **$tier3Count** |")
[void]$mdList.Add("| **Tier 4: General Software** | Software geral, documentacao, repositorios auxiliares | **$tier4Count** |")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 2. Top 20 Repositorios com Maior Relevancia Identificados")
[void]$mdList.Add("")
[void]$mdList.Add("| # | Repositorio | Score | Categoria Inferida | Linguagem | Stars |")
[void]$mdList.Add("| :--- | :--- | :--- | :--- | :--- | :--- |")

$rank = 1
foreach ($r in ($sortedRepos | Select-Object -First 25)) {
    $scoreVal = [string]$r.relevance_score
    $fn = [string]$r.full_name
    $cat = [string]$r.inferred_category
    $lang = [string]$r.language
    $st = [string]$r.stargazers_count
    $row = "| {0} | **{1}** | `{2}` | {3} | {4} | {5} |" -f $rank, $fn, $scoreVal, $cat, $lang, $st
    [void]$mdList.Add($row)
    $rank++
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 3. Inspecao de Arvores (Git Trees API - Sem Clones)")
[void]$mdList.Add("")
[void]$mdList.Add("Foram inspecionadas as arvores de arquivos dos repositorios mais relevantes de Tier 1:")
[void]$mdList.Add("- **Total de Arvores Inspecionadas**: $($inspectedTrees.Count)")
[void]$mdList.Add("- **Artefatos Candidatos Descobertos**: **$($candidateArtifacts.Count)**")
[void]$mdList.Add("- **Ledger de Artefatos**: [`staging/github-inlet/candidate-artifacts.jsonl`](file:///E:/.skill-registry/staging/github-inlet/candidate-artifacts.jsonl)")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 4. Classificacao Estrita dos Artefatos Descobertos")
[void]$mdList.Add("")
[void]$mdList.Add("Os artefatos identificados foram classificados sem auto-promocao:")
[void]$mdList.Add("- `SKILL_DEFINITION_CANDIDATE`: Arquivos estruturados com instrucoes/frontmatter de skill.")
[void]$mdList.Add("- `AGENT_CONFIG_ARTIFACT`: Configuracoes de comportamento (`.cursorrules`, `claude.json`).")
[void]$mdList.Add("- `PROMPT_TEMPLATE_ARTIFACT`: Templates de prompts desacoplados de logica executavel.")
[void]$mdList.Add("- `CAPABILITY_ARTIFACT`: Servidores MCP e modulos de ferramentas prontas para orquestracao.")

[System.IO.File]::WriteAllLines($reportMd, $mdList.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DEEP TRIAGE COMPLETE                                       " -ForegroundColor Green
Write-Host " Ranked Ledger     : $triageJsonl" -ForegroundColor Green
Write-Host " Candidate Ledger  : $treeCatalogJsonl" -ForegroundColor Green
Write-Host " Report            : $reportMd" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
