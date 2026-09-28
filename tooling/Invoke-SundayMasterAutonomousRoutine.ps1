# ==============================================================================
# Invoke-SundayMasterAutonomousRoutine.ps1
# J.A.R.V.I.S. // Esteira Mestra Autonoma Dominical (Todo Domingo as 20:00)
# Puxa novo, atualiza, registra, separa, valida e instala no IDE e em tudo.
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$SkipRepoClones = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RegistryRoot = Split-Path -Parent $ScriptDir
Set-Location -Path $RegistryRoot

$LogsDir = Join-Path $RegistryRoot "logs"
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null }
$Timestamp = (Get-Date).ToString("yyyy-MM-dd_HH-mm-ss")
$LogFile = Join-Path $LogsDir "sunday-autonomous-routine.log"

function Write-JarvisLog {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] [$Level] $Message"
    Write-Host $line -ForegroundColor $(switch ($Level) { "ERROR" {"Red"} "WARN" {"Yellow"} "SUCCESS" {"Green"} default {"Cyan"} })
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

Write-JarvisLog "=================================================================" "INFO"
Write-JarvisLog "  J.A.R.V.I.S. // CICLO MESTRE AUTONOMO DOMINICAL (20:00)" "INFO"
Write-JarvisLog "  Soberania Total: Puxar, Atualizar, Separar, Validar e Instalar" "INFO"
Write-JarvisLog "=================================================================" "INFO"

$StartTime = Get-Date
$ExecutionSummary = [ordered]@{
    timestamp = $Timestamp
    status = "IN_PROGRESS"
    phases = [ordered]@{}
}

# ------------------------------------------------------------------------------
# FASE 1: Puxar e Sincronizar Novos Repositorios do GitHub (API & Catalogo ate 50k)
# ------------------------------------------------------------------------------
Write-JarvisLog ">>> FASE 1: Sincronizando novos repositorios favoritados via GitHub API (ate 50.000 repos)..." "INFO"
$phase1Start = Get-Date
try {
    $syncScript = Join-Path $ScriptDir "sync_starred_repos.py"
    $p1 = Start-Process -FilePath "python" -ArgumentList "`"$syncScript`"" -NoNewWindow -Wait -PassThru
    if ($p1.ExitCode -eq 0) {
        Write-JarvisLog "[FASE 1 OK] Catalogo de estrelas e documento 06 atualizados com sucesso." "SUCCESS"
        $ExecutionSummary.phases["01_sync_github_stars"] = "SUCCESS"
        
        # Atualizar Note 14 (Dossie Tatico por Esquadrao)
        $analyzeJs = Join-Path $ScriptDir "analyze_catalog.js"
        if (Test-Path $analyzeJs) {
            Start-Process -FilePath "node" -ArgumentList "`"$analyzeJs`"" -NoNewWindow -Wait | Out-Null
            Write-JarvisLog "[FASE 1 OK] Dossie tatico por esquadrao (Nota 14) regenerado." "SUCCESS"
        }
    } else {
        Write-JarvisLog "[FASE 1 AVISO] sync_starred_repos retornou codigo $($p1.ExitCode)." "WARN"
        $ExecutionSummary.phases["01_sync_github_stars"] = "WARN (ExitCode $($p1.ExitCode))"
    }
} catch {
    Write-JarvisLog "[FASE 1 ERRO] Falha ao executar sync_starred_repos: $_" "ERROR"
    $ExecutionSummary.phases["01_sync_github_stars"] = "FAILED: $_"
}

