# Skill Registry - Tooling: Comprehensive Test Suite Runner
# Executes all 34 test harnesses across all phases (1-27) and reports exact status

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$ReportJson = (Join-Path $RegistryRoot 'reports\all-test-suites-execution.json'),
    [string]$ReportMd = (Join-Path $RegistryRoot 'reports\all-test-suites-execution.md')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$testsDir = Join-Path $RegistryRoot 'tests'
$testFiles = Get-ChildItem -Path $testsDir -Filter 'Invoke-*.ps1' | Sort-Object Name

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " EXECUTING ALL 34 TEST HARNESSES ACROSS SKILL REGISTRY      " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$suiteResults = New-Object 'System.Collections.Generic.List[object]'
$passedCount = 0
$failedCount = 0
$totalStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

foreach ($tf in $testFiles) {
    Write-Host ("`n--> Running: " + $tf.Name + " ...") -ForegroundColor Cyan
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $errOutput = New-Object 'System.Collections.Generic.List[string]'
    
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "powershell.exe"
    $pinfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$($tf.FullName)`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.WorkingDirectory = $RegistryRoot
    
    $p = [System.Diagnostics.Process]::Start($pinfo)
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    $sw.Stop()
    
    $isPass = ($p.ExitCode -eq 0)
    $status = if ($isPass) { 'PASS' } else { 'FAIL' }
    
    if ($isPass) {
        $passedCount++
        Write-Host ("    [PASS] " + $tf.Name + " (" + $sw.ElapsedMilliseconds + "ms)") -ForegroundColor Green
    } else {
        $failedCount++
        Write-Host ("    [FAIL] " + $tf.Name + " (ExitCode: " + $p.ExitCode + ", " + $sw.ElapsedMilliseconds + "ms)") -ForegroundColor Red
        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            Write-Host ("    ERROR: " + ($stderr.Trim().Split("`n")[0])) -ForegroundColor Yellow
        }
    }
    
    [void]$suiteResults.Add([ordered]@{
        suite_name = $tf.Name
        file_path = $tf.FullName
        status = $status
        exit_code = $p.ExitCode
        elapsed_ms = $sw.ElapsedMilliseconds
        error_sample = if (-not [string]::IsNullOrWhiteSpace($stderr)) { $stderr.Trim().Split("`n")[0] } else { $null }
    })
}
$totalStopwatch.Stop()

$nowUtc = [DateTime]::UtcNow.ToString('o')
$reportData = [ordered]@{
    schema = "skill-registry.all-tests-execution/v1"
    executed_utc = $nowUtc
    total_suites = $testFiles.Count
    passed_suites = $passedCount
    failed_suites = $failedCount
    elapsed_seconds = [Math]::Round($totalStopwatch.Elapsed.TotalSeconds, 2)
    suites = $suiteResults
}

[System.IO.File]::WriteAllText($ReportJson, ($reportData | ConvertTo-Json -Depth 5), $utf8NoBom)

$reportLines = @(
    "# Relatorio de Execucao Integral de Todas as Suites de Teste",
    "",
    ('- **Data/Hora UTC:** ' + $nowUtc),
    ('- **Total de Suites:** ' + $testFiles.Count),
    ('- **Suites Aprovadas:** ' + $passedCount),
    ('- **Suites Reprovadas:** ' + $failedCount),
    ('- **Tempo Total:** ' + [Math]::Round($totalStopwatch.Elapsed.TotalSeconds, 2) + 's'),
    '',
    '| Suite | Status | Exit Code | Duracao | Erro / Detalhes |',
    '| :--- | :---: | :---: | :---: | :--- |'
)

foreach ($sr in $suiteResults) {
    $err = if ($null -ne $sr.error_sample) { $sr.error_sample.Replace('|', '/') } else { '-' }
    $reportLines += ('| `' + $sr.suite_name + '` | **' + $sr.status + '** | ' + $sr.exit_code + ' | ' + $sr.elapsed_ms + 'ms | ' + $err + ' |')
}

[System.IO.File]::WriteAllText($ReportMd, ($reportLines -join "`r`n"), $utf8NoBom)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host (" TEST RESULTS: " + $passedCount + " PASSED, " + $failedCount + " FAILED out of " + $testFiles.Count) -ForegroundColor (if ($failedCount -eq 0) { 'Green' } else { 'Yellow' })
Write-Host "============================================================" -ForegroundColor Cyan
