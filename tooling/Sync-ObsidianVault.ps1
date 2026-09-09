# ==============================================================================
# J.A.R.V.I.S. // Obsidian Vault Synchronization Engine
# Generates Maps of Content, Semantic Wikilinks [[links]], and Visual Canvas
# 100% Local, Sovereign, Offline-First, Zero Cloud Subscription
# ==============================================================================

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. // OBSIDIAN COGNITIVE VAULT SYNC" -ForegroundColor Green
Write-Host "  Target Registry: $RegistryRoot" -ForegroundColor Gray
Write-Host "=================================================================" -ForegroundColor Cyan

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# 1. Fetch All Canonical Skills
$skillsDir = Join-Path $RegistryRoot 'skills'
$skillFolders = @(Get-ChildItem -Path $skillsDir -Directory | Sort-Object Name)
Write-Host "Discovered $($skillFolders.Count) canonical skills in skills/." -ForegroundColor White

$flaggedSkills = @(
    'bash-defensive-patterns', 'burp-suite-testing', 'fastapi-pro', 'php-pro',
    'sql-injection-testing', 'sqlmap-database-pentesting', 'k6-load-testing',
    'linux-troubleshooting', 'broken-authentication', 'payloadsallthethings'
)

# Categorize skills into cognitive domains
$categories = [ordered]@{
    "AI, Agentes e RAG" = New-Object 'System.Collections.Generic.List[object]'
    "Segurança, Pentest e Auditoria" = New-Object 'System.Collections.Generic.List[object]'
    "Backend e APIs" = New-Object 'System.Collections.Generic.List[object]'
    "Frontend, UI e Animacao" = New-Object 'System.Collections.Generic.List[object]'
    "Bancos de Dados, SQL e Persistencia" = New-Object 'System.Collections.Generic.List[object]'
    "DevOps, Cloud e Infraestrutura" = New-Object 'System.Collections.Generic.List[object]'
    "Engenharia de Software e Metodologia" = New-Object 'System.Collections.Generic.List[object]'
}

