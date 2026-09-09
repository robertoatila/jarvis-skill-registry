# Ensure server running
$serverScript = "E:\.skill-registry\tooling\Start-JarvisServer.ps1"
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8899/api/status" -TimeoutSec 1 -ErrorAction SilentlyContinue
    if (-not $resp) {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "$serverScript" -Port 8899" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
} catch {
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "$serverScript" -Port 8899" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# Voice greeting via SAPI
try {
    $speak = New-Object -ComObject SAPI.SpVoice
    $speak.Rate = 1
    $speak.Speak("JARVIS online, senhor. Todos os 2168 repositÃ³rios e esquadrÃµes de agentes operacionais.")
} catch {}

# Open browser to Command Center HUD
Start-Process "http://localhost:8899"