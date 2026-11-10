param(
    [Parameter(Mandatory = $true)]
    [string]$SkillsRoot,

    [Parameter(Mandatory = $true)]
    [string]$StageRoot,

    [Parameter(Mandatory = $true)]
    [string]$AddList,

    [Parameter(Mandatory = $true)]
    [string]$SkipList,

    [Parameter(Mandatory = $true)]
    [string]$ExtraList,

    [Parameter(Mandatory = $true)]
    [string]$MissingList
)

$ErrorActionPreference = "Stop"

$ExpectedManaged = 165
$ExpectedOverlap = 77
$ExpectedDelta = 87

# Nomes reservados pelo proprio ChatGPT.
# skill-creator e uma skill nativa/default e nao pode ser enviada por upload.
$ReservedChatGPT = @(
    "skill-creator"
)

# Snapshot antigo: skills que ja estavam no ChatGPT.
$ExistingChatGPT = @(
    "Impeccable"
    "backend architect"
    "devops deploy"
    "taste skill"
    "nodejs backend patterns"
    "react best practices"
    "huashu design"
    "typescript expert"
    "testing for xss vulnerabilities"
    "zod validation expert"
    "skill installer"
    "github workflow automation"
    "git advanced workflows"
    "sqlmap database pentesting"
    "deployment engineer"
    "sql injection testing"
    "mcp builder"
    "api patterns"
    "testing api for broken object level authorization"
    "api documenter"
    "api fuzzing bug bounty"
    "ui ux pro max"
    "broken authentication"
    "shadcn"
    "testing api for mass assignment vulnerability"
    "007"
    "senior frontend"
    "backend dev guidelines"
    "testing api security with owasp top 10"
    "skill sentinel"
    "saas mvp launcher"
    "antigravity skill orchestrator"
    "appdeploy"
    "OpenAI Docs"
    "high end visual design"
    "sql optimization patterns"
    "idor testing"
    "web security testing"
    "cred omega"
    "code review ai ai review"
    "codex antigravity skill policy"
    "security audit"
    "vercel deployment"
    "fastapi pro"
    "tailwind design system"
    "production code audit"
    "ai engineer"
    "github automation"
    "github actions templates"
    "modern javascript patterns"
    "claude code expert"
    "java springboot"
    "multi agent task orchestrator"
    "burp suite testing"
    "sql pro"
    "java pro"
    "database architect"
    "cc skill security review"
    "testing api authentication weaknesses"
    "aws secrets rotation"
    "javascript typescript typescript scaffold"
    "logic lens"
    "security auditor"
    "codebase audit pre push"
    "spring boot testing"
    "cloud devops"
    "aws serverless"
    "springboot tdd"
    "typescript pro"
    "database migration"
    "tokenwise"
    "bash pro"
    "mock hunter"
    "springboot verification"
    "backend security coder"
    "jpa patterns"
    "database migrations migration observability"
    "gsd context workflow"
    "design taste frontend"
    "backend development feature development"
    "database migrations sql migrations"
    "springboot security"
    "gemini api integration"
    "api design principles"
    "skill router"
    "frontend dev guidelines"
    "security and hardening"
    "aws security audit"
    "tailwind patterns"
    "using agent skills"
    "laravel security audit"
    "docker expert"
    "frontend design"
    "react patterns"
    "parallel agents"
    "zustand store ts"
    "python pro"
    "frontend mobile security xss scan"
    "python fastapi development"
    "nextjs app router patterns"
    "nextjs best practices"
    "javascript pro"
    "java coding standards"
    "mcp tool developer"
    "api endpoint builder"
    "frontend security coder"
    "cloudflare workers expert"
    "ai engineering toolkit"
    "performance engineer"
    "aws iam best practices"
    "api security best practices"
    "react nextjs development"
    "codex review"
    "postgresql"
    "code review excellence"
    "api security testing"
    "postgresql optimization"
    "database"
    "agent memory mcp"
    "typescript advanced types"
    "react modernization"
    "privacy by design"
    "cloud architect"
    "code review and quality"
    "frontend ui engineering"
    "database admin"
    "react state management"
    "database optimizer"
    "code review checklist"
    "git workflow and versioning"
    "react ui patterns"
    "nodejs best practices"
    "ci cd and automation"
    "code reviewer"
    "devops troubleshooter"
    "database design"
    "php pro"
    "React Component Performance"
    "error handling patterns"
    "mysql patterns"
    "architect review"
    "deployment procedures"
    "frontend developer"
)