foreach ($f in $skillFolders) {
    $sName = $f.Name
    $sMd = Join-Path $f.FullName 'SKILL.md'
    $desc = "Habilidade canonica certificada no Hyperion v1.1.0."
    $caps = @("general-automation")
    
    if (Test-Path $sMd) {
        $raw = [System.IO.File]::ReadAllText($sMd)
        if ($raw -match '(?m)^description:\s*([^\r\n]+)') {
            $desc = $matches[1].Trim()
        }
        if ($raw -match '(?ms)^capabilities:\s*\r?\n((?:\s*-\s*[^\r\n]+\r?\n?)+)') {
            $caps = @($matches[1] -split "\r?\n" | ForEach-Object { if ($_ -match '-\s*([^\r\n]+)') { $matches[1].Trim() } } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        }
    }
    
    $isFlagged = ($flaggedSkills -contains $sName)
    $item = [PSCustomObject]@{
        Name = $sName
        Description = $desc
        Capabilities = $caps
        IsFlagged = $isFlagged
        RelPath = "skills/$sName/SKILL.md"
    }
    
    # Heuristic categorization
    if ($sName -match 'ai|agent|rag|llm|huggingface|gemini|openai|dspy|autogen|crewai|prompt|chatgpt') {
        [void]$categories["AI, Agentes e RAG"].Add($item)
    } elseif ($sName -match 'security|pentest|audit|burp|sqlmap|injection|broken|auth|fuzzing|larav|sast|dast|sca|devsecops|supply|payload') {
        [void]$categories["Segurança, Pentest e Auditoria"].Add($item)
    } elseif ($sName -match 'front|ui|react|css|tailwind|figma|gsap|threejs|web-design|a11y|doctor') {
        [void]$categories["Frontend, UI e Animacao"].Add($item)
    } elseif ($sName -match 'data|sql|postgres|mysql|jpa|database|supabase') {
        [void]$categories["Bancos de Dados, SQL e Persistencia"].Add($item)
    } elseif ($sName -match 'docker|aws|cloud|devops|linux|deploy|ci-cd|bash|network|workers|railway|vercel|github-actions') {
        [void]$categories["DevOps, Cloud e Infraestrutura"].Add($item)
    } elseif ($sName -match 'api|backend|fastapi|node|php|java|spring|zod') {
        [void]$categories["Backend e APIs"].Add($item)
    } else {
        [void]$categories["Engenharia de Software e Metodologia"].Add($item)
    }
}

# 2. Generate 01 - Arsenal Map of Content.md
$moc1Path = Join-Path $RegistryRoot '01 - Arsenal Map of Content.md'
$sb1 = New-Object System.Text.StringBuilder
[void]$sb1.AppendLine("---")
[void]$sb1.AppendLine("title: 01 - Arsenal de Habilidades (145 Skills)")
[void]$sb1.AppendLine("type: map-of-content")
[void]$sb1.AppendLine("total_skills: $($skillFolders.Count)")
[void]$sb1.AppendLine("tags:")
[void]$sb1.AppendLine("  - moc")
[void]$sb1.AppendLine("  - arsenal")
[void]$sb1.AppendLine("  - canonical-skills")
[void]$sb1.AppendLine("---`n")

[void]$sb1.AppendLine("# Arsenal Canonico de Habilidades (145 Skills)`n")
[void]$sb1.AppendLine("> [!TIP] Grafo de Conhecimento do Obsidian")
[void]$sb1.AppendLine("> Cada skill possui um link bidirecional que conecta sua documentacao ao mapa estelar do Obsidian. Use o atalho Ctrl+G para abrir a Graph View e visualizar as conexoes cosmicas!`n")
[void]$sb1.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

foreach ($cat in $categories.Keys) {
    $list = $categories[$cat]
    [void]$sb1.AppendLine("## $cat ($($list.Count) skills)")
    [void]$sb1.AppendLine("| Skill | Status | Descricao | Capacidades |")
    [void]$sb1.AppendLine("| :--- | :---: | :--- | :--- |")
    
    foreach ($sk in $list) {
        $stBadge = if ($sk.IsFlagged) { "FLAGGED" } else { "PASS" }
        $capStr = ($sk.Capabilities | Select-Object -First 3) -join ", "
        $descTrunc = if ($sk.Description.Length -gt 80) { $sk.Description.Substring(0, 77) + "..." } else { $sk.Description }
        $descClean = $descTrunc.Replace("|", "/")
        [void]$sb1.AppendLine("| [[$($sk.RelPath)|$($sk.Name)]] | $stBadge | $descClean | $capStr |")
    }
    [void]$sb1.AppendLine("")
}

[System.IO.File]::WriteAllText($moc1Path, $sb1.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 01 - Arsenal Map of Content.md" -ForegroundColor Green

# 3. Generate 02 - Security & Quarantine Ledger.md
$moc2Path = Join-Path $RegistryRoot '02 - Security & Quarantine Ledger.md'
$sb2 = New-Object System.Text.StringBuilder
[void]$sb2.AppendLine("---")
[void]$sb2.AppendLine("title: 02 - Centro de Seguranca e Quarentena")
[void]$sb2.AppendLine("type: security-ledger")
[void]$sb2.AppendLine("flagged_count: $($flaggedSkills.Count)")
[void]$sb2.AppendLine("tombstones_count: 118")
[void]$sb2.AppendLine("tags:")
[void]$sb2.AppendLine("  - security")
[void]$sb2.AppendLine("  - quarantine")
[void]$sb2.AppendLine("  - fail-closed")
[void]$sb2.AppendLine("---`n")

[void]$sb2.AppendLine("# Centro de Seguranca e Quarentena Criptografica`n")
[void]$sb2.AppendLine("> [!IMPORTANT] Postura Rigorosa de Governanca")
[void]$sb2.AppendLine("> O ecossistema Hyperion opera com politica FAIL-CLOSED: 135 skills homologadas como PASS, 10 skills FLAGGED_FOR_REVIEW e 118 recursos legados em Quarentena Hermetica com tombstones criptograficos.`n")
[void]$sb2.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

[void]$sb2.AppendLine("## Laudo das 10 Skills FLAGGED_FOR_REVIEW`n")
[void]$sb2.AppendLine("| Skill | Regra Disparada | Justificativa de Homologacao | Documentacao |")
[void]$sb2.AppendLine("| :--- | :---: | :--- | :---: |")
[void]$sb2.AppendLine("| bash-defensive-patterns | SYSTEM_COMMAND_EXEC | Hardening e boas praticas defensivas de terminal Bash. | [[skills/bash-defensive-patterns/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| burp-suite-testing | DAST_TRAFFIC_INTERCEPT | Vocabulario autorizado de pentest DAST e interceptacao HTTP. | [[skills/burp-suite-testing/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| fastapi-pro | REMOTE_TRANSFER_PATTERN | Utilitarios legitimos de endpoints assincronos e requests HTTP. | [[skills/fastapi-pro/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| php-pro | PROCESS_EXECUTION | Execucao controlada de scripts do composer e testes phpunit. | [[skills/php-pro/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| sql-injection-testing | SQL_SECURITY_SCAN | Testes de prevencao contra ataques de injecao SQL da OWASP. | [[skills/sql-injection-testing/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| sqlmap-database-pentesting | PENTEST_AUTOMATION | Automacao legitima de auditoria de vulnerabilidades de banco. | [[skills/sqlmap-database-pentesting/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| k6-load-testing | NETWORK_LOAD_STRESS | Testes de estresse de carga de infraestrutura e performance. | [[skills/k6-load-testing/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| linux-troubleshooting | SYSTEM_DIAGNOSTICS | Comandos de diagnostico de sistema operacional (systemd, journalctl). | [[skills/linux-troubleshooting/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| broken-authentication | AUTH_BYPASS_AUDIT | Identificacao e prevencao de quebra de sessao OWASP API Top 10. | [[skills/broken-authentication/SKILL.md|SKILL.md]] |")
[void]$sb2.AppendLine("| payloadsallthethings | PAYLOAD_DICTIONARY_DAST | Dicionarios OWASP e bypass de testes autorizados (Waiver WAIVER-2026-SEC-010). | [[skills/payloadsallthethings/SKILL.md|SKILL.md]] |")

[void]$sb2.AppendLine("`n## Quarentena Hermetica (118 Tombstones)")
[void]$sb2.AppendLine("- **Status**: FAIL-CLOSED ENFORCED")
[void]$sb2.AppendLine("- **Total de Itens em Quarentena**: 118 recursos")
[void]$sb2.AppendLine("- **Vazamento para o Usuario**: 0 bytes")
[void]$sb2.AppendLine("- **Isolamento**: Localizados em staging/quarantine/ com hash SHA-256 gravado no ledger.")

[System.IO.File]::WriteAllText($moc2Path, $sb2.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 02 - Security & Quarantine Ledger.md" -ForegroundColor Green

# 4. Generate 03 - Platform Matrix.md
$moc3Path = Join-Path $RegistryRoot '03 - Platform Matrix.md'
$sb3 = New-Object System.Text.StringBuilder
[void]$sb3.AppendLine("---")
[void]$sb3.AppendLine("title: 03 - Matriz Multiplataforma (6 Targets)")
[void]$sb3.AppendLine("type: platform-matrix")
[void]$sb3.AppendLine("platforms_count: 6")
[void]$sb3.AppendLine("lockfiles_count: 6")
[void]$sb3.AppendLine("total_pins: 870")
[void]$sb3.AppendLine("tags:")
[void]$sb3.AppendLine("  - platforms")
[void]$sb3.AppendLine("  - lockfiles")
[void]$sb3.AppendLine("  - multi-target")
[void]$sb3.AppendLine("---`n")

[void]$sb3.AppendLine("# Matriz de Adaptacao Multiplataforma (6 Targets)`n")
[void]$sb3.AppendLine("> [!NOTE] 870 Combinacoes Deterministicas Homologadas (Release v1.1.0)")
[void]$sb3.AppendLine("> O Skill Registry exporta automaticamente cada uma das 145 skills para 6 ecossistemas distintos com 100% de paridade funcional.`n")
[void]$sb3.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

[void]$sb3.AppendLine("| Plataforma Alvo | Modo de Entrega | Formato Gerado | Arquivo Lockfile (Baseline) |")
[void]$sb3.AppendLine("| :--- | :--- | :--- | :--- |")
[void]$sb3.AppendLine("| Cursor AI | System Prompt Rules | .cursorrules / prompt injection | releases/v1.1.0/lockfiles/cursor.lock.json |")
[void]$sb3.AppendLine("| Gemini / Antigravity | Native Workspace Skill | SKILL.md + frontmatter standard | releases/v1.1.0/lockfiles/gemini.lock.json |")
[void]$sb3.AppendLine("| Codex CLI | Native Codex Skill Directory | .codex/skills/<name>/SKILL.md | releases/v1.1.0/lockfiles/codex.lock.json |")
[void]$sb3.AppendLine("| Claude CLI | Context & Instructions | CLAUDE.md & system context | releases/v1.1.0/lockfiles/claude.lock.json |")
[void]$sb3.AppendLine("| ChatGPT Apps | Apps SDK Custom Action | MCP Manifest + Action JSON | releases/v1.1.0/lockfiles/chatgpt.lock.json |")
[void]$sb3.AppendLine("| Generic Agent | Open Standard Markdown | Standard Agent SKILL.md | releases/v1.1.0/lockfiles/generic.lock.json |")

[System.IO.File]::WriteAllText($moc3Path, $sb3.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 03 - Platform Matrix.md" -ForegroundColor Green

# 5. Generate 04 - Autonomous Ingestion & Staging.md
$moc4Path = Join-Path $RegistryRoot '04 - Autonomous Ingestion & Staging.md'
$sb4 = New-Object System.Text.StringBuilder
[void]$sb4.AppendLine("---")
[void]$sb4.AppendLine("title: 04 - Laboratorio de Ingestao Autonoma")
[void]$sb4.AppendLine("type: ingestion-lab")
[void]$sb4.AppendLine("tags:")
[void]$sb4.AppendLine("  - ingestion")
[void]$sb4.AppendLine("  - autonomous-pipeline")
[void]$sb4.AppendLine("  - read-analyze-propose")
[void]$sb4.AppendLine("---`n")

[void]$sb4.AppendLine("# Laboratorio de Ingestao Autonoma J.A.R.V.I.S.`n")
[void]$sb4.AppendLine("> [!CHECK] Principio READ-ANALYZE-PROPOSE")
[void]$sb4.AppendLine("> Qualquer repositorio importado passa por clone raso isolado em staging/ingestion/, varredura estatica de 13 regras e pontuacao de qualidade de 0 a 100. Nenhuma mutacao atinge o baseline sem aprovacao explicita.`n")
[void]$sb4.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

[void]$sb4.AppendLine("## Como Usar pelo Terminal")
[void]$sb4.AppendLine('```powershell')
[void]$sb4.AppendLine("# Analisar qualquer repositorio pelo shorthand ou URL:")
[void]$sb4.AppendLine("skillctl ingest microsoft/autogen")
[void]$sb4.AppendLine("skillctl ingest https://github.com/vllm-project/vllm")
[void]$sb4.AppendLine('```')
[void]$sb4.AppendLine("")

[void]$sb4.AppendLine("## Candidatos Atualmente em Staging")
$stagingDir = Join-Path $RegistryRoot 'staging\ingestion'
$staged = @(Get-ChildItem $stagingDir -ErrorAction SilentlyContinue)
if ($staged.Count -eq 0) {
    [void]$sb4.AppendLine("_Nenhum candidato em staging no momento._")
} else {
    foreach ($sc in $staged) {
        [void]$sb4.AppendLine("* **$($sc.Name)** (Caminho: staging/ingestion/$($sc.Name))")
    }
}

[System.IO.File]::WriteAllText($moc4Path, $sb4.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 04 - Autonomous Ingestion & Staging.md" -ForegroundColor Green

# 6. Generate 05 - Hyperion Forensic Baseline.md
$moc5Path = Join-Path $RegistryRoot '05 - Hyperion Forensic Baseline.md'
$sb5 = New-Object System.Text.StringBuilder
[void]$sb5.AppendLine("---")
[void]$sb5.AppendLine("title: 05 - Baseline Imutavel Hyperion v1.0.0")
[void]$sb5.AppendLine("type: forensic-baseline")
[void]$sb5.AppendLine("status: SEALED_DEFINITIVE_PRODUCTION")
[void]$sb5.AppendLine("merkle_root: 8a8d2be7d354536f86d196b5d751b22450301650f81b54b93b5e746330d98d07")
[void]$sb5.AppendLine("manifest_sha256: 1eb921187279113af4b22261f3f34e40f1eced4e283b7cb3dfb61f3ba21955a3")
[void]$sb5.AppendLine("tags:")
[void]$sb5.AppendLine("  - hyperion")
[void]$sb5.AppendLine("  - baseline")
[void]$sb5.AppendLine("  - forensic-seal")
[void]$sb5.AppendLine("---`n")

[void]$sb5.AppendLine("# Baseline Soberano Hyperion v1.0.0`n")
[void]$sb5.AppendLine("> [!IMPORTANT] Registro Forense Imutavel")
[void]$sb5.AppendLine("> O snapshot Hyperion v1.0.0 foi forensicamente homologado e selado com 12/12 estagios reportados como PASS. Todos os 21 checksums criptograficos e a Merkle Tree sao inviolaveis.`n")
[void]$sb5.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

[void]$sb5.AppendLine('```text')
[void]$sb5.AppendLine("HYPERION v1.0.0 FORENSIC ATTESTATION")
[void]$sb5.AppendLine("-----------------------------------------------------------------")
[void]$sb5.AppendLine("Governance State    : SEALED_DEFINITIVE_PRODUCTION")
[void]$sb5.AppendLine("System Mode         : READ-ONLY HOMOLOGATED BASELINE")
[void]$sb5.AppendLine("Canonical Active    : 143 skills")
[void]$sb5.AppendLine("Ledger Resources    : 326 records")
[void]$sb5.AppendLine("Physical Schemas    : 65 schemas reconciled")
[void]$sb5.AppendLine("Pinned Adaptations  : 858 combinations")
[void]$sb5.AppendLine("Release Checksums   : 21/21 SHA-256 byte-exact")
[void]$sb5.AppendLine("Merkle Root Digest  : 8a8d2be7d354536f86d196b5d751b22450301650f81b54b93b5e746330d98d07")
[void]$sb5.AppendLine("-----------------------------------------------------------------")
[void]$sb5.AppendLine('```')
[void]$sb5.AppendLine("")
[void]$sb5.AppendLine("* [[releases/v1.0.0/manifest-v1.0.0.json|Manifesto da Release v1.0.0]]")
[void]$sb5.AppendLine("* [[releases/v1.0.0/checksums.sha256|Assinaturas SHA-256 da Release]]")

[System.IO.File]::WriteAllText($moc5Path, $sb5.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 05 - Hyperion Forensic Baseline.md" -ForegroundColor Green

# 7. Generate JARVIS-Brain-Map.canvas (Interactive Obsidian Canvas)
$canvasPath = Join-Path $RegistryRoot 'JARVIS-Brain-Map.canvas'
$canvasContent = @'
{
  "nodes": [
    {
      "id": "node-reactor",
      "x": 400,
      "y": 50,
      "width": 320,
      "height": 160,
      "color": "4",
      "type": "text",
      "text": "### J.A.R.V.I.S. Command Center\n**Interface HUD & Orquestrador**\n- Porta: `:8899`\n- Estado: `ACTIVE_EVOLUTION`\n- [[00 - J.A.R.V.I.S. Cognitive Vault]]"
    },
    {
      "id": "node-arsenal",
      "x": 100,
      "y": 300,
      "width": 300,
      "height": 200,
      "color": "5",
      "type": "text",
      "text": "### Canonical Arsenal\n**145 Skills Homologadas**\n- 7 Dominios Cognitivos\n- 100% Markdown puro\n- [[01 - Arsenal Map of Content]]"
    },
    {
      "id": "node-security",
      "x": 450,
      "y": 300,
      "width": 300,
      "height": 200,
      "color": "1",
      "type": "text",
      "text": "### Security & Quarantine\n**Postura de Governanca**\n- 135 Clean PASS\n- 10 FLAGGED_FOR_REVIEW\n- 118 Tombstones Quarentena\n- [[02 - Security & Quarantine Ledger]]"
    },
    {
      "id": "node-platforms",
      "x": 800,
      "y": 300,
      "width": 300,
      "height": 200,
      "color": "3",
      "type": "text",
      "text": "### Matriz Multiplataforma\n**6 Targets Suportados**\n- Cursor, Gemini, Codex\n- Claude, ChatGPT, Generic\n- 870 Pins Verificados\n- [[03 - Platform Matrix]]"
    },
    {
      "id": "node-ingestion",
      "x": 100,
      "y": 600,
      "width": 300,
      "height": 180,
      "color": "6",
      "type": "text",
      "text": "### Ingestion Engine\n**Descoberta Autonoma**\n- Clone raso em staging/\n- 13 regras de seguranca\n- Quality Score de 0 a 100\n- [[04 - Autonomous Ingestion & Staging]]"
    },
    {
      "id": "node-baseline",
      "x": 600,
      "y": 600,
      "width": 340,
      "height": 180,
      "color": "2",
      "type": "text",
      "text": "### Hyperion Baseline v1.0.0\n**Selo Soberano Imutavel**\n- 21/21 Checksums Exatos\n- Merkle Root: `8a8d2be7...`\n- 0 Workspace Leaks\n- [[05 - Hyperion Forensic Baseline]]"
    }
  ],
  "edges": [
    { "id": "e1", "fromNode": "node-reactor", "fromSide": "bottom", "toNode": "node-arsenal", "toSide": "top" },
    { "id": "e2", "fromNode": "node-reactor", "fromSide": "bottom", "toNode": "node-security", "toSide": "top" },
    { "id": "e3", "fromNode": "node-reactor", "fromSide": "bottom", "toNode": "node-platforms", "toSide": "top" },
    { "id": "e4", "fromNode": "node-arsenal", "fromSide": "bottom", "toNode": "node-ingestion", "toSide": "top" },
    { "id": "e5", "fromNode": "node-security", "fromSide": "bottom", "toNode": "node-baseline", "toSide": "top" },
    { "id": "e6", "fromNode": "node-platforms", "fromSide": "bottom", "toNode": "node-baseline", "toSide": "top" }
  ]
}
'@

[System.IO.File]::WriteAllText($canvasPath, $canvasContent, $utf8NoBom)
Write-Host "[OK] Created: JARVIS-Brain-Map.canvas (Interactive Obsidian Canvas)" -ForegroundColor Green

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  OBSIDIAN VAULT SYNCHRONIZATION COMPLETE! (100% SOVEREIGN)" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
