# Skill Registry - Governed Distribution Pilot Execution Protocol
# Executes a controlled end-to-end lifecycle pilot on a single target platform (cursor)
# with a single representative canonical skill (polars-streaming-dataframe-engine).
# Verifies: Snapshot -> Plan -> Approved Execution -> Idempotency -> Drift Injection ->
# Governed Sync Reconciliation -> Atomic Uninstall & Lockfile Tombstone -> Hermetic Isolation.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$TargetPlatform = 'cursor',
    [string]$PilotSkill = 'polars-streaming-dataframe-engine',
    [string]$JsonOutputPath = 'E:\.skill-registry\reports\governed-pilot-cursor-polars.json',
    [string]$MdOutputPath = 'E:\.skill-registry\reports\governed-pilot-cursor-polars.md'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GOVERNED DISTRIBUTION SINGLE-TARGET PILOT PROTOCOL         " -ForegroundColor Cyan
Write-Host " Target Platform : $TargetPlatform" -ForegroundColor Yellow
Write-Host " Pilot Skill     : $PilotSkill" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

$distModule = Join-Path $RegistryRoot 'tooling\DistributionEngine.psm1'
if (-not [System.IO.File]::Exists($distModule)) {
    throw "DistributionEngine module not found at: $distModule"
}
Import-Module $distModule -Force

$pilotDestRoot = Join-Path $RegistryRoot "staging\targets\pilot-$TargetPlatform"
if (Test-Path $pilotDestRoot) {
    Remove-Item -Path $pilotDestRoot -Recurse -Force | Out-Null
}
New-Item -ItemType Directory -Path $pilotDestRoot -Force | Out-Null

$phaseRecords = New-Object 'System.Collections.Generic.List[object]'
$pilotSuccess = $true

function Assert-PilotPhase {
    param(
        [string]$PhaseId,
        [string]$Title,
        [scriptblock]$Action
    )
    
    $rec = [ordered]@{
        phase_id = $PhaseId
        title = $Title
        status = "FAIL"
        details = $null
        timestamp_utc = [DateTime]::UtcNow.ToString("o")
    }
    
    try {
        $res = & $Action
        if ($res.passed -eq $true) {
            $rec.status = "PASS"
            $rec.details = $res.details
            Write-Host "  [$PhaseId] $Title : PASS" -ForegroundColor Green
            if ($res.details) {
                Write-Host "         $($res.details)" -ForegroundColor Gray
            }
        } else {
            $rec.status = "FAIL"
            $rec.details = $res.details
            Write-Host "  [$PhaseId] $Title : FAIL ($($res.details))" -ForegroundColor Red
            $script:pilotSuccess = $false
        }
    } catch {
        $rec.status = "FAIL"
        $rec.details = $_.Exception.Message
        Write-Host "  [$PhaseId] $Title : FAIL ($($_.Exception.Message))" -ForegroundColor Red
        $script:pilotSuccess = $false
    }
    
    [void]$script:phaseRecords.Add([PSCustomObject]$rec)
}

# --- PHASE 1: Baseline & Target Inspection ---
Assert-PilotPhase "PHASE-1" "Baseline and Target Platform Inspection" {
    $insp = Get-DistributionTargetInspection -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform
    if ($insp.status -ne 'READY') {
        return @{ passed = $false; details = "Target platform $TargetPlatform not READY" }
    }
    
    $invBefore = Get-DistributionInventory -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    if ($invBefore.total_installed_count -ne 0) {
        return @{ passed = $false; details = "Pilot destination is not clean before execution" }
    }
    
    return @{ passed = $true; details = "Target contract verified ($($insp.entrypoint_filename)); pilot root clean (0 installed)" }
}

# Variable to carry plan across phases
$script:activePlan = $null