# Identidades reais (campo name:) do arsenal v31.2 gerenciado.
$ManagedV312 = @(
    "agent-skill-stack"
    "agent-supply-chain"
    "agentic-actions-auditor"
    "ai-engineer"
    "ai-engineering-toolkit"
    "api-and-interface-design"
    "api-documenter"
    "api-endpoint-builder"
    "api-fuzzing-bug-bounty"
    "api-patterns"
    "api-security-best-practices"
    "api-security-testing"
    "arthas"
    "assistant-ui"
    "auth-implementation-patterns"
    "aws-compute"
    "aws-secrets-rotation"
    "aws-security"
    "aws-serverless"
    "backend-architect"
    "backend-dev-guidelines"
    "backend-development-feature-development"
    "backend-security-coder"
    "bash-defensive-patterns"
    "bash-linux"
    "book-to-skill"
    "broken-authentication"
    "burp-suite-testing"
    "chatgpt-apps"
    "chrome-devtools"
    "ci-cd-and-automation"
    "claude-code-expert"
    "cloud-architect"
    "code-simplification"
    "codebase-audit-pre-push"
    "codex-antigravity-skill-policy"
    "context-budget"
    "context-compression"
    "context-engineering"
    "database-admin"
    "database-architect"
    "database-design"
    "database-migrations-migration-observability"
    "database-migrations-sql-migrations"
    "database-optimizer"
    "deploy-to-vercel"
    "deprecation-and-migration"
    "design-dna"
    "devops-deploy"
    "devops-troubleshooter"
    "dispatching-parallel-agents"
    "distributed-tracing"
    "docker-expert"
    "documentation-and-adrs"
    "domain-modeling"
    "error-handling-patterns"
    "fastapi-pro"
    "figma-implement-design"
    "frontend-a11y"
    "frontend-api-integration-patterns"
    "frontend-design"
    "frontend-mobile-security-xss-scan"
    "frontend-security-coder"
    "frontend-ui-engineering"
    "gemini-api-integration"
    "gh-address-comments"
    "gh-fix-ci"
    "git-advanced-workflows"
    "git-pr-workflows-pr-enhance"
    "git-workflow-and-versioning"
    "github-actions-templates"
    "gitnexus-cli"
    "gitnexus-debugging"
    "gitnexus-exploring"
    "gitnexus-impact-analysis"
    "gitnexus-pdg-query"
    "gitnexus-plan"
    "gitnexus-refactoring"
    "gitnexus-review"
    "gsap-core"
    "gsap-performance"
    "gsap-react"
    "gsap-scrolltrigger"
    "huggingface-best"
    "impeccable"
    "implementing-devsecops-security-scanning"
    "incremental-implementation"
    "integrating-dast-with-owasp-zap-in-pipeline"
    "integrating-sast-into-github-actions-pipeline"
    "java-coding-standards"
    "java-pro"
    "javascript-pro"
    "javascript-testing-patterns"
    "javascript-typescript-typescript-scaffold"
    "jpa-patterns"
    "k6-load-testing"
    "laravel-security-audit"
    "linux-troubleshooting"
    "mcp-builder"
    "mock-hunter"
    "motion-design"
    "mysql-patterns"
    "network-engineer"
    "nextjs-app-router-patterns"
    "nodejs-backend-patterns"
    "observability-and-instrumentation"
    "openai-docs"
    "openapi-spec-generation"
    "performance-optimization"
    "performing-api-inventory-and-discovery"
    "performing-sca-dependency-scanning-with-snyk"
    "php-pro"
    "planning-with-files"
    "playwright-cli"
    "privacy-by-design"
    "production-audit"
    "python-pro"
    "react-doctor"
    "react-modernization"
    "react-state-management"
    "react-testing"
    "saas-multi-tenant"
    "securing-serverless-functions"
    "security-review"
    "security-scan"
    "shadcn"
    "shipping-and-launch"
    "skill-creator"
    "skill-installer"
    "source-driven-development"
    "spec-driven-development"
    "spring-boot-testing"
    "springboot-patterns"
    "springboot-security"
    "springboot-tdd"
    "springboot-verification"
    "sql-injection-testing"
    "sql-optimization-patterns"
    "sql-pro"
    "sqlmap-database-pentesting"
    "subagent-driven-development"
    "supabase-postgres-best-practices"
    "systematic-debugging"
    "tailwind-design-system"
    "tailwind-patterns"
    "test-driven-development"
    "testing-api-for-broken-object-level-authorization"
    "testing-oauth2-implementation-flaws"
    "threejs-animation"
    "threejs-fundamentals"
    "typescript-advanced-types"
    "typescript-expert"
    "ui-ux-pro-max"
    "use-railway"
    "using-agent-skills"
    "using-git-worktrees"
    "vercel-composition-patterns"
    "vercel-optimize"
    "vercel-react-best-practices"
    "verification-before-completion"
    "web-design-guidelines"
    "web-security-testing"
    "webapp-testing"
    "workers-best-practices"
    "zod-validation-expert"
)

