<#
.SYNOPSIS
    J.A.R.V.I.S. Cognitive OS - Autonomous 5-Step Skill Workflow CLI
.DESCRIPTION
    Executes the complete autonomous lifecycle for any GitHub repository:
    [1. LER]       - Ingests repository metadata and structure.
    [2. ANALISAR]   - Static threat review (13 rules) and quality scoring.
    [3. PODAR]     - Applies Active Pruning (Token budget <= 25 words frontmatter).
    [4. MELHORAR]  - Synthesizes Level 9 Skill specification (SKILL.md).
    [5. IMPLEMENTAR]- Homologates and commits to the Sovereign Arsenal.
.EXAMPLE
    .\Invoke-JarvisSkillWorkflow.ps1 -RepositorySource "KiExitDispatcher/GoDefender"
    .\Invoke-JarvisSkillWorkflow.ps1 -RepositorySource "vllm-project/vllm" -AutoCommit
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$RepositorySource,

    [string]$RegistryRoot = 'E:\.skill-registry',

    [switch]$AutoCommit,

    [switch]$CopyToGeminiGlobal
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Import Ingestion Module
$ingestModule = Join-Path $RegistryRoot 'tooling\IngestionEngine.psm1'
if (-not (Test-Path $ingestModule)) {
    throw "IngestionEngine module not found at: $ingestModule"
}
Import-Module $ingestModule -Force

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. SKILL FACTORY // AUTONOMOUS 5-STEP WORKFLOW" -ForegroundColor Green
Write-Host "  Repository Source: $RepositorySource" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

# Execute Workflow
$result = Invoke-JarvisAutonomousWorkflow -RepositorySource $RepositorySource -RegistryRoot $RegistryRoot

Write-Host $result.logs -ForegroundColor Gray

$prop = $result.proposal

Write-Host "`n--- RESUMO DO WORKFLOW J.A.R.V.I.S. ---" -ForegroundColor Cyan
Write-Host "Canonical Name:      $($prop.canonical_name)" -ForegroundColor White
Write-Host "Security Status:     $($prop.security_status)" -ForegroundColor $(if ($prop.security_status -eq 'PASS') { 'Green' } else { 'Yellow' })
Write-Host "Quality Score:       $($prop.quality_score)/100" -ForegroundColor Green
Write-Host "Moat Classification: $($prop.moat_classification)" -ForegroundColor Magenta
Write-Host "Token Savings:       $($prop.token_savings_pct)% (Pruned to $($prop.pruned_word_count) words)" -ForegroundColor Yellow
Write-Host "Duration:            $($result.duration_ms) ms" -ForegroundColor DarkGray

if ($AutoCommit) {
    Write-Host "`n[AUTO-COMMIT] Homologando e inserindo no Arsenal Soberano..." -ForegroundColor Cyan
    
    $stagingDir = Join-Path $RegistryRoot ("staging\ingestion\" + $prop.canonical_name)
    if (-not (Test-Path $stagingDir)) {
        [void](New-Item -ItemType Directory -Path $stagingDir -Force)
    }
    
    $skillMd = Join-Path $stagingDir "SKILL.md"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($skillMd, $prop.manifest_preview, $utf8NoBom)
    
    $commitRes = Commit-PromotedSkillToArsenal -Proposal $prop -SourceDir $stagingDir -RegistryRoot $RegistryRoot
    Write-Host "Commit Concluído! Nova contagem de skills ativas: $($commitRes.new_active_skills_count)" -ForegroundColor Green
    Write-Host "Novo Merkle Root: $($commitRes.updated_merkle_root)" -ForegroundColor DarkGray
    
    if ($CopyToGeminiGlobal) {
        $geminiSkillsDir = 'C:\Users\Ad\.gemini\config\skills'
        if (Test-Path $geminiSkillsDir) {
            $dest = Join-Path $geminiSkillsDir $prop.canonical_name
            if (-not (Test-Path $dest)) { [void](New-Item -ItemType Directory -Path $dest -Force) }
            Copy-Item -Path (Join-Path $stagingDir "*") -Destination $dest -Recurse -Force
            Write-Host "Exportado para Gemini Global: $dest" -ForegroundColor Green
        }
    }
} else {
    Write-Host "`n[INFO] Para homologar e comitar este artefato, execute novamente com a flag -AutoCommit." -ForegroundColor Yellow
}