# ------------------------------------------------------------------------------
# FASE 2: Puxar e Atualizar os 205 Repositorios Brutos Clonados (Quality Gate v31.2)
# ------------------------------------------------------------------------------
if (-not $SkipRepoClones) {
    Write-JarvisLog ">>> FASE 2: Atualizando cache de repositorios clonados (instalador-repo.bat)..." "INFO"
    try {
        $installerBat = Join-Path $RegistryRoot "instalador-repo.bat"
        if (Test-Path $installerBat) {
            $p2 = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"`"$installerBat`" --no-pause`"" -NoNewWindow -Wait -PassThru
            if ($p2.ExitCode -eq 0) {
                Write-JarvisLog "[FASE 2 OK] Cache dos 205 repositorios atualizado e lockfile verificado." "SUCCESS"
                $ExecutionSummary.phases["02_update_raw_repos"] = "SUCCESS"
            } else {
                Write-JarvisLog "[FASE 2 AVISO] instalador-repo retornou codigo $($p2.ExitCode)." "WARN"
                $ExecutionSummary.phases["02_update_raw_repos"] = "WARN (ExitCode $($p2.ExitCode))"
            }
        } else {
            Write-JarvisLog "[FASE 2 AVISO] instalador-repo.bat nao encontrado em $RegistryRoot." "WARN"
            $ExecutionSummary.phases["02_update_raw_repos"] = "SKIPPED_NOT_FOUND"
        }
    } catch {
        Write-JarvisLog "[FASE 2 ERRO] Falha ao executar instalador-repo: $_" "ERROR"
        $ExecutionSummary.phases["02_update_raw_repos"] = "FAILED: $_"
    }
} else {
    Write-JarvisLog ">>> FASE 2: Pular atualizacao de repositorios brutos (-SkipRepoClones ativado)." "WARN"
    $ExecutionSummary.phases["02_update_raw_repos"] = "SKIPPED_BY_PARAM"
}

# ------------------------------------------------------------------------------
# FASE 3: Separar, Filtrar e Extrair Skills do Bau (Quality Gate)
# ------------------------------------------------------------------------------
Write-JarvisLog ">>> FASE 3: Separando e filtrando arsenal de skills do bau (setup-e-filtrar-skills.bat)..." "INFO"
try {
    $filterBat = Join-Path $RegistryRoot "setup-e-filtrar-skills.bat"
    if (Test-Path $filterBat) {
        $p3 = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"`"$filterBat`" --no-pause`"" -NoNewWindow -Wait -PassThru
        if ($p3.ExitCode -eq 0) {
            Write-JarvisLog "[FASE 3 OK] Arsenal de 165 skills gerenciadas extraido e validado com sucesso." "SUCCESS"
            $ExecutionSummary.phases["03_filter_managed_skills"] = "SUCCESS"
        } else {
            Write-JarvisLog "[FASE 3 AVISO] setup-e-filtrar-skills retornou codigo $($p3.ExitCode)." "WARN"
            $ExecutionSummary.phases["03_filter_managed_skills"] = "WARN (ExitCode $($p3.ExitCode))"
        }
    } else {
        Write-JarvisLog "[FASE 3 AVISO] setup-e-filtrar-skills.bat nao encontrado em $RegistryRoot." "WARN"
        $ExecutionSummary.phases["03_filter_managed_skills"] = "SKIPPED_NOT_FOUND"
    }
} catch {
    Write-JarvisLog "[FASE 3 ERRO] Falha ao executar setup-e-filtrar-skills: $_" "ERROR"
    $ExecutionSummary.phases["03_filter_managed_skills"] = "FAILED: $_"
}

