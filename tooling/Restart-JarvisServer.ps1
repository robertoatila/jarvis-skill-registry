$pyPath = 'C:\Users\Ad\AppData\Local\Programs\Python\Python312\pythonw.exe'
if (-not (Test-Path $pyPath)) {
    $pyPath = 'C:\Users\Ad\AppData\Local\Programs\Python\Python312\python.exe'
}
$serverScript = 'E:\.skill-registry\tooling\jarvis_server.py'

# 1. Kill existing processes on port 8899 or running jarvis_server.py
$netLines = netstat -ano | findstr :8899
if ($netLines) {
    foreach ($l in $netLines) {
        $parts = -split $l.Trim()
        $procId = $parts[-1]
        if ($procId -match '^\d+$' -and [int]$procId -gt 4) {
            Write-Host "Stopping process PID on port 8899: $procId" -ForegroundColor Yellow
            Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
        }
    }
}

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*jarvis_server.py*' } | ForEach-Object {
    Write-Host "Stopping Jarvis Python PID: $($_.ProcessId)" -ForegroundColor Yellow
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Milliseconds 600

# 2. Start server
if (Test-Path $pyPath) {
    Start-Process -FilePath $pyPath -ArgumentList "`"$serverScript`" --port 8899" -WorkingDirectory "E:\.skill-registry" -WindowStyle Hidden
    Write-Host "Iniciando servidor J.A.R.V.I.S. Python na porta 8899..." -ForegroundColor Cyan

    # 3. Health check verification loop
    $ready = $false
    $timeout = 15
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($stopwatch.Elapsed.TotalSeconds -lt $timeout) {
        Start-Sleep -Milliseconds 400
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:8899/api/status" -TimeoutSec 1 -ErrorAction Stop
            if ($resp -and $resp.phase) {
                $ready = $true
                break
            }
        } catch {}
    }

    if ($ready) {
        Write-Host "[OK] J.A.R.V.I.S. Sovereign Server ONLINE com sucesso!" -ForegroundColor Green
        Write-Host "     Skills ativas: $($resp.canonical_active_skills_count)" -ForegroundColor Gray
        Write-Host "     Repos catalogados: $($resp.total_starred_catalog_count)" -ForegroundColor Gray
        Write-Host "     URL: http://localhost:8899/" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] O servidor foi disparado, mas ainda está inicializando." -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERRO] Python não encontrado em: $pyPath" -ForegroundColor Red
}
