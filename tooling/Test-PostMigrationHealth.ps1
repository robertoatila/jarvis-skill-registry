# ==============================================================================
# J.A.R.V.I.S. // Test-PostMigrationHealth.ps1
# Post-Migration Integrity & Health Check for Antigravity & Skill Registry
# ==============================================================================

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. // AUDITORIA DE SAUDE POS-MIGRACAO GOOGLE" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

$allPass = $true

# 1. Check MCP Configuration File
Write-Host "1. Verificando mcp_config.json..." -NoNewline
$mcpFile = 'C:\Users\Ad\.gemini\config\mcp_config.json'
if (Test-Path $mcpFile) {
    try {
        $mcp = [System.IO.File]::ReadAllText($mcpFile) | ConvertFrom-Json
        if ($mcp.mcpServers.'github-mcp-server' -and $mcp.mcpServers.'chrome-devtools-mcp') {
            Write-Host " [PASS] (MCPs configurados e validos)" -ForegroundColor Green
        } else {
            Write-Host " [WARN] (Faltando servidores no mcp_config.json)" -ForegroundColor Yellow
            $allPass = $false
        }
    } catch {
        Write-Host " [FAIL] (Arquivo corrompido)" -ForegroundColor Red
        $allPass = $false
    }
} else {
    Write-Host " [FAIL] (Arquivo nao encontrado)" -ForegroundColor Red
    $allPass = $false
}

# 2. Check GitHub API Token
Write-Host "2. Verificando Token do GitHub via REST API..." -NoNewline
$token = $env:GITHUB_PERSONAL_ACCESS_TOKEN
if ([string]::IsNullOrWhiteSpace($token) -and (Test-Path $mcpFile)) {
    try {
        $mcp = [System.IO.File]::ReadAllText($mcpFile) | ConvertFrom-Json
        $token = $mcp.mcpServers.'github-mcp-server'.env.GITHUB_PERSONAL_ACCESS_TOKEN
    } catch {}
}

if (-not [string]::IsNullOrWhiteSpace($token)) {
    try {
        $headers = @{ "Authorization" = "Bearer $token"; "User-Agent" = "JARVIS-Health-Check" }
        $user = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -TimeoutSec 8
        Write-Host " [PASS] (Autenticado como: $($user.login))" -ForegroundColor Green
    } catch {
        Write-Host " [WARN] (Token falhou na API do GitHub: $($_.Exception.Message))" -ForegroundColor Yellow
    }
} else {
    Write-Host " [FAIL] (Nenhum token encontrado)" -ForegroundColor Red
    $allPass = $false
}

# 3. Check Workspace Skills Directory
Write-Host "3. Verificando Skills do Workspace (C:\Users\Ad\.gemini\skills)..." -NoNewline
$userSkillsDir = 'C:\Users\Ad\.gemini\skills'
if (Test-Path $userSkillsDir) {
    $count = (Get-ChildItem -Path $userSkillsDir -Directory).Count
    if ($count -ge 160) {
        Write-Host " [PASS] ($count skills ativas no workspace)" -ForegroundColor Green
    } else {
        Write-Host " [WARN] (Apenas $count skills encontradas)" -ForegroundColor Yellow
    }
} else {
    Write-Host " [FAIL] (Diretorio nao encontrado)" -ForegroundColor Red
    $allPass = $false
}

# 4. Check Canonical Registry Arsenal
Write-Host "4. Verificando Arsenal Canonico (E:\.skill-registry\skills)..." -NoNewline
$canonicalDir = Join-Path $RegistryRoot 'skills'
if (Test-Path $canonicalDir) {
    $canCount = (Get-ChildItem -Path $canonicalDir -Directory).Count
    if ($canCount -ge 143) {
        Write-Host " [PASS] ($canCount skills canonicas homologadas)" -ForegroundColor Green
    } else {
        Write-Host " [FAIL] (Esperado no minimo 143, encontrado $canCount)" -ForegroundColor Red
        $allPass = $false
    }
} else {
    Write-Host " [FAIL] (Diretorio canonico nao encontrado)" -ForegroundColor Red
    $allPass = $false
}

# 5. Check Merkle Root
Write-Host "5. Verificando Merkle Root Criptografica Hyperion..." -NoNewline
$stateFile = Join-Path $RegistryRoot 'state\current-state.json'
if (Test-Path $stateFile) {
    $st = [System.IO.File]::ReadAllText($stateFile) | ConvertFrom-Json
    $expectedRoot = "8a8d2be7d354536f86d196b5d751b22450301650f81b54b93b5e746330d98d07"
    if ($st.canonical_merkle_root -eq $expectedRoot) {
        Write-Host " [PASS] (Merkle Root 100% integra)" -ForegroundColor Green
    } else {
        Write-Host " [FAIL] (Merkle diverge: $($st.canonical_merkle_root))" -ForegroundColor Red
        $allPass = $false
    }
} else {
    Write-Host " [FAIL] (Estado soberano ausente)" -ForegroundColor Red
    $allPass = $false
}

# 6. Check Obsidian Vault MOCs
Write-Host "6. Verificando Cofre do Obsidian & MOCs..." -NoNewline
$mocs = @(
    '00 - J.A.R.V.I.S. Cognitive Vault.md',
    '01 - Arsenal Map of Content.md',
    '02 - Security & Quarantine Ledger.md',
    '03 - Platform Matrix.md',
    '04 - Autonomous Ingestion & Staging.md',
    '05 - Hyperion Forensic Baseline.md',
    '06 - GitHub Starred Repositories.md',
    'JARVIS-Brain-Map.canvas'
)
$missingMocs = @()
foreach ($m in $mocs) {
    if (-not (Test-Path (Join-Path $RegistryRoot $m))) { $missingMocs += $m }
}
if ($missingMocs.Count -eq 0) {
    Write-Host " [PASS] (Todos os 7 MOCs + Canvas intactos)" -ForegroundColor Green
} else {
    Write-Host " [WARN] (MOCs ausentes: $($missingMocs -join ', '))" -ForegroundColor Yellow
}

# 7. Check J.A.R.V.I.S. Command Center Server
Write-Host "7. Verificando J.A.R.V.I.S. Server na porta 8899..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri "http://localhost:8899/api/status" -TimeoutSec 3
    if ($r.phase -eq "PHASE_33_JARVIS_ORCHESTRATION") {
        Write-Host " [PASS] (Online e respondendo)" -ForegroundColor Green
    } else {
        Write-Host " [WARN] (Respondendo com fase inesperada)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [INFO] (Servidor offline; inicie com 'skillctl jarvis')" -ForegroundColor Cyan
}

Write-Host "=================================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host "  RESULTADO: 100% OPERACIONAL E HOMOLOGADO POS-MIGRACAO!" -ForegroundColor Green
} else {
    Write-Host "  RESULTADO: ALGUNS PONTOS REQUEREM ATENCAO (VEJA ACIMA)" -ForegroundColor Yellow
}
Write-Host "=================================================================" -ForegroundColor Cyan