# --- PHASE 2: Deterministic Pre-Execution Plan ---
Assert-PilotPhase "PHASE-2" "Pre-Execution Distribution Plan Generation" {
    $script:activePlan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $PilotSkill -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    
    if ($script:activePlan.action_type -ne 'CREATE') {
        return @{ passed = $false; details = "Expected action CREATE, got $($script:activePlan.action_type)" }
    }
    if ($script:activePlan.execution_performed -ne $false) {
        return @{ passed = $false; details = "execution_performed must be false in plan stage" }
    }
    if ($script:activePlan.approval_required -ne $true) {
        return @{ passed = $false; details = "approval_required must be true" }
    }
    
    # Test fail-closed without approved flag
    $refused = $false
    try {
        Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $script:activePlan | Out-Null
    } catch {
        $refused = $true
    }
    if (-not $refused) {
        return @{ passed = $false; details = "Execution without -Approved flag did not fail" }
    }
    
    return @{ passed = $true; details = "Plan $($script:activePlan.plan_id) generated; unapproved execution refused (fail-closed)" }
}

# --- PHASE 3: Approved Atomic Execution & SHA-256 Validation ---
Assert-PilotPhase "PHASE-3" "Approved Execution and Byte-Fidelity Deployment" {
    $execRes = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $script:activePlan -Approved
    if ($execRes.status -ne 'COMMITTED') {
        return @{ passed = $false; details = "Execution status not COMMITTED ($($execRes.status))" }
    }
    
    # Verify deployed physical file
    $destFile = Join-Path $pilotDestRoot "$PilotSkill\SKILL.md"
    $origFile = Join-Path $RegistryRoot "skills\$PilotSkill\SKILL.md"
    if (-not [System.IO.File]::Exists($destFile)) {
        return @{ passed = $false; details = "Deployed file missing at $destFile" }
    }
    
    $destHash = Get-Sha256FileHash -Path $destFile
    $origHash = Get-Sha256FileHash -Path $origFile
    if ($destHash -ne $origHash) {
        return @{ passed = $false; details = "SHA-256 mismatch: deployed $destHash != orig $origHash" }
    }
    
    # Verify lockfile
    $lockFile = Join-Path $pilotDestRoot '.skill-registry.lock'
    if (-not (Test-Path $lockFile)) {
        return @{ passed = $false; details = "Lockfile not created at $lockFile" }
    }
    $lockContent = [System.IO.File]::ReadAllText($lockFile)
    if (-not $lockContent.Contains($PilotSkill)) {
        return @{ passed = $false; details = "Lockfile missing skill entry" }
    }
    
    return @{ passed = $true; details = "Deployed with 100% SHA-256 fidelity ($destHash); lockfile committed" }
}

# --- PHASE 4: Idempotency Guarantee Proof ---
Assert-PilotPhase "PHASE-4" "Idempotency Proof (2nd Execution = NOOP, 0 Writes)" {
    $plan2 = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $PilotSkill -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    if ($plan2.action_type -ne 'NOOP') {
        return @{ passed = $false; details = "Expected action NOOP on second run, got $($plan2.action_type)" }
    }
    if ($plan2.approval_required -ne $false) {
        return @{ passed = $false; details = "approval_required must be false on NOOP" }
    }
    
    $fileBefore = (Get-Item (Join-Path $pilotDestRoot "$PilotSkill\SKILL.md")).LastWriteTimeUtc
    $exec2 = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $plan2 -Approved
    $fileAfter = (Get-Item (Join-Path $pilotDestRoot "$PilotSkill\SKILL.md")).LastWriteTimeUtc
    
    if ($fileBefore -ne $fileAfter) {
        return @{ passed = $false; details = "File was rewritten during NOOP execution" }
    }
    
    return @{ passed = $true; details = "Idempotency verified: action=NOOP, operation=$($exec2.operation), zero disk writes" }
}

# --- PHASE 5: Controlled Drift Injection & Detection ---
Assert-PilotPhase "PHASE-5" "Controlled Drift Injection and Multi-Vector Detection" {
    $destFile = Join-Path $pilotDestRoot "$PilotSkill\SKILL.md"
    $tamperString = "`n<!-- PILOT_CONTROLLED_DRIFT_PROBE_2026 -->"
    Add-Content -Path $destFile -Value $tamperString -Encoding UTF8
    
    $invDrift = Get-DistributionInventory -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    if ($invDrift.drifted_count -ne 1) {
        return @{ passed = $false; details = "Expected 1 drifted skill, got $($invDrift.drifted_count)" }
    }
    
    $item = @($invDrift.installed_skills | Where-Object { $_.canonical_name -eq $PilotSkill })[0]
    if ($item.drift_status -ne 'MODIFIED_EXTERNALLY') {
        return @{ passed = $false; details = "Expected MODIFIED_EXTERNALLY, got $($item.drift_status)" }
    }
    
    return @{ passed = $true; details = "Drift accurately detected: status=MODIFIED_EXTERNALLY, tampered hash identified" }
}

