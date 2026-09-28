# ==============================================================================
# Register-JarvisSundayTask.ps1
# J.A.R.V.I.S. // Agendador de Tarefas do Windows (Ciclo Dominical as 20:00)
# Agenda a esteira completa: puxar novo, atualizar, registrar, separar e instalar.
# ==============================================================================

[CmdletBinding()]
param(
    [string]$Time = "20:00",
    [string]$TaskName = "Jarvis-Weekly-Sunday-Autonomous-Pipeline"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RegistryRoot = Split-Path -Parent $ScriptDir
$MasterScript = Join-Path $ScriptDir "Invoke-SundayMasterAutonomousRoutine.ps1"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " J.A.R.V.I.S. // AGENDADOR DOMINICAL DO WINDOWS AS $Time" -ForegroundColor Cyan
Write-Host " Script Alvo: $MasterScript" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$pwshExe = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
if (-not $pwshExe) { $pwshExe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" }

$action = New-ScheduledTaskAction `
    -Execute $pwshExe `
    -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$MasterScript`""

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Sunday `
    -At $Time

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 15)

try {
    # Unregister existing task if present
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Register new weekly task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "J.A.R.V.I.S. Esteira Mestra Autonoma Dominical (Puxar novos repositorios, atualizar baude-skills, separar arsenal, auditar SSP-v13 e instalar no IDE com governanca de tokens)" `
        -ErrorAction Stop

    Write-Host "[OK] Tarefa agendada '$TaskName' criada com sucesso no Windows para rodar todo Domingo as $Time!" -ForegroundColor Green
    
    # Print task info
    $taskInfo = Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
    $taskInfo | Format-Table -AutoSize
} catch {
    Write-Host "[AVISO] Nao foi possivel registrar a tarefa do Windows diretamente (requer permissao de Administrador): $_" -ForegroundColor Yellow
    Write-Host "[INFO] Para registrar no Windows Task Scheduler, abra um terminal PowerShell como Administrador e execute:" -ForegroundColor Cyan
    Write-Host "powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\Register-JarvisSundayTask.ps1`"" -ForegroundColor White
}
