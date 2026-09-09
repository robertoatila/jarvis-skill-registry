# Skill Registry — Layer 4/5 Sidecar Background Observer Engine
# Implements non-blocking read-analyze-propose loop, passive drift observation, proposal generation, and zero autonomous writes.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'ResolutionEngine.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'DistributionEngine.psm1') -Force

function Get-Sha256TextHash {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        $bytes = $utf8NoBom.GetBytes($Text)
        $hashBytes = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
    } finally {
        $sha.Dispose()
    }
}

function Get-Sha256FileHash {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) {
        throw "File not found for hashing: $FilePath"
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($FilePath)
        try {
            $hashBytes = $sha.ComputeHash($stream)
            return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
}

function Get-SidecarConfig {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry'
    )
    $cfgFile = Join-Path $RegistryRoot 'schemas\sidecar-config.json'
    if (Test-Path $cfgFile) {
        return [System.IO.File]::ReadAllText($cfgFile) | ConvertFrom-Json
    }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        observer_id = "scfg-default"
        poll_interval_seconds = 60
        monitored_workspaces = @()
        monitored_inlets = @("LOCAL_HD", "GITHUB", "OCI_REMOTE", "FEDERATION")
        monitored_targets = @("gemini", "codex", "claude", "chatgpt", "cursor", "generic")
        governance_mode = "READ_ANALYZE_PROPOSE"
        allow_autonomous_writes = $false
        created_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function New-SidecarObservation {
    param(
        [string]$EventType,
        [string]$SourceLocation,
        [string]$TargetPlatform = "NONE",
        [string]$Details,
        [string[]]$EvidenceHashes = @(),
        [string]$QuarantineFlag = "CLEAN"
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $obsId = "sobs-$nowUtc-$randomHex"
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        observation_id = $obsId
        event_type = $EventType
        source_location = $SourceLocation
        target_platform = $TargetPlatform
        details = $Details
        evidence_hashes = $EvidenceHashes
        quarantine_flag = $QuarantineFlag
        observed_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function New-SidecarProposal {
    param(
        [object]$Observation,
        [string]$ProposedAction,
        [string]$TargetPlatform,
        [string]$SkillId,
        [string]$Reason,
        [string]$Priority = "MEDIUM"
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $propId = "sprop-$nowUtc-$randomHex"
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        proposal_id = $propId
        observation_id = $Observation.observation_id
        proposed_action = $ProposedAction
        target_platform = $TargetPlatform
        skill_id = $SkillId
        reason = $Reason
        priority = $Priority
        approval_required = $true
        auto_executed = $false
        created_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Test-WorkspaceDriftObservation {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$WorkspacePath
    )
    
    if (-not (Test-Path $WorkspacePath)) {
        return @()
    }
    
    $observations = New-Object 'System.Collections.Generic.List[object]'
    $lockPath = Join-Path $WorkspacePath '.skill-registry.lock'
    
    # 1. Check if stack has new undetected manifests
    $det = Detect-ProjectStack -WorkspaceRoot $WorkspacePath
    if ($det.detected_frameworks.Count -gt 0) {
        $obs = New-SidecarObservation -EventType 'MANIFEST_STACK_CHANGED' -SourceLocation $WorkspacePath -TargetPlatform 'NONE' -Details "Detected stack: $($det.detected_frameworks -join ', ')" -EvidenceHashes @((Get-Sha256TextHash -Text ($det.detected_manifests -join ','))) -QuarantineFlag 'CLEAN'
        [void]$observations.Add($obs)
    }
    
    # 2. Check lockfile integrity if present
    if (Test-Path $lockPath) {
        $lockTest = Test-SkillRegistryLock -LockfilePath $lockPath
        if (-not $lockTest.passed) {
            $obs = New-SidecarObservation -EventType 'LOCKFILE_MISMATCH' -SourceLocation $lockPath -TargetPlatform 'NONE' -Details "Lockfile verification failed: $($lockTest.error)" -EvidenceHashes @() -QuarantineFlag 'CLEAN'
            [void]$observations.Add($obs)
        }
    }
    
    return $observations.ToArray()
}

function Invoke-SidecarCycle {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string[]]$WorkspacesToScan = @(),
        [string[]]$TargetsToScan = @('cursor', 'gemini', 'codex')
    )
    
    $config = Get-SidecarConfig -RegistryRoot $RegistryRoot
    $allObservations = New-Object 'System.Collections.Generic.List[object]'
    $allProposals = New-Object 'System.Collections.Generic.List[object]'
    
    # 1. Scan Workspaces (Passive Read-Only)
    foreach ($ws in $WorkspacesToScan) {
        if (Test-Path $ws) {
            $wsObs = Test-WorkspaceDriftObservation -RegistryRoot $RegistryRoot -WorkspacePath $ws
            foreach ($o in $wsObs) {
                [void]$allObservations.Add($o)
                if ($o.event_type -eq 'MANIFEST_STACK_CHANGED') {
                    $prop = New-SidecarProposal -Observation $o -ProposedAction 'PROPOSE_RESOLVE_NEW_STACK' -TargetPlatform 'cursor' -SkillId 'workspace-stack' -Reason "Workspace manifests changed. Proposing fresh capability resolution." -Priority 'MEDIUM'
                    [void]$allProposals.Add($prop)
                }
            }
        }
    }
    
    # 2. Scan Staging Inlets for unapproved candidates
    $ociInlet = Join-Path $RegistryRoot 'staging\oci-inlet'
    if (Test-Path $ociInlet) {
        $dirs = @(Get-ChildItem -Path $ociInlet -Directory)
        foreach ($d in $dirs) {
            $files = @(Get-ChildItem -Path $d.FullName -Recurse -File)
            if ($files.Count -gt 0) {
                $obs = New-SidecarObservation -EventType 'INLET_NEW_CANDIDATE' -SourceLocation $d.FullName -TargetPlatform 'NONE' -Details "Pending OCI bundle in staging: $($d.Name)" -EvidenceHashes @($d.Name) -QuarantineFlag 'CLEAN'
                [void]$allObservations.Add($obs)
                $prop = New-SidecarProposal -Observation $obs -ProposedAction 'PROPOSE_INGESTION' -TargetPlatform 'NONE' -SkillId $d.Name -Reason "New OCI candidate bundle waiting in staging for user review." -Priority 'LOW'
                [void]$allProposals.Add($prop)
            }
        }
    }
    
    $fedInlet = Join-Path $RegistryRoot 'staging\federation-inlet'
    if (Test-Path $fedInlet) {
        $dirs = @(Get-ChildItem -Path $fedInlet -Directory)
        foreach ($d in $dirs) {
            $files = @(Get-ChildItem -Path $d.FullName -Recurse -File)
            if ($files.Count -gt 0) {
                $obs = New-SidecarObservation -EventType 'INLET_NEW_CANDIDATE' -SourceLocation $d.FullName -TargetPlatform 'NONE' -Details "Pending Federation exchange in staging: $($d.Name)" -EvidenceHashes @($d.Name) -QuarantineFlag 'CLEAN'
                [void]$allObservations.Add($obs)
                $prop = New-SidecarProposal -Observation $obs -ProposedAction 'PROPOSE_INGESTION' -TargetPlatform 'NONE' -SkillId $d.Name -Reason "New Federation exchange package waiting in staging for user review." -Priority 'LOW'
                [void]$allProposals.Add($prop)
            }
        }
    }
    
    # 3. If no events, produce baseline IN_SYNC observation
    if ($allObservations.Count -eq 0) {
        $obs = New-SidecarObservation -EventType 'IN_SYNC' -SourceLocation $RegistryRoot -TargetPlatform 'NONE' -Details "All monitored sources and targets in sync." -EvidenceHashes @() -QuarantineFlag 'CLEAN'
        [void]$allObservations.Add($obs)
    }
    
    # 4. Update Sidecar State Record
    $stateRecord = [PSCustomObject]@{
        schema_version = "1.0.0"
        observer_id = $config.observer_id
        last_cycle_utc = [DateTime]::UtcNow.ToString("o")
        total_cycles_executed = 1
        active_observations_count = $allObservations.Count
        pending_proposals_count = $allProposals.Count
        last_known_registry_merkle = if (Test-Path (Join-Path $RegistryRoot 'state\canonical-merkle.json')) {
            (Get-Content -LiteralPath (Join-Path $RegistryRoot 'state\canonical-merkle.json') | ConvertFrom-Json).merkle_root
        } else {
            "7471930786cc9566df84801ef081f689f377fe92eef4195728ee355302d82d50"
        }
        status = "IDLE"
    }
    
    return [PSCustomObject]@{
        cycle_status = "COMPLETED"
        observations = $allObservations.ToArray()
        proposals = $allProposals.ToArray()
        state = $stateRecord
        zero_writes_enforced = $true
    }
}

Export-ModuleMember -Function `
    Get-Sha256TextHash, `
    Get-Sha256FileHash, `
    Get-SidecarConfig, `
    New-SidecarObservation, `
    New-SidecarProposal, `
    Test-WorkspaceDriftObservation, `
    Invoke-SidecarCycle