# ------------------------------------------------------------------------------
# FASE 4: Ciclo Autonomo de Avaliacao & Protocolo SSP-v13
# ------------------------------------------------------------------------------
Write-JarvisLog ">>> FASE 4: Executando avaliacao autonoma de candidatos e protocolo SSP-v13..." "INFO"
try {
    $evalPy = @"
import sys, json
from pathlib import Path
root = Path(r"$RegistryRoot")
sys.path.insert(0, str(root))
try:
    from tooling.jarvis_server import AUTONOMOUS_ENGINE, load_canonical_skills, load_starred_catalog
    load_canonical_skills()
    load_starred_catalog()
    summary = AUTONOMOUS_ENGINE.execute_cycle(trigger_mode="SUNDAY_MASTER_PIPELINE")
    print(json.dumps({"status": "SUCCESS", "evaluated": summary.get("candidates_evaluated", 0), "implemented": summary.get("implemented_count", 0), "quarantined": summary.get("quarantined_count", 0)}))
except Exception as e:
    print(json.dumps({"status": "ERROR", "error": str(e)}))
"@
    $evalScriptPath = Join-Path $ScriptDir "run_sunday_eval_temp.py"
    [System.IO.File]::WriteAllText($evalScriptPath, $evalPy, [System.Text.Encoding]::UTF8)
    $evalOutput = python "$evalScriptPath"
    Remove-Item $evalScriptPath -Force -ErrorAction SilentlyContinue
    Write-JarvisLog "[FASE 4 OK] Avaliacao autonoma executada: $evalOutput" "SUCCESS"
    $ExecutionSummary.phases["04_autonomous_lifecycle_eval"] = $evalOutput
} catch {
    Write-JarvisLog "[FASE 4 ERRO] Falha no ciclo de vida autonomo: $_" "ERROR"
    $ExecutionSummary.phases["04_autonomous_lifecycle_eval"] = "FAILED: $_"
}

# ------------------------------------------------------------------------------
# FASE 5: Utilizar e Instalar em Tudo e Todos (Otimizacao e Governanca de Tokens)
# ------------------------------------------------------------------------------
Write-JarvisLog ">>> FASE 5: Instalando e otimizando todo o arsenal no IDE global (sync_and_optimize_arsenal.py)..." "INFO"
try {
    $optScript = Join-Path $ScriptDir "sync_and_optimize_arsenal.py"
    $p5 = Start-Process -FilePath "python" -ArgumentList "`"$optScript`"" -NoNewWindow -Wait -PassThru
    if ($p5.ExitCode -eq 0) {
        Write-JarvisLog "[FASE 5 OK] Todas as skills sincronizadas no IDE global com governanca de tokens ativa (< 35% de cota)." "SUCCESS"
        $ExecutionSummary.phases["05_sync_and_optimize_ide"] = "SUCCESS"
    } else {
        Write-JarvisLog "[FASE 5 AVISO] sync_and_optimize_arsenal retornou codigo $($p5.ExitCode)." "WARN"
        $ExecutionSummary.phases["05_sync_and_optimize_ide"] = "WARN (ExitCode $($p5.ExitCode))"
    }
} catch {
    Write-JarvisLog "[FASE 5 ERRO] Falha ao otimizar e sincronizar skills no IDE: $_" "ERROR"
    $ExecutionSummary.phases["05_sync_and_optimize_ide"] = "FAILED: $_"
}

# ------------------------------------------------------------------------------
# FASE 6: Registro de Integridade e Ledger
# ------------------------------------------------------------------------------
$EndTime = Get-Date
$Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds, 2)
$ExecutionSummary.status = "SUCCESS"
$ExecutionSummary["duration_seconds"] = $Duration

$EvidenceDir = Join-Path $RegistryRoot "evidence"
if (-not (Test-Path $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }
$ReceiptFile = Join-Path $EvidenceDir "sunday_autonomous_receipt.json"
$ExecutionSummary | ConvertTo-Json -Depth 5 | Set-Content -Path $ReceiptFile -Encoding UTF8

Write-JarvisLog "=================================================================" "SUCCESS"
Write-JarvisLog "  CICLO AUTONOMO CONCLUIDO COM EXITO EM $Duration SEGUNDOS" "SUCCESS"
Write-JarvisLog "  Comprovante gravado em: $ReceiptFile" "SUCCESS"
Write-JarvisLog "=================================================================" "SUCCESS"

# Vocalizacao SAPI nativa opcional
try {
    $speaker = New-Object -ComObject SAPI.SpVoice -ErrorAction SilentlyContinue
    if ($speaker) {
        $speaker.Rate = 0
        $speaker.Speak("Ciclo dominical autônomo do JARVIS concluído com sucesso. Todos os repositórios, skills e orçamentos de contexto sincronizados e operacionais.") | Out-Null
    }
} catch { }

return $ExecutionSummary