$AssistantUiDescription = "Overview and router for assistant-ui, the React library for composable AI chat interfaces. Use for high-level architecture, package selection, runtime choice, core primitives, message model, and deciding which focused assistant-ui skill to use. Covers @assistant-ui/react, AI SDK, LangChain/LangGraph adapters, assistant-stream, assistant-cloud, React Native/Ink bindings, AssistantRuntimeProvider, Thread/Message/Composer primitives, useAui/useAuiState/useAuiEvent, and runtime selection. For hands-on setup, runtime, primitives, tools, streaming, cloud, thread-list, copilots, markdown, react-mcp, observability, or updates, route to the corresponding focused skill."

function Normalize-Name {
    param([string]$Value)
    $v = $Value.Trim().ToLowerInvariant().Replace("_", "-")
    $v = [regex]::Replace($v, "[^a-z0-9]+", "-")
    return $v.Trim("-")
}

function Get-FrontMatterBounds {
    param([string[]]$Lines)
    if ($Lines.Count -lt 3 -or $Lines[0].Trim() -ne "---") { return $null }
    for ($i = 1; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i].Trim() -eq "---") {
            return [pscustomobject]@{ Start = 0; End = $i }
        }
    }
    return $null
}

function Get-LeadingIndent {
    param([string]$Line)
    $m = [regex]::Match($Line, "^(\s*)")
    return $m.Groups[1].Value.Length
}

function Get-YamlFieldRange {
    param(
        [string[]]$Lines,
        [int]$FrontMatterEnd,
        [string]$FieldName
    )

    for ($i = 1; $i -lt $FrontMatterEnd; $i++) {
        if ($Lines[$i] -match ("^(\s*)" + [regex]::Escape($FieldName) + "\s*:\s*(.*)$")) {
            $keyIndent = $Matches[1].Length
            $rest = $Matches[2]
            $start = $i
            $end = $i

            if ($rest.StartsWith('"') -and -not ($rest.Length -gt 1 -and $rest.TrimEnd().EndsWith('"'))) {
                for ($j = $i + 1; $j -lt $FrontMatterEnd; $j++) {
                    $end = $j
                    if ($Lines[$j].TrimEnd().EndsWith('"')) { break }
                }
                return [pscustomobject]@{ Start = $start; End = $end }
            }

            if ($rest.StartsWith("'") -and -not ($rest.Length -gt 1 -and $rest.TrimEnd().EndsWith("'"))) {
                for ($j = $i + 1; $j -lt $FrontMatterEnd; $j++) {
                    $end = $j
                    if ($Lines[$j].TrimEnd().EndsWith("'")) { break }
                }
                return [pscustomobject]@{ Start = $start; End = $end }
            }

            if ($rest -match "^[>|][+-]?\s*$" -or [string]::IsNullOrWhiteSpace($rest)) {
                for ($j = $i + 1; $j -lt $FrontMatterEnd; $j++) {
                    if ($Lines[$j].Trim() -eq "") {
                        $end = $j
                        continue
                    }
                    if ((Get-LeadingIndent $Lines[$j]) -le $keyIndent) { break }
                    $end = $j
                }
                return [pscustomobject]@{ Start = $start; End = $end }
            }

            return [pscustomobject]@{ Start = $start; End = $end }
        }
    }
    return $null
}