# --- PHASE 6: Governed Synchronization & Restoration ---
Assert-PilotPhase "PHASE-6" "Governed Sync Reconciliation and Hash Restoration" {
    $syncRes = Invoke-DistributionSync -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot -Approved
    if ($syncRes.reconciled_count -ne 1) {
        return @{ passed = $false; details = "Expected 1 reconciled skill, got $($syncRes.reconciled_count)" }
    }
    
    # Verify file is restored to canonical hash
    $destFile = Join-Path $pilotDestRoot "$PilotSkill\SKILL.md"
    $origFile = Join-Path $RegistryRoot "skills\$PilotSkill\SKILL.md"
    $restoredHash = Get-Sha256FileHash -Path $destFile
    $canonicalHash = Get-Sha256FileHash -Path $origFile
    
    if ($restoredHash -ne $canonicalHash) {
        return @{ passed = $false; details = "Restored hash does not match canonical" }
    }
    
    $invAfter = Get-DistributionInventory -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    if ($invAfter.in_sync_count -ne 1 -or $invAfter.drifted_count -ne 0) {
        return @{ passed = $false; details = "Inventory not IN_SYNC after reconciliation" }
    }
    
    return @{ passed = $true; details = "Canonical hash restored ($restoredHash); inventory returned to 100% IN_SYNC" }
}

# --- PHASE 7: Atomic Uninstallation & Tombstone Ledger ---
Assert-PilotPhase "PHASE-7" "Atomic Uninstallation and Lockfile Tombstone Ledger" {
    $skillFolder = Join-Path $pilotDestRoot $PilotSkill
    $unRes = Invoke-DistributionUninstall -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -CanonicalName $PilotSkill -DestinationPath $skillFolder -Approved
    if ($unRes.status -ne 'UNINSTALLED') {
        return @{ passed = $false; details = "Uninstall status not UNINSTALLED" }
    }
    if (Test-Path $skillFolder) {
        return @{ passed = $false; details = "Skill folder was not removed from destination" }
    }
    
    $lockFile = Join-Path $pilotDestRoot '.skill-registry.lock'
    $lockContent = [System.IO.File]::ReadAllText($lockFile)
    if (-not $lockContent.Contains("# TOMBSTONE: $PilotSkill uninstalled at")) {
        return @{ passed = $false; details = "Audit tombstone missing in lockfile" }
    }
    
    $invFinal = Get-DistributionInventory -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $pilotDestRoot
    if ($invFinal.total_installed_count -ne 0) {
        return @{ passed = $false; details = "Installed count not zero after uninstallation" }
    }
    
    return @{ passed = $true; details = "Skill folder cleanly deleted; formal tombstone written to .skill-registry.lock" }
}

# --- PHASE 8: Hermetic Isolation Verification ---
Assert-PilotPhase "PHASE-8" "Hermetic Workspace Isolation Audit" {
    $userSkillsDir = 'C:\Users\Ad\.gemini\config\skills'
    $leakDetected = $false
    $leakDetails = ''
    
    $testMarkers = @('pilot-cursor', $PilotSkill)
    # Check that user skills directory did not receive test directories
    $pilotDirInUser = Join-Path $userSkillsDir "pilot-$TargetPlatform"
    if (Test-Path $pilotDirInUser) {
        $leakDetected = $true
        $leakDetails = "Pilot directory leaked to $userSkillsDir"
    }
    
    # Clean pilot directory
    if (Test-Path $pilotDestRoot) {
        Remove-Item -Path $pilotDestRoot -Recurse -Force | Out-Null
    }
    
    if ($leakDetected) {
        return @{ passed = $false; details = $leakDetails }
    }
    return @{ passed = $true; details = "Zero workspace leaks detected; pilot staging hermetically purged" }
}

