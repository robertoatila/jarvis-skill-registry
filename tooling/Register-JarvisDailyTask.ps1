# ==============================================================================
# Register-JarvisDailyTask.ps1
# J.A.R.V.I.S. // Agendador de Tarefas do Windows (Ciclo Autônomo Diário às 20:00)
# ==============================================================================

[CmdletBinding()]
param(
    [string]$Time = "20:00",
    [string]$TaskName = "Jarvis-Daily-Autonomous-Cycle"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " J.A.R.V.I.S. // REGISTRO DE CICLO AUTONOMO DIARIO AS $Time" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\Ad\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
}

$triggerScript = @"
import urllib.request, json, sys
try:
    req = urllib.request.Request('http://localhost:8899/api/autonomous/cycle', data=b'{}', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        print('[JARVIS AGENDADO 20:00] Ciclo executado com sucesso:', resp.read().decode('utf-8')[:200])
except Exception as e:
    print('[JARVIS AGENDADO 20:00] Servidor local nao estava rodando ou erro:', e)
"@

$tempScript = "E:\.skill-registry\tooling\run_daily_cycle.py"
[System.IO.File]::WriteAllText($tempScript, $triggerScript, [System.Text.Encoding]::UTF8)

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$tempScript`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    # Check if task already exists and unregister
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "J.A.R.V.I.S. Ciclo de Vida Autônomo Diário às $Time"
    Write-Host "[OK] Tarefa agendada '$TaskName' criada com sucesso no Windows para rodar diariamente as $Time!" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Para registrar como Tarefa do Windows, execute o PowerShell como Administrador. O agendador interno em Python e o cron do Antigravity já estão ativos!" -ForegroundColor Yellow
}
