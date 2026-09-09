# Skill Registry — Layer 4 Distribution Engine
# Implements governed multi-target distribution, pre-execution planning, idempotency, drift detection, and uninstallation.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256FileHash {
    param([string]$Path)
    if (-not [System.IO.File]::Exists($Path)) {
        throw "File not found for hashing: $Path"
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $hashBytes = $sha.ComputeHash($stream)
        return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

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

function Get-DistributionTargetInspection {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$TargetPlatform
    )
    
    $layoutsFile = Join-Path $RegistryRoot 'schemas\target-layouts.json'
    if (-not [System.IO.File]::Exists($layoutsFile)) {
        throw "Target layouts specification missing: $layoutsFile"
    }
    $layouts = [System.IO.File]::ReadAllText($layoutsFile) | ConvertFrom-Json
    
    if (-not $layouts.targets.PSObject.Properties.Item($TargetPlatform)) {
        throw "Unsupported target platform: $TargetPlatform"
    }
    $targetConfig = $layouts.targets.PSObject.Properties.Item($TargetPlatform).Value
    
    return [PSCustomObject]@{
        platform_id = $TargetPlatform
        entrypoint_filename = $targetConfig.entrypoint_filename
        supporting_subdirectories = $targetConfig.supporting_subdirectories
        collision_policy = $targetConfig.collision_policy
        atomic_write_strategy = $targetConfig.atomic_write_strategy
        global_path_template = $targetConfig.global_skills_path_template
        workspace_path_template = $targetConfig.workspace_skills_path_template
        lockfile_template = $targetConfig.lockfile_path_template
        status = 'READY'
    }
}