function Get-YamlFieldValue {
    param(
        [string[]]$Lines,
        [object]$Range,
        [string]$FieldName
    )

    if ($null -eq $Range) { return $null }

    $first = $Lines[$Range.Start] -replace ("^\s*" + [regex]::Escape($FieldName) + "\s*:\s*"), ""
    $parts = New-Object System.Collections.Generic.List[string]

    if (-not [string]::IsNullOrWhiteSpace($first) -and $first -notmatch "^[>|][+-]?\s*$") {
        $parts.Add($first.Trim())
    }

    for ($i = $Range.Start + 1; $i -le $Range.End; $i++) {
        $t = $Lines[$i].Trim()
        if ($t -ne "") { $parts.Add($t) }
    }

    $value = ($parts -join " ").Trim()

    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        if ($value.Length -ge 2) {
            $value = $value.Substring(1, $value.Length - 2)
        }
    }

    return $value.Trim()
}

function Patch-AssistantUi {
    param([string]$SkillMd)

    $text = [System.IO.File]::ReadAllText($SkillMd, [System.Text.Encoding]::UTF8)
    $newline = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
    $lines = $text -split "`r?`n"

    $bounds = Get-FrontMatterBounds -Lines $lines
    if ($null -eq $bounds) { throw "assistant-ui sem front matter valido" }

    $descRange = Get-YamlFieldRange -Lines $lines -FrontMatterEnd $bounds.End -FieldName "description"
    if ($null -eq $descRange) { throw "assistant-ui sem description" }

    $before = if ($descRange.Start -gt 0) { $lines[0..($descRange.Start - 1)] } else { @() }
    $after = if ($descRange.End + 1 -lt $lines.Count) { $lines[($descRange.End + 1)..($lines.Count - 1)] } else { @() }

    $replacement = 'description: "' + $AssistantUiDescription.Replace('"', '\"') + '"'
    $lines = @($before + $replacement + $after)

    [System.IO.File]::WriteAllText(
        $SkillMd,
        ($lines -join $newline),
        (New-Object System.Text.UTF8Encoding($false))
    )
}

# Sets canônicos.
$existingSet = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($n in $ExistingChatGPT) {
    [void]$existingSet.Add((Normalize-Name $n))
}

$managedSet = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($n in $ManagedV312) {
    [void]$managedSet.Add((Normalize-Name $n))
}

$reservedSet = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($n in $ReservedChatGPT) {
    [void]$reservedSet.Add((Normalize-Name $n))
}

if ($managedSet.Count -ne $ExpectedManaged) {
    Write-Host "[ERRO] Manifest interno v31.2 invalido: $($managedSet.Count)/$ExpectedManaged." -ForegroundColor Red
    exit 1
}

# Indexar todas as pastas locais pelo name: real do SKILL.md.
$skillDirs = Get-ChildItem -LiteralPath $SkillsRoot -Directory | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md")
}

$byName = @{}
$extras = New-Object System.Collections.Generic.List[string]

foreach ($dir in $skillDirs) {
    $skillMd = Join-Path $dir.FullName "SKILL.md"
    $text = [System.IO.File]::ReadAllText($skillMd, [System.Text.Encoding]::UTF8)
    $lines = $text -split "`r?`n"

    $bounds = Get-FrontMatterBounds -Lines $lines
    if ($null -eq $bounds) {
        $extras.Add("$($dir.Name) | front matter invalido")
        continue
    }

    $nameRange = Get-YamlFieldRange -Lines $lines -FrontMatterEnd $bounds.End -FieldName "name"
    $name = Get-YamlFieldValue -Lines $lines -Range $nameRange -FieldName "name"

    if ([string]::IsNullOrWhiteSpace($name)) {
        $extras.Add("$($dir.Name) | name ausente/vazio")
        continue
    }

    $normalized = Normalize-Name $name

    if ($byName.ContainsKey($normalized)) {
        Write-Host "[ERRO] Duas pastas possuem o mesmo name real: $name" -ForegroundColor Red
        Write-Host "  $($byName[$normalized].FullName)"
        Write-Host "  $($dir.FullName)"
        exit 1
    }

    $byName[$normalized] = [pscustomobject]@{
        Name = $name
        Folder = $dir.Name
        FullName = $dir.FullName
    }

    if (-not $managedSet.Contains($normalized)) {
        $extras.Add("$name | pasta=$($dir.Name)")
    }
}

# Garantir que as 165 gerenciadas existem, independentemente de extras.
$missing = New-Object System.Collections.Generic.List[string]
$managedLocal = New-Object System.Collections.Generic.List[object]

