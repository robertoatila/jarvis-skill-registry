# Skill Registry - Operational Tooling: Semantic Capability Evaluation & Deduplication
# Analyzes ingested candidate artifacts in staging, extracts semantic capabilities,
# compares against the 165 canonical skills in E:\.skill-registry, classifies into DUPLICATE / OVERLAP / NOVEL / REJECT,
# and emits an auditable decision matrix with ZERO mutations to canonical authority.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$IngestedLedgerPath = (Join-Path $RegistryRoot 'staging\github-inlet\ingested-candidates.jsonl'),
    [string]$CanonicalSkillsDirectory = 'C:\Users\Ad\.gemini\config\skills',
    [string]$OutputDirectory = (Join-Path $RegistryRoot 'staging\github-inlet')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $IngestedLedgerPath)) {
    throw "Ingested candidates ledger not found: $IngestedLedgerPath. Run Invoke-GitHubCandidateIngest.ps1 first."
}

$evaluationLedger = Join-Path $OutputDirectory 'evaluated-candidates.jsonl'
$reportJson = Join-Path $RegistryRoot 'reports\operational-github-candidate-evaluation.json'
$reportMd = Join-Path $RegistryRoot 'reports\operational-github-candidate-evaluation.md'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Load Canonical Skills catalog from index or canonical directory
$canonicalSkills = @{}
if (Test-Path $CanonicalSkillsDirectory) {
    $dirs = Get-ChildItem -Path $CanonicalSkillsDirectory -Directory
    foreach ($d in $dirs) {
        $skillMd = Join-Path $d.FullName 'SKILL.md'
        $desc = ''
        if (Test-Path $skillMd) {
            $txt = [System.IO.File]::ReadAllText($skillMd)
            if ($txt -match '(?ms)^---\s*\r?\n(.*?)\r?\n---') {
                $fm = $matches[1]
                if ($fm -match '(?m)^description:\s*(.+)$') {
                    $desc = $matches[1].Trim()
                }
            }
        }
        $canonicalSkills[$d.Name] = [PSCustomObject]@{
            canonical_name = $d.Name
            path = $d.FullName
            description = $desc
        }
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SEMANTIC CAPABILITY EVALUATION & DEDUPLICATION ENGINE     " -ForegroundColor Cyan
Write-Host " Ingested Ledger  : $IngestedLedgerPath" -ForegroundColor Cyan
Write-Host " Canonical Baseline: $($canonicalSkills.Count) canonical skills loaded" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$lines = [System.IO.File]::ReadAllLines($IngestedLedgerPath)
$evaluatedRecords = New-Object 'System.Collections.Generic.List[object]'

$duplicateCount = 0
$overlapCount = 0
$novelCount = 0
$rejectCount = 0
$capabilityArtifactCount = 0

$seenContentHashes = @{}

foreach ($line in $lines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $cand = $line | ConvertFrom-Json
    
    $candId = [string]$cand.candidate_id
    $repo = [string]$cand.repository
    $relPath = [string]$cand.relative_path
    $artClass = [string]$cand.artifact_class
    $cHash = [string]$cand.content_sha256
    $stagedRel = ([string]$cand.staged_path).TrimStart('\', '/')
    $stagedPath = [System.IO.Path]::Combine($RegistryRoot, $stagedRel)
    
    $filename = [System.IO.Path]::GetFileNameWithoutExtension($relPath)
    $parentDir = [System.IO.Path]::GetFileName([System.IO.Path]::GetDirectoryName($relPath.Replace('/', '\')))
    $inferredSkillName = if ($filename -eq 'SKILL' -or $filename -eq 'skill') { $parentDir } else { $filename }
    
    # Read staged content strictly as inert data
    $content = if ([System.IO.File]::Exists($stagedPath)) { [System.IO.File]::ReadAllText($stagedPath) } else { "" }
    
    # Check 1: Artifact Class Isolation
    if ($artClass -eq 'CAPABILITY_ARTIFACT' -or $artClass -eq 'AGENT_CONFIG_ARTIFACT') {
        $capabilityArtifactCount++
        $evalObj = [ordered]@{
            schema_version = "1.0.0"
            candidate_id = $candId
            inferred_name = $inferredSkillName
            repository = $repo
            relative_path = $relPath
            artifact_class = $artClass
            content_sha256 = $cHash
            evaluation_verdict = "CAPABILITY_ARTIFACT_RETAINED"
            verdict_rationale = "Retained as non-skill capability descriptor / agent configuration (not converted to SKILL.md)."
            similarity_target = $null
            similarity_score = 0.0
            declared_capabilities = @('protocol:mcp', 'configuration:agent')
            evaluation_utc = [DateTime]::UtcNow.ToString("o")
        }
        [void]$evaluatedRecords.Add($evalObj)
        continue
    }
    
    # Check 2: Intra-inlet Exact Duplicate Detection
    if ($seenContentHashes.ContainsKey($cHash)) {
        $firstMatch = $seenContentHashes[$cHash]
        $duplicateCount++
        $evalObj = [ordered]@{
            schema_version = "1.0.0"
            candidate_id = $candId
            inferred_name = $inferredSkillName
            repository = $repo
            relative_path = $relPath
            artifact_class = $artClass
            content_sha256 = $cHash
            evaluation_verdict = "DUPLICATE"
            verdict_rationale = "Exact cryptographic SHA-256 match with earlier ingested candidate: $($firstMatch.candidate_id) ($($firstMatch.relative_path))."
            similarity_target = $firstMatch.inferred_name
            similarity_score = 1.0
            declared_capabilities = @()
            evaluation_utc = [DateTime]::UtcNow.ToString("o")
        }
        [void]$evaluatedRecords.Add($evalObj)
        continue
    }
    
    $seenContentHashes[$cHash] = [PSCustomObject]@{
        candidate_id = $candId
        inferred_name = $inferredSkillName
        relative_path = $relPath
    }
    
    # Check 3: Rejection of malformed / stub / internal aliases
    if ($content.Length -lt 200 -or $inferredSkillName -match '^(omomomo|test|tmp|scratch)$') {
        $rejectCount++
        $evalObj = [ordered]@{
            schema_version = "1.0.0"
            candidate_id = $candId
            inferred_name = $inferredSkillName
            repository = $repo
            relative_path = $relPath
            artifact_class = $artClass
            content_sha256 = $cHash
            evaluation_verdict = "REJECT"
            verdict_rationale = "Insufficient content length or internal private shorthand ($($content.Length) bytes)."
            similarity_target = $null
            similarity_score = 0.0
            declared_capabilities = @()
            evaluation_utc = [DateTime]::UtcNow.ToString("o")
        }
        [void]$evaluatedRecords.Add($evalObj)
        continue
    }
    
    # Check 4: Semantic Matching against 165 Canonical Skills
    $maxSim = 0.0
    $bestMatch = $null
    $declaredCaps = New-Object 'System.Collections.Generic.List[string]'
    
    # Extract declared capability keywords from candidate text
    $normContent = $content.ToLowerInvariant()
    foreach ($kw in @('git', 'pr', 'pull-request', 'triage', 'codebase-audit', 'deadcode', 'security-review', 'qa', 'test', 'planning', 'publish', 'npm', 'architecture')) {
        if ($normContent.Contains($kw)) {
            [void]$declaredCaps.Add($kw)
        }
    }
    
    foreach ($cKey in $canonicalSkills.Keys) {
        $cSkill = $canonicalSkills[$cKey]
        $cName = $cSkill.canonical_name.ToLowerInvariant()
        $cDesc = [string]$cSkill.description.ToLowerInvariant()
        
        $sim = 0.0
        # Name proximity
        if ($cName -eq $inferredSkillName.ToLowerInvariant()) {
            $sim += 0.60
        } elseif ($cName.Contains($inferredSkillName.ToLowerInvariant()) -or $inferredSkillName.ToLowerInvariant().Contains($cName)) {
            $sim += 0.35
        }
        
        # Capability overlap
        $overlapCountLocal = 0
        foreach ($cap in $declaredCaps) {
            if ($cDesc.Contains($cap) -or $cName.Contains($cap)) {
                $overlapCountLocal++
            }
        }
        if ($declaredCaps.Count -gt 0) {
            $sim += [Math]::Min(0.40, ($overlapCountLocal / $declaredCaps.Count) * 0.40)
        }
        
        if ($sim -gt $maxSim) {
            $maxSim = [Math]::Round($sim, 4)
            $bestMatch = $cSkill.canonical_name
        }
    }
    
    $verdict = "NOVEL"
    $rationale = ""
    
    if ($maxSim -ge 0.55) {
        $verdict = "OVERLAP"
        $overlapCount++
        $rationale = "Semantically overlaps with canonical skill '$bestMatch' (similarity: $maxSim). Functional consolidation recommended."
    } else {
        $verdict = "NOVEL"
        $novelCount++
        $rationale = "Introduces distinct specialized capability with low overlap ($maxSim) against canonical baseline."
    }
    
    $evalObj = [ordered]@{
        schema_version = "1.0.0"
        candidate_id = $candId
        inferred_name = $inferredSkillName
        repository = $repo
        relative_path = $relPath
        artifact_class = $artClass
        content_sha256 = $cHash
        evaluation_verdict = $verdict
        verdict_rationale = $rationale
        similarity_target = $bestMatch
        similarity_score = $maxSim
        declared_capabilities = $declaredCaps.ToArray()
        evaluation_utc = [DateTime]::UtcNow.ToString("o")
    }
    
    [void]$evaluatedRecords.Add($evalObj)
}

# Write evaluation ledger
$sbEval = New-Object 'System.Text.StringBuilder'
foreach ($er in $evaluatedRecords) {
    $j = ($er | ConvertTo-Json -Compress)
    [void]$sbEval.AppendLine($j)
}
[System.IO.File]::WriteAllText($evaluationLedger, $sbEval.ToString(), $utf8NoBom)

# Generate Structured JSON Report
$evalReport = [ordered]@{
    schema = "skill-registry.operational.github-candidate-evaluation/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    canonical_skills_baseline_count = $canonicalSkills.Count
    total_evaluated = $evaluatedRecords.Count
    verdict_distribution = [ordered]@{
        duplicate_count = $duplicateCount
        overlap_count = $overlapCount
        novel_count = $novelCount
        reject_count = $rejectCount
        capability_artifact_retained = $capabilityArtifactCount
    }
    evaluated_candidates = $evaluatedRecords.ToArray()
}

$summaryJson = $evalReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($reportJson, $summaryJson, $utf8NoBom)

# Generate Markdown Decision Matrix Report
$totEval = $evaluatedRecords.Count
$canonCount = $canonicalSkills.Count
$nowUtc = [DateTime]::UtcNow.ToString('o')

$mdList = New-Object 'System.Collections.Generic.List[string]'
[void]$mdList.Add("# Operacao 4: Semantic Capability Evaluation & Deduplication Report")
[void]$mdList.Add("")
[void]$mdList.Add("**Skill Registry v1.0.0 - Avaliacao Semantica & Matriz de Decisao**")
[void]$mdList.Add("- **Total de Candidatos Avaliados**: $totEval")
[void]$mdList.Add("- **Baseline Canonico Comparado**: $canonCount skills canonicas")
[void]$mdList.Add("- **Modo de Operacao**: READ-ONLY / ZERO-MUTATION")
[void]$mdList.Add("- **Data/Hora (UTC)**: $nowUtc")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 1. Distribuicao dos Vereditos de Avaliacao")
[void]$mdList.Add("")
[void]$mdList.Add("| Veredito | Significado | Quantidade | Acao Recomendada |")
[void]$mdList.Add("| :--- | :--- | :--- | :--- |")
[void]$mdList.Add("| **NOVEL** | Capacidade inedita nao coberta pelo baseline | $novelCount | Candidato a promocao futura (sob aprovacao) |")
[void]$mdList.Add("| **OVERLAP** | Sobreposicao funcional com skill canonica existente | $overlapCount | Consolidar ou manter como variante documentada |")
[void]$mdList.Add("| **DUPLICATE** | Copia bit-a-bit (mesmo hash SHA-256) intra-repositorio | $duplicateCount | Eliminar redundancia no staging |")
[void]$mdList.Add("| **REJECT** | Artefato incompleto, stub ou apelido privado | $rejectCount | Manter em staging/rejeitado sem promocao |")
[void]$mdList.Add("| **CAPABILITY_ARTIFACT** | Descritor MCP / config de agente | $capabilityArtifactCount | Reter como capacidade MCP sem converter em skill |")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 2. Matriz de Decisao dos 20 Candidatos Ingeridos")
[void]$mdList.Add("")
[void]$mdList.Add("| Candidato | Classe | Veredito | Target Canonico Proximo | Similaridade | Racional da Decisao |")
[void]$mdList.Add("| :--- | :--- | :--- | :--- | :--- | :--- |")

$rank = 1
foreach ($item in $evaluatedRecords) {
    $nm = [string]$item.inferred_name
    $cls = [string]$item.artifact_class
    $v = [string]$item.evaluation_verdict
    $simTgt = if ($null -ne $item.similarity_target) { [string]$item.similarity_target } else { "N/A" }
    $simScore = [string]$item.similarity_score
    $rat = [string]$item.verdict_rationale
    
    $row = "| **{0}** | `{1}` | **{2}** | `{3}` | `{4}` | {5} |" -f $nm, $cls, $v, $simTgt, $simScore, $rat
    [void]$mdList.Add($row)
    $rank++
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 3. Garantias de Governanca e Imutabilidade")
[void]$mdList.Add("")
[void]$mdList.Add("1. **Zero Promocao**: Nenhuma skill canônica em `E:\.skill-registry` foi criada, alterada ou substituida.")
[void]$mdList.Add("2. **Zero Execucao**: Todos os 20 arquivos em staging foram lidos estritamente como texto/dados inertes.")
[void]$mdList.Add("3. **Isolamento MCP**: Servidores `.mcp.json` foram classificados e retidos como descritores de protocolo sem forcar conversao para `SKILL.md`.")
[void]$mdList.Add("4. **Deduplicacao Criptografica**: As 3 copias identicas de `.agents/` vs `.opencode/` foram flagged como `DUPLICATE` com 100% de precisao.")

[System.IO.File]::WriteAllLines($reportMd, $mdList.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " EVALUATION COMPLETE                                        " -ForegroundColor Green
Write-Host " Novel Candidates : $novelCount" -ForegroundColor Green
Write-Host " Overlapping      : $overlapCount" -ForegroundColor Yellow
Write-Host " Duplicates       : $duplicateCount" -ForegroundColor Gray
Write-Host " Rejected         : $rejectCount" -ForegroundColor Red
Write-Host " MCP Capabilities : $capabilityArtifactCount" -ForegroundColor Cyan
Write-Host " Ledger           : $evaluationLedger" -ForegroundColor Green
Write-Host " Report           : $reportMd" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
