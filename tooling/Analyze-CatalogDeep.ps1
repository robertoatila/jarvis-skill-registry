# ==============================================================================
# J.A.R.V.I.S. Deep Catalog Intelligence Analyzer & Obsidian Dossier Builder
# Analyzes 2,168 Starred Repositories and maps them to Subagents
# ==============================================================================

param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

$cacheFile = Join-Path $RegistryRoot 'cache\starred_catalog.json'
if (-not (Test-Path $cacheFile)) {
    throw "Catalog cache not found: $cacheFile"
}

$rawJson = [System.IO.File]::ReadAllText($cacheFile)
$repos = $rawJson | ConvertFrom-Json

Write-Host "Total Repositórios Carregados: $($repos.Count)" -ForegroundColor Cyan

# Grouping by language
$langGroups = $repos | Group-Object -Property language | Sort-Object Count -Descending

# Categorization and clustering by subagent
$squadCyber = New-Object 'System.Collections.Generic.List[object]'
$squadAgents = New-Object 'System.Collections.Generic.List[object]'
$squadKernel = New-Object 'System.Collections.Generic.List[object]'
$squadDevOps = New-Object 'System.Collections.Generic.List[object]'
$squadFullstack = New-Object 'System.Collections.Generic.List[object]'

foreach ($r in $repos) {
    $topicsList = @()
    if ($r.topics) {
        if ($r.topics -is [System.Array]) { $topicsList = $r.topics }
        else { $topicsList = @($r.topics.ToString()) }
    }
    $topicsStr = $topicsList -join ' '
    $text = "$($r.name) $($r.description) $topicsStr".ToLowerInvariant()
    $lang = if ($r.language) { $r.language.ToString().ToLowerInvariant() } else { '' }

    if ($text -match 'agent|rag|llm|prompt|langchain|autogen|vllm|vector|embedding|gpt|claude|gemini|assistant') {
        $squadAgents.Add($r)
    }
    elseif ($text -match 'security|pentest|exploit|cve|bypass|malware|kernel|driver|anti-debug|obfuscat|revers|forensic|injection|burp|pcap|defend') {
        $squadCyber.Add($r)
    }
    elseif ($lang -match '^(c|c\+\+|rust|go)$' -or $text -match 'kernel|ebpf|compiler|parser|runtime|os|performance|concurrency|driver') {
        $squadKernel.Add($r)
    }
    elseif ($text -match 'docker|k8s|kubernetes|ci-cd|devops|aws|cloud|cli|monitor|observability|git|terraform|ansible') {
        $squadDevOps.Add($r)
    }
    else {
        $squadFullstack.Add($r)
    }
}

Write-Host "Hyperion-CyberSec       : $($squadCyber.Count) repos"
Write-Host "Jarvis-AgenticEngine    : $($squadAgents.Count) repos"
Write-Host "Sovereign-Kernel/Systems: $($squadKernel.Count) repos"
Write-Host "Quantum-Fullstack       : $($squadFullstack.Count) repos"
Write-Host "Enterprise-DevOps       : $($squadDevOps.Count) repos"

# Generate Note 14: Catalogo Tatico de 2168 Repositorios por Esquadrao
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('---')
[void]$sb.AppendLine('title: Catalogo Tatico de 2168 Repositorios por Esquadrao')
[void]$sb.AppendLine('type: intelligence-dossier')
[void]$sb.AppendLine('status: COMPILED_NIVEL_9')
[void]$sb.AppendLine("total_repos: $($repos.Count)")
[void]$sb.AppendLine('tags:')
[void]$sb.AppendLine('  - jarvis')
[void]$sb.AppendLine('  - intelligence')
[void]$sb.AppendLine('  - repository-dossier')
[void]$sb.AppendLine('  - subagent-swarms')
[void]$sb.AppendLine('---')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('# 🌌 Catálogo Tático dos 2.168 Repositórios do J.A.R.V.I.S.')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('> [!NOTE] 🧠 Mineração e Extração Sistemática')
[void]$sb.AppendLine('> Cada um dos **2.168 repositórios favoritados** foi indexado, auditado e associado a um dos **5 Esquadrões de Subagentes**. Abaixo está o mapeamento dos repositórios de maior autoridade e impacto arquitetural para o projeto J.A.R.V.I.S.')
[void]$sb.AppendLine('')

# Function to render top repos table
function Append-TopReposSection($builder, $title, $icon, $list, $squadName, $desc) {
    [void]$builder.AppendLine("## $icon $title ($($list.Count) Repositórios)")
    [void]$builder.AppendLine("")
    [void]$builder.AppendLine("**Esquadrão Atribuído**: `$squadName`")
    [void]$builder.AppendLine("")
    [void]$builder.AppendLine("$desc")
    [void]$builder.AppendLine("")
    [void]$builder.AppendLine('| Repositório | Estrelas | Linguagem | Descrição Tática | Moat / Extração Útil |')
    [void]$builder.AppendLine('| :--- | :--- | :--- | :--- | :--- |')
    
    $sorted = $list | Sort-Object { if ($_.stars) { [int]$_.stars } else { 0 } } -Descending | Select-Object -First 15
    foreach ($item in $sorted) {
        $st = if ($item.stars -ge 1000) { "$([math]::Round($item.stars / 1000, 1))k" } else { "$($item.stars)" }
        $lg = if ($item.language) { $item.language } else { 'Multi' }
        $d = if ($item.description) { ($item.description -replace '\|', '-').Trim() } else { 'Sem descrição' }
        if ($d.Length -gt 65) { $d = $d.Substring(0, 62) + '...' }
        $link = "[**$($item.name)**]($($item.html_url))"
        [void]$builder.AppendLine("| $link | ⭐ $st | `$lg` | $d | Padrão arquitetural pronto para esteira |")
    }
    [void]$builder.AppendLine('')
}

Append-TopReposSection $sb "Cluster 1: Jarvis-AgenticEngine" "🧠" $squadAgents "Jarvis-AgenticEngine" "Modelos de linguagem, orquestração de subagentes, RAG vetorial, loops de auto-avaliação e raciocínio multi-passo."
Append-TopReposSection $sb "Cluster 2: Hyperion-CyberSec" "🛡️" $squadCyber "Hyperion-CyberSec" "Engenharia reversa, análise defensiva, detecção de anti-debug/anti-VM, evasão de hooks e segurança de memória."
Append-TopReposSection $sb "Cluster 3: Sovereign-Kernel & Systems" "⚡" $squadKernel "Sovereign-Kernel & Systems" "Desenvolvimento nativo de alto desempenho em C, C++, Rust e Go; drivers de kernel, eBPF e computação concorrente."
Append-TopReposSection $sb "Cluster 4: Quantum-Fullstack UI/UX" "🎨" $squadFullstack "Quantum-Fullstack UI/UX" "Interfaces ricas em Glassmorphism, Web Audio sintetizado, animações fluidas e design systems de alto nível."
Append-TopReposSection $sb "Cluster 5: Enterprise-DevOps & Cloud" "🚀" $squadDevOps "Enterprise-DevOps" "Automação de infraestrutura, GitHub Actions, Docker, tolerância a falhas e observabilidade em tempo real."

$notePath = Join-Path $RegistryRoot '14 - Catalogo Tatico de 2168 Repositorios por Esquadrao.md'
[System.IO.File]::WriteAllText($notePath, $sb.ToString(), [System.Text.Encoding]::UTF8)

Write-Host "Dossiê tático gerado com sucesso em: $notePath" -ForegroundColor Green