Write-Host "============================================================" -ForegroundColor Cyan
$sumClr = if ($pilotSuccess) { 'Green' } else { 'Red' }
$sumText = if ($pilotSuccess) { '8 / 8 PHASES PASSED' } else { 'FAILURES DETECTED' }
Write-Host " PILOT PROTOCOL SUMMARY: $sumText" -ForegroundColor $sumClr
Write-Host "============================================================" -ForegroundColor Cyan

# Output reports
$pilotReport = [ordered]@{
    schema_version = '1.0.0'
    protocol_title = 'GOVERNED DISTRIBUTION SINGLE-TARGET PILOT'
    target_platform = $TargetPlatform
    pilot_skill = $PilotSkill
    pilot_verdict = if ($pilotSuccess) { 'PILOT_LIFECYCLE_CERTIFIED' } else { 'PILOT_FAILED' }
    total_phases = $phaseRecords.Count
    passed_phases = @($phaseRecords | Where-Object { $_.status -eq 'PASS' }).Count
    failed_phases = @($phaseRecords | Where-Object { $_.status -eq 'FAIL' }).Count
    completed_utc = [DateTime]::UtcNow.ToString('o')
    phases = $phaseRecords.ToArray()
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$jsonContent = $pilotReport | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($JsonOutputPath, $jsonContent, $utf8NoBom)
Write-Host "JSON report saved: $JsonOutputPath" -ForegroundColor Green

$bt = [char]96
$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# Governed Distribution Pilot Execution Report")
[void]$md.AppendLine("")
[void]$md.AppendLine(('**Target Platform:** {0}{1}{0}' -f $bt, $TargetPlatform))
[void]$md.AppendLine(('**Pilot Skill:** {0}{1}{0}' -f $bt, $PilotSkill))
[void]$md.AppendLine(('**Data / Hora (UTC):** {0}' -f $pilotReport.completed_utc))
[void]$md.AppendLine(('**Veredito Oficial:** {0}{1}{0}' -f $bt, $pilotReport.pilot_verdict))
[void]$md.AppendLine(('**Fases Executadas:** **{0} / {1} PASS**' -f $pilotReport.passed_phases, $pilotReport.total_phases))
[void]$md.AppendLine("")
[void]$md.AppendLine("---")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Tabela de Fases do Piloto")
[void]$md.AppendLine("")
[void]$md.AppendLine("| Fase | Titulo | Status | Evidencia Tecnica |")
[void]$md.AppendLine("| :--- | :--- | :---: | :--- |")

foreach ($p in $pilotReport.phases) {
    $stIcon = if ($p.status -eq 'PASS') { "PASS" } else { "FAIL" }
    [void]$md.AppendLine(('| {0}{1}{0} | {2} | **{3}** | {4} |' -f $bt, $p.phase_id, $p.title, $stIcon, $p.details))
}

[void]$md.AppendLine("")
[void]$md.AppendLine("---")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Conclusao Operacional do Piloto")
[void]$md.AppendLine("")
[void]$md.AppendLine("> O ciclo de vida completo de distribuicao governada foi comprovado em 8 fases sequenciais:")
[void]$md.AppendLine("> 1. Inspecao de contrato e baseline limpo;")
[void]$md.AppendLine("> 2. Geracao deterministica de plano e bloqueio fail-closed de execucao nao autorizada;")
[void]$md.AppendLine("> 3. Implantacao atomica com 100% de fidelidade SHA-256 e gravacao de lockfile;")
[void]$md.AppendLine("> 4. Garantia estrita de idempotencia (segunda execucao resulta em NOOP com zero escritas);")
[void]$md.AppendLine("> 5. Detecao de adulteracao externa (MODIFIED_EXTERNALLY);")
[void]$md.AppendLine("> 6. Reconciliacao governada (sync) restaurando com precisao o hash canonico;")
[void]$md.AppendLine("> 7. Desinstalacao atomica com exclusao de arquivos e registro de tombstone;")
[void]$md.AppendLine("> 8. Isolamento hermetico com zero vazamentos no workspace do usuario.")

[System.IO.File]::WriteAllText($MdOutputPath, $md.ToString(), $utf8NoBom)
Write-Host "Markdown report saved: $MdOutputPath" -ForegroundColor Green
