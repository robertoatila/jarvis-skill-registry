$desktopDir = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopDir "J.A.R.V.I.S..lnk"
$icoPath = "E:\.skill-registry\ui\assets\jarvis.ico"
$vbsLauncher = "E:\.skill-registry\tooling\Launch-Jarvis.vbs"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$vbsLauncher`""
$shortcut.WorkingDirectory = "E:\.skill-registry\tooling"
$shortcut.Description = "J.A.R.V.I.S. Cognitive Command Hub & Sovereign Arsenal"
if (Test-Path $icoPath) {
    $shortcut.IconLocation = "$icoPath, 0"
}
$shortcut.Save()

Write-Host "Desktop shortcut configured with zero-flicker launcher: $shortcutPath"
Write-Host "Target: wscript.exe `"$vbsLauncher`""
Write-Host "Icon set to: $icoPath"