function Get-DistributionPlan {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$ResourceId = $null,
        [string]$CanonicalName = $null,
        [string]$TargetPlatform,
        [string]$DestinationRoot = $null,
        [string]$QuarantineStatus = $null
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $planId = "dplan-$nowUtc-$randomHex"
    
    # 1. Resolve Resource
    $resIndex = Join-Path $RegistryRoot 'index\resources.jsonl'
    $res = $null
    if ([System.IO.File]::Exists($resIndex)) {
        $lines = [System.IO.File]::ReadAllLines($resIndex)
        foreach ($l in $lines) {
            if ([string]::IsNullOrWhiteSpace($l)) { continue }
            $obj = $l | ConvertFrom-Json
            if ($obj.PSObject.Properties.Item('index_type')) { continue }
            
            $objResId = if ($obj.PSObject.Properties.Item('resource_id')) { $obj.resource_id } else { $null }
            $objName = if ($obj.PSObject.Properties.Item('canonical_name')) { $obj.canonical_name } else { $null }
            
            if ($ResourceId -and $objResId -and $objResId -eq $ResourceId) { $res = $obj; break }
            if ($CanonicalName -and $objName -and $objName -eq $CanonicalName) { $res = $obj; break }
        }
    }
    
    if ($null -eq $res) {
        # Fallback synthetic lookup for standalone testing
        $targetName = if (-not [string]::IsNullOrEmpty($CanonicalName)) { $CanonicalName } else { "synthetic-skill" }
        $targetResId = if (-not [string]::IsNullOrEmpty($ResourceId)) { $ResourceId } else { "sres-v1-sha256:" + (Get-Sha256TextHash -Text $targetName) }
        $res = [PSCustomObject]@{
            resource_id = $targetResId
            canonical_name = $targetName
            quarantine_status = if ($QuarantineStatus) { $QuarantineStatus } else { "CLEAN" }
        }
    }
    
    $isBlocked = $false
    if ($QuarantineStatus -in @('QUARANTINED', 'BLOCKED')) {
        $isBlocked = $true
    } elseif ($null -ne $res.PSObject.Properties.Item('quarantine_status') -and $res.quarantine_status -in @('QUARANTINED', 'BLOCKED')) {
        $isBlocked = $true
    } elseif ($null -ne $res.PSObject.Properties.Item('lifecycle_state') -and $res.lifecycle_state -notin @('ACTIVE', 'SYNTHETIC')) {
        $isBlocked = $true
    } elseif ($null -ne $res.PSObject.Properties.Item('trust_level') -and $res.trust_level -in @('UNTRUSTED', 'BLOCKED', 'QUARANTINED')) {
        $isBlocked = $true
    }
    
    # 2. Check Quarantine
    if ($isBlocked) {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            plan_id = $planId
            resource_id = $res.resource_id
            canonical_name = $res.canonical_name
            target_platform = $TargetPlatform
            target_destination_path = ""
            action_type = "QUARANTINE_BLOCKED"
            expected_content_hash = "0000000000000000000000000000000000000000000000000000000000000000"
            files_plan = @()
            collision_status = "CONFLICT"
            quarantine_status = "QUARANTINED"
            approval_required = $false
            execution_performed = $false
            created_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
    
    # 3. Destination Path Resolution
    $inspection = Get-DistributionTargetInspection -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform
    $destPath = if ($DestinationRoot) {
        Join-Path $DestinationRoot $res.canonical_name
    } else {
        Join-Path $RegistryRoot ("staging\targets\" + $TargetPlatform + "\" + $res.canonical_name)
    }
    
    # 4. Compute Files Plan & Hashes
    $expectedFiles = New-Object 'System.Collections.Generic.List[object]'
    $entryFile = $inspection.entrypoint_filename
    
    $sourceSkillDir = Join-Path $RegistryRoot ("skills\" + $res.canonical_name)
    $hasRealSource = [System.IO.Directory]::Exists($sourceSkillDir)
    
    if ($hasRealSource) {
        $realFiles = @(Get-ChildItem -Path $sourceSkillDir -Recurse -File)
        foreach ($rf in $realFiles) {
            $rel = $rf.FullName.Substring($sourceSkillDir.Length).TrimStart('\', '/').Replace('\', '/')
            $targetRel = if ($rel -eq 'SKILL.md' -and $entryFile -ne 'SKILL.md') { $entryFile } else { $rel }
            $fHash = Get-Sha256FileHash -Path $rf.FullName
            [void]$expectedFiles.Add([PSCustomObject]@{
                relative_path = $targetRel
                action = "CREATE"
                sha256 = $fHash
                size_bytes = $rf.Length
            })
        }
    } else {
        $contentMock = "# Skill: $($res.canonical_name)`n`nAutomated instruction for $TargetPlatform.`n"
        $entryHash = Get-Sha256TextHash -Text $contentMock
        [void]$expectedFiles.Add([PSCustomObject]@{
            relative_path = $entryFile
            action = "CREATE"
            sha256 = $entryHash
            size_bytes = $contentMock.Length
        })
    }
    
    # Sort files by relative_path ordinally for deterministic preimage
    $sortedFiles = @($expectedFiles | Sort-Object -Property relative_path)
    $preimageParts = New-Object 'System.Collections.Generic.List[string]'
    [void]$preimageParts.Add("dist-v1")
    foreach ($sf in $sortedFiles) {
        [void]$preimageParts.Add("$($sf.relative_path):$($sf.sha256)")
    }
    $preimage = $preimageParts -join '|'
    $expectedHash = Get-Sha256TextHash -Text $preimage
    
    # 5. Check Destination for Idempotency
    $actionType = "CREATE"
    $collisionStatus = "NONE"
    
    if ([System.IO.Directory]::Exists($destPath)) {
        $allMatch = $true
        $hasAnyFile = $false
        foreach ($ef in $expectedFiles) {
            $destFilePath = Join-Path $destPath $ef.relative_path
            if ([System.IO.File]::Exists($destFilePath)) {
                $hasAnyFile = $true
                $currHash = Get-Sha256FileHash -Path $destFilePath
                if ($currHash -eq $ef.sha256) {
                    $ef.action = "NOOP"
                } else {
                    $ef.action = "OVERWRITE"
                    $allMatch = $false
                }
            } else {
                $ef.action = "CREATE"
                $allMatch = $false
            }
        }
        
        if ($hasAnyFile -and $allMatch) {
            $actionType = "NOOP"
            $collisionStatus = "NONE"
        } elseif ($hasAnyFile) {
            $actionType = "UPDATE"
            $collisionStatus = "SAFE_OVERWRITE"
        }
    }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        plan_id = $planId
        resource_id = $res.resource_id
        canonical_name = $res.canonical_name
        target_platform = $TargetPlatform
        target_destination_path = $destPath
        action_type = $actionType
        expected_content_hash = $expectedHash
        files_plan = $expectedFiles.ToArray()
        collision_status = $collisionStatus
        quarantine_status = "CLEAN"
        approval_required = ($actionType -ne "NOOP")
        execution_performed = $false
        created_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Invoke-StagedCompilation {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [object]$Plan
    )
    
    $planId = $Plan.plan_id
    $canonicalName = $Plan.canonical_name
    $targetPlatform = $Plan.target_platform
    $filesPlan = $Plan.files_plan
    
    $stagingDir = Join-Path $RegistryRoot ("staging\distribution\" + $planId)
    if (-not (Test-Path $stagingDir)) {
        New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
    }
    
    $sourceSkillDir = Join-Path $RegistryRoot ("skills\" + $canonicalName)
    $hasRealSource = [System.IO.Directory]::Exists($sourceSkillDir)
    
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    foreach ($f in $filesPlan) {
        $targetFile = Join-Path $stagingDir $f.relative_path
        $parent = [System.IO.Path]::GetDirectoryName($targetFile)
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        
        if ($hasRealSource) {
            $sourceFile = Join-Path $sourceSkillDir $f.relative_path
            if (-not [System.IO.File]::Exists($sourceFile) -and $f.relative_path -ne 'SKILL.md') {
                $skillMd = Join-Path $sourceSkillDir 'SKILL.md'
                if ([System.IO.File]::Exists($skillMd)) { $sourceFile = $skillMd }
            }
            if ([System.IO.File]::Exists($sourceFile)) {
                Copy-Item -Path $sourceFile -Destination $targetFile -Force | Out-Null
            } else {
                $content = "# Skill: $($canonicalName)`n`nAutomated instruction for $($targetPlatform).`n"
                [System.IO.File]::WriteAllText($targetFile, $content, $utf8NoBom)
            }
        } else {
            $content = "# Skill: $($canonicalName)`n`nAutomated instruction for $($targetPlatform).`n"
            [System.IO.File]::WriteAllText($targetFile, $content, $utf8NoBom)
        }
    }
    
    return [PSCustomObject]@{
        plan_id = $planId
        staging_dir = $stagingDir
        staged_files_count = $filesPlan.Count
        status = 'COMPILED'
    }
}

function Test-StagedArtifactValidation {
    param(
        [string]$StagingDir
    )
    
    if (-not (Test-Path $StagingDir)) {
        return @{ passed = $false; error = "Staging directory does not exist: $StagingDir" }
    }
    
    $files = @(Get-ChildItem -Path $StagingDir -Recurse -File)
    foreach ($f in $files) {
        if ($f.Extension -in @('.exe', '.dll', '.bat', '.cmd', '.vbs', '.so')) {
            return @{ passed = $false; error = "Dangerous binary extension found in staging: $($f.Name)" }
        }
    }
    
    return @{ passed = $true; files_validated = $files.Count; error = $null }
}

function Invoke-DistributionExecution {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [object]$Plan,
        [switch]$Approved
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    
    # Check if Plan is a Batch Plan
    if ($null -ne $Plan.PSObject.Properties['batch_plan_id']) {
        if (-not $Approved) {
            throw "Explicit approval required to execute batch distribution plan $($Plan.batch_plan_id)."
        }
        $executedPlans = New-Object 'System.Collections.Generic.List[object]'
        $execSuccess = 0
        $execNoop = 0
        $execBlocked = 0
        
        foreach ($sp in $Plan.skill_plans) {
            if ($sp.action_type -eq 'QUARANTINE_BLOCKED') {
                $execBlocked++
                continue
            }
            $res = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $sp -Approved:$Approved
            if ($res.operation -eq 'SYNC' -or $sp.action_type -eq 'NOOP') { $execNoop++ } else { $execSuccess++ }
            [void]$executedPlans.Add($res)
        }
        
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            batch_execution_id = "dexec-batch-$nowUtc-$randomHex"
            batch_plan_id = $Plan.batch_plan_id
            target_platform = $Plan.target_platform
            total_executed = $executedPlans.Count
            successful_installs = $execSuccess
            noop_skips = $execNoop
            quarantine_blocked = $execBlocked
            executions = $executedPlans.ToArray()
            completed_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
    
    $journalId = "djour-$nowUtc-$randomHex"
    $planId = $Plan.plan_id
    $canonicalName = $Plan.canonical_name
    $targetPlatform = $Plan.target_platform
    $actionType = $Plan.action_type
    $expectedHash = $Plan.expected_content_hash
    $destPath = $Plan.target_destination_path
    $approvalRequired = $Plan.approval_required
    
    if ($actionType -eq 'QUARANTINE_BLOCKED') {
        throw "Refusing to execute distribution: Skill is quarantined."
    }
    
    if (-not $Approved -and $approvalRequired) {
        throw "Explicit approval required to execute distribution plan $($planId)."
    }
    
    $destParent = [System.IO.Path]::GetDirectoryName($destPath)
    $lockfilePath = if (-not [string]::IsNullOrEmpty($destParent)) { Join-Path $destParent '.skill-registry.lock' } else { Join-Path $RegistryRoot '.skill-registry.lock' }
    
    # Idempotent NOOP handler
    if ($actionType -eq 'NOOP') {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            journal_id = $journalId
            plan_id = $planId
            target_platform = $targetPlatform
            operation = "SYNC"
            status = "COMMITTED"
            destination_path = $destPath
            lockfile_path = $lockfilePath
            pre_backup_path = $null
            deployed_content_hash = $expectedHash
            deployed_files = $Plan.files_plan
            user_approval_granted = [bool]$Approved
            timestamp_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
    
    # 1. Compile to Staging
    $compileRes = Invoke-StagedCompilation -RegistryRoot $RegistryRoot -Plan $Plan
    
    # 2. Validate Staged
    $validation = Test-StagedArtifactValidation -StagingDir $compileRes.staging_dir
    if (-not $validation.passed) {
        Remove-Item -Path $compileRes.staging_dir -Recurse -Force | Out-Null
        throw "Staging validation failed: $($validation.error)"
    }
    
    # 3. Create Backup if modifying existing
    $backupPath = $null
    if ([System.IO.Directory]::Exists($destPath)) {
        $backupDir = Join-Path $RegistryRoot 'backups\distribution'
        if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir -Force | Out-Null }
        $backupPath = Join-Path $backupDir "$($canonicalName)-$nowUtc"
        Copy-Item -Path $destPath -Destination $backupPath -Recurse -Force | Out-Null
    }
    
    # 4. Atomic Install / Replace
    if (-not (Test-Path $destPath)) {
        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
    }
    
    $deployedFiles = New-Object 'System.Collections.Generic.List[object]'
    $stagedFiles = @(Get-ChildItem -Path $compileRes.staging_dir -Recurse -File)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    foreach ($sf in $stagedFiles) {
        $rel = $sf.FullName.Substring($compileRes.staging_dir.Length).TrimStart('\', '/').Replace('\', '/')
        $targetFile = Join-Path $destPath $rel
        $parentDir = [System.IO.Path]::GetDirectoryName($targetFile)
        if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir -Force | Out-Null }
        Copy-Item -Path $sf.FullName -Destination $targetFile -Force | Out-Null
        
        [void]$deployedFiles.Add([PSCustomObject]@{
            relative_path = $rel
            sha256 = (Get-Sha256FileHash -Path $targetFile)
            size_bytes = (Get-Item $targetFile).Length
        })
    }
    
    # 5. Clean staging
    Remove-Item -Path $compileRes.staging_dir -Recurse -Force | Out-Null
    
    # 6. Commit Lockfile
    $lockEntry = [ordered]@{
        resource_id = $Plan.resource_id
        canonical_name = $canonicalName
        target_platform = $targetPlatform
        content_hash = $expectedHash
        installed_utc = [DateTime]::UtcNow.ToString("o")
    }
    $lockJson = ($lockEntry | ConvertTo-Json -Compress) + "`n"
    [System.IO.File]::AppendAllText($lockfilePath, $lockJson, $utf8NoBom)
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        journal_id = $journalId
        plan_id = $planId
        target_platform = $targetPlatform
        operation = "INSTALL"
        status = "COMMITTED"
        destination_path = $destPath
        lockfile_path = $lockfilePath
        pre_backup_path = $backupPath
        deployed_content_hash = $expectedHash
        deployed_files = $deployedFiles.ToArray()
        user_approval_granted = [bool]$Approved
        timestamp_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Test-DistributionDrift {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$TargetPlatform,
        [string]$DestinationPath,
        [string]$ExpectedContentHash
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $assessmentId = "ddrift-$nowUtc-$randomHex"
    
    if (-not [System.IO.Directory]::Exists($DestinationPath)) {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            assessment_id = $assessmentId
            target_platform = $TargetPlatform
            destination_path = $DestinationPath
            expected_content_hash = $ExpectedContentHash
            actual_content_hash = $null
            drift_status = "MISSING_DESTINATION"
            tampered_files_count = 0
            missing_files_count = 1
            untracked_files_count = 0
            reconciliation_action = "PROPOSE_REINSTALL"
            verified_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
    
    $files = @(Get-ChildItem -Path $DestinationPath -Recurse -File)
    if ($files.Count -eq 0) {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            assessment_id = $assessmentId
            target_platform = $TargetPlatform
            destination_path = $DestinationPath
            expected_content_hash = $ExpectedContentHash
            actual_content_hash = $null
            drift_status = "CORRUPTED"
            tampered_files_count = 0
            missing_files_count = 1
            untracked_files_count = 0
            reconciliation_action = "PROPOSE_REINSTALL"
            verified_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
    
    # Calculate actual hash from all files in destination sorted ordinally
    $sortedFiles = @($files | Sort-Object -Property FullName)
    $preimageParts = New-Object 'System.Collections.Generic.List[string]'
    [void]$preimageParts.Add("dist-v1")
    foreach ($f in $sortedFiles) {
        $fHash = Get-Sha256FileHash -Path $f.FullName
        $rel = $f.FullName.Substring($DestinationPath.Length).TrimStart('\', '/').Replace('\', '/')
        [void]$preimageParts.Add($rel + ':' + $fHash)
    }
    $actualHash = Get-Sha256TextHash -Text ($preimageParts -join '|')
    
    if ($actualHash -eq $ExpectedContentHash) {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            assessment_id = $assessmentId
            target_platform = $TargetPlatform
            destination_path = $DestinationPath
            expected_content_hash = $ExpectedContentHash
            actual_content_hash = $actualHash
            drift_status = "IN_SYNC"
            tampered_files_count = 0
            missing_files_count = 0
            untracked_files_count = 0
            reconciliation_action = "NONE"
            verified_utc = [DateTime]::UtcNow.ToString("o")
        }
    } else {
        return [PSCustomObject]@{
            schema_version = "1.0.0"
            assessment_id = $assessmentId
            target_platform = $TargetPlatform
            destination_path = $DestinationPath
            expected_content_hash = $ExpectedContentHash
            actual_content_hash = $actualHash
            drift_status = "MODIFIED_EXTERNALLY"
            tampered_files_count = 1
            missing_files_count = 0
            untracked_files_count = 0
            reconciliation_action = "PROPOSE_SYNC_UPDATE"
            verified_utc = [DateTime]::UtcNow.ToString("o")
        }
    }
}

function Invoke-DistributionUninstall {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$TargetPlatform,
        [string]$CanonicalName,
        [string]$DestinationPath,
        [switch]$Approved
    )
    
    if (-not $Approved) {
        throw "Explicit approval required to uninstall skill $CanonicalName."
    }
    
    if ([System.IO.Directory]::Exists($DestinationPath)) {
        Remove-Item -Path $DestinationPath -Recurse -Force | Out-Null
    }
    
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $destParent = [System.IO.Path]::GetDirectoryName($DestinationPath)
    $lockfilePath = if (-not [string]::IsNullOrEmpty($destParent)) { Join-Path $destParent '.skill-registry.lock' } else { Join-Path $RegistryRoot '.skill-registry.lock' }
    if ([System.IO.File]::Exists($lockfilePath)) {
        $tombstone = "# TOMBSTONE: $CanonicalName uninstalled at " + [DateTime]::UtcNow.ToString("o") + "`n"
        [System.IO.File]::AppendAllText($lockfilePath, $tombstone, $utf8NoBom)
    }
    
    return [PSCustomObject]@{
        status = 'UNINSTALLED'
        canonical_name = $CanonicalName
        target_platform = $TargetPlatform
        destination_path = $DestinationPath
        uninstalled_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Get-DistributionBatchPlan {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string[]]$CanonicalNames = @(),
        [switch]$AllActive,
        [string]$TargetPlatform,
        [string]$DestinationRoot = $null
    )
    
    $nowUtc = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $randomHex = (Get-Random -Minimum 0x10000000 -Maximum 0x7FFFFFFF).ToString("x8")
    $batchPlanId = "dplan-batch-$nowUtc-$randomHex"
    
    $targetSkills = New-Object 'System.Collections.Generic.List[string]'
    if ($AllActive) {
        $resIndex = Join-Path $RegistryRoot 'index\resources.jsonl'
        if ([System.IO.File]::Exists($resIndex)) {
            $lines = [System.IO.File]::ReadAllLines($resIndex)
            foreach ($l in $lines) {
                if ([string]::IsNullOrWhiteSpace($l)) { continue }
                $obj = $l | ConvertFrom-Json
                if ($null -ne $obj.PSObject.Properties['lifecycle_state'] -and $obj.lifecycle_state -eq 'ACTIVE') {
                    [void]$targetSkills.Add($obj.canonical_name)
                }
            }
        }
    } elseif ($CanonicalNames.Count -gt 0) {
        foreach ($cn in $CanonicalNames) {
            [void]$targetSkills.Add($cn)
        }
    } else {
        throw "Either -CanonicalNames or -AllActive must be specified for batch planning."
    }
    
    $skillPlans = New-Object 'System.Collections.Generic.List[object]'
    $createCount = 0
    $updateCount = 0
    $noopCount = 0
    $blockedCount = 0
    $totalFiles = 0
    $totalBytes = 0
    
    foreach ($name in $targetSkills) {
        $plan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $name -TargetPlatform $TargetPlatform -DestinationRoot $DestinationRoot
        [void]$skillPlans.Add($plan)
        
        switch ($plan.action_type) {
            'CREATE'             { $createCount++ }
            'UPDATE'             { $updateCount++ }
            'NOOP'               { $noopCount++ }
            'QUARANTINE_BLOCKED' { $blockedCount++ }
        }
        
        foreach ($f in $plan.files_plan) {
            $totalFiles++
            $totalBytes += $f.size_bytes
        }
    }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        batch_plan_id = $batchPlanId
        target_platform = $TargetPlatform
        destination_root = $DestinationRoot
        total_skills_requested = $targetSkills.Count
        create_count = $createCount
        update_count = $updateCount
        noop_count = $noopCount
        quarantine_blocked_count = $blockedCount
        total_files = $totalFiles
        total_bytes = $totalBytes
        executable_plans_count = ($createCount + $updateCount)
        skill_plans = $skillPlans.ToArray()
        created_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Get-DistributionInventory {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$TargetPlatform,
        [string]$DestinationRoot = $null
    )
    
    $inspection = Get-DistributionTargetInspection -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform
    $targetDir = if ($DestinationRoot) {
        $DestinationRoot
    } else {
        Join-Path $RegistryRoot ("staging\targets\" + $TargetPlatform)
    }
    
    # Load canonical resources
    $resIndex = Join-Path $RegistryRoot 'index\resources.jsonl'
    $canonicalMap = @{}
    if ([System.IO.File]::Exists($resIndex)) {
        $lines = [System.IO.File]::ReadAllLines($resIndex)
        foreach ($l in $lines) {
            if ([string]::IsNullOrWhiteSpace($l)) { continue }
            $obj = $l | ConvertFrom-Json
            if ($null -ne $obj.PSObject.Properties['canonical_name']) {
                $canonicalMap[$obj.canonical_name] = $obj
            }
        }
    }
    
    # Load quarantine tombstones
    $quarantineFile = Join-Path $RegistryRoot 'state\quarantine-link.json'
    $quarantineSet = New-Object 'System.Collections.Generic.HashSet[string]'
    if ([System.IO.File]::Exists($quarantineFile)) {
        try {
            $qObj = [System.IO.File]::ReadAllText($quarantineFile) | ConvertFrom-Json
            if ($null -ne $qObj.PSObject.Properties['quarantine_tombstones']) {
                foreach ($t in $qObj.quarantine_tombstones) {
                    if ($null -ne $t.PSObject.Properties['canonical_name']) {
                        [void]$quarantineSet.Add($t.canonical_name)
                    }
                }
            }
        } catch {}
    }
    
    $installed = New-Object 'System.Collections.Generic.List[object]'
    $inSyncCount = 0
    $driftedCount = 0
    $untrackedCount = 0
    $quarantinedCount = 0
    
    if ([System.IO.Directory]::Exists($targetDir)) {
        $subdirs = @(Get-ChildItem -Path $targetDir -Directory)
        foreach ($sd in $subdirs) {
            $sName = $sd.Name
            $resObj = if ($canonicalMap.ContainsKey($sName)) { $canonicalMap[$sName] } else { $null }
            $isActive = ($null -ne $resObj -and $null -ne $resObj.PSObject.Properties['lifecycle_state'] -and $resObj.lifecycle_state -eq 'ACTIVE')
            $isUntracked = (-not $canonicalMap.ContainsKey($sName))
            $isQuarantined = ($quarantineSet.Contains($sName) -or ($null -ne $resObj -and $null -ne $resObj.PSObject.Properties['lifecycle_state'] -and $resObj.lifecycle_state -ne 'ACTIVE'))
            
            $driftRes = $null
            $expectedHash = $null
            if ($isActive) {
                $plan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $sName -TargetPlatform $TargetPlatform -DestinationRoot $DestinationRoot
                $expectedHash = $plan.expected_content_hash
                $driftRes = Test-DistributionDrift -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationPath $sd.FullName -ExpectedContentHash $expectedHash
            }
            
            $driftStatus = if ($isUntracked) {
                $untrackedCount++
                "UNTRACKED"
            } elseif ($isQuarantined) {
                $quarantinedCount++
                "UNAUTHORIZED_CANDIDATE"
            } elseif ($driftRes.drift_status -eq 'IN_SYNC') {
                $inSyncCount++
                "IN_SYNC"
            } else {
                $driftedCount++
                $driftRes.drift_status
            }
            
            [void]$installed.Add([PSCustomObject]@{
                canonical_name = $sName
                path = $sd.FullName
                is_active = $isActive
                is_untracked = $isUntracked
                is_quarantined = $isQuarantined
                expected_hash = $expectedHash
                actual_hash = if ($driftRes) { $driftRes.actual_content_hash } else { $null }
                drift_status = $driftStatus
            })
        }
    }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        target_platform = $TargetPlatform
        target_directory = $targetDir
        total_installed_count = $installed.Count
        in_sync_count = $inSyncCount
        drifted_count = $driftedCount
        untracked_count = $untrackedCount
        quarantined_count = $quarantinedCount
        installed_skills = $installed.ToArray()
        inspected_utc = [DateTime]::UtcNow.ToString("o")
    }
}

function Invoke-DistributionSync {
    param(
        [string]$RegistryRoot = 'E:\.skill-registry',
        [string]$TargetPlatform,
        [string]$DestinationRoot = $null,
        [string]$CanonicalName = $null,
        [switch]$PruneUntracked,
        [switch]$Approved
    )
    
    if (-not $Approved) {
        throw "Explicit approval required to synchronize distribution target."
    }
    
    $inventory = Get-DistributionInventory -RegistryRoot $RegistryRoot -TargetPlatform $TargetPlatform -DestinationRoot $DestinationRoot
    $syncResults = New-Object 'System.Collections.Generic.List[object]'
    $reconciledCount = 0
    $prunedCount = 0
    
    # 1. Reconcile drifted skills and prune unauthorized/untracked
    foreach ($item in $inventory.installed_skills) {
        if (-not [string]::IsNullOrEmpty($CanonicalName) -and $item.canonical_name -ne $CanonicalName) {
            continue
        }
        
        if ($item.is_active -and $item.drift_status -in @('MODIFIED_EXTERNALLY', 'CORRUPTED', 'MISSING_DESTINATION')) {
            # Execute safe overwrite from canonical source
            $plan = Get-DistributionPlan -RegistryRoot $RegistryRoot -CanonicalName $item.canonical_name -TargetPlatform $TargetPlatform -DestinationRoot $DestinationRoot
            $exec = Invoke-DistributionExecution -RegistryRoot $RegistryRoot -Plan $plan -Approved
            $reconciledCount++
            [void]$syncResults.Add([PSCustomObject]@{
                canonical_name = $item.canonical_name
                action = "RECONCILED"
                previous_drift_status = $item.drift_status
                new_hash = $exec.deployed_content_hash
            })
        } elseif (($item.is_untracked -or $item.is_quarantined) -and $PruneUntracked) {
            Remove-Item -Path $item.path -Recurse -Force | Out-Null
            $prunedCount++
            [void]$syncResults.Add([PSCustomObject]@{
                canonical_name = $item.canonical_name
                action = "PRUNED_UNAUTHORIZED"
                previous_drift_status = $item.drift_status
                new_hash = $null
            })
        }
    }
    
    return [PSCustomObject]@{
        schema_version = "1.0.0"
        target_platform = $TargetPlatform
        target_directory = $inventory.target_directory
        reconciled_count = $reconciledCount
        pruned_count = $prunedCount
        sync_results = $syncResults.ToArray()
        synchronized_utc = [DateTime]::UtcNow.ToString("o")
    }
}

Export-ModuleMember -Function `
    Get-Sha256FileHash, `
    Get-Sha256TextHash, `
    Get-DistributionTargetInspection, `
    Get-DistributionPlan, `
    Get-DistributionBatchPlan, `
    Get-DistributionInventory, `
    Invoke-StagedCompilation, `
    Test-StagedArtifactValidation, `
    Invoke-DistributionExecution, `
    Test-DistributionDrift, `
    Invoke-DistributionSync, `
    Invoke-DistributionUninstall