foreach ($expected in $ManagedV312) {
    $k = Normalize-Name $expected
    if (-not $byName.ContainsKey($k)) {
        $missing.Add($expected)
    }
    else {
        $managedLocal.Add($byName[$k])
    }
}

$missing | Sort-Object | Set-Content -LiteralPath $MissingList -Encoding UTF8
$extras  | Sort-Object | Set-Content -LiteralPath $ExtraList -Encoding UTF8

if ($missing.Count -gt 0) {
    Write-Host "[ERRO] Faltam $($missing.Count) skills gerenciadas da v31.2." -ForegroundColor Red
    Write-Host "Veja: $MissingList"
    exit 1
}

if ($managedLocal.Count -ne $ExpectedManaged) {
    Write-Host "[ERRO] Selecao gerenciada inesperada: $($managedLocal.Count)/$ExpectedManaged." -ForegroundColor Red
    exit 1
}

# Calcular delta somente dentro das 165 gerenciadas.
$toAdd = New-Object System.Collections.Generic.List[object]
$toSkip = New-Object System.Collections.Generic.List[object]

$reservedSkipped = New-Object System.Collections.Generic.List[object]

foreach ($item in $managedLocal) {
    $normalizedName = Normalize-Name $item.Name

    if ($reservedSet.Contains($normalizedName)) {
        $reservedSkipped.Add($item)
    }
    elseif ($existingSet.Contains($normalizedName)) {
        $toSkip.Add($item)
    }
    else {
        $toAdd.Add($item)
    }
}

if ($toSkip.Count -ne $ExpectedOverlap -or $reservedSkipped.Count -ne 1 -or $toAdd.Count -ne $ExpectedDelta) {
    Write-Host "[ERRO] Diff gerenciado inesperado." -ForegroundColor Red
    Write-Host "  Ja existentes: $($toSkip.Count) / esperado $ExpectedOverlap"
    Write-Host "  Reservadas:    $($reservedSkipped.Count) / esperado 1"
    Write-Host "  Novas:         $($toAdd.Count) / esperado $ExpectedDelta"
    exit 1
}

if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StageRoot -Force | Out-Null

foreach ($item in $toAdd) {
    $dst = Join-Path $StageRoot $item.Folder
    Copy-Item -LiteralPath $item.FullName -Destination $dst -Recurse -Force

    $copiedMd = Join-Path $dst "SKILL.md"

    if ((Normalize-Name $item.Name) -eq "assistant-ui") {
        Patch-AssistantUi -SkillMd $copiedMd
    }

    $text = [System.IO.File]::ReadAllText($copiedMd, [System.Text.Encoding]::UTF8)
    $lines = $text -split "`r?`n"
    $bounds = Get-FrontMatterBounds -Lines $lines
    $descRange = Get-YamlFieldRange -Lines $lines -FrontMatterEnd $bounds.End -FieldName "description"
    $desc = Get-YamlFieldValue -Lines $lines -Range $descRange -FieldName "description"

    if ([string]::IsNullOrWhiteSpace($desc) -or $desc.Length -gt 1024) {
        Write-Host "[ERRO] description invalida apos sanitizacao: $($item.Name) ($($desc.Length) chars)" -ForegroundColor Red
        exit 1
    }
}

$toAdd | Sort-Object Name | ForEach-Object { $_.Name } |
    Set-Content -LiteralPath $AddList -Encoding UTF8

@(
    $toSkip | Sort-Object Name | ForEach-Object { $_.Name + " | ja existe no ChatGPT" }
    $reservedSkipped | Sort-Object Name | ForEach-Object { $_.Name + " | reservado pelo ChatGPT" }
) | Set-Content -LiteralPath $SkipList -Encoding UTF8

Write-Host "[OK] Pastas locais encontradas: $($skillDirs.Count)"
Write-Host "[OK] Arsenal gerenciado v31.2:  $($managedLocal.Count)/$ExpectedManaged"
Write-Host "[OK] Extras ignoradas:          $($extras.Count)"
Write-Host "[OK] Ja no ChatGPT:             $($toSkip.Count)"
Write-Host "[OK] Reservadas pelo ChatGPT:   $($reservedSkipped.Count)"
Write-Host "[OK] Novas para adicionar:      $($toAdd.Count)"
Write-Host "[OK] Todas as descriptions do delta: 1-1024 caracteres."
Write-Host "[OK] Origem preservada."
