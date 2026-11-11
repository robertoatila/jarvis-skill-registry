$desktopDir = [System.Environment]::GetFolderPath('Desktop')
$oldShortcut = Join-Path $desktopDir "J.A.R.V.I.S. (Host Silencioso).lnk"
if (Test-Path $oldShortcut) {
    Remove-Item -LiteralPath $oldShortcut -Force -ErrorAction SilentlyContinue
}

$shortcutPath = Join-Path $desktopDir "J.A.R.V.I.S..lnk"
$icoPath = "E:\.skill-registry\ui\assets\jarvis_golden.ico"
if (-not (Test-Path $icoPath)) {
    $icoPath = "E:\.skill-registry\ui\assets\jarvis.ico"
}
$vbsLauncher = "E:\.skill-registry\tooling\scripts\iniciar_jarvis_silencioso.vbs"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$vbsLauncher`""
$shortcut.WorkingDirectory = "E:\.skill-registry"
$shortcut.Description = "J.A.R.V.I.S. Sovereign Neural Core (Execucao Silenciosa em Segundo Plano)"
$shortcut.IconLocation = "$icoPath, 0"
$shortcut.Save()

# Force Windows Explorer to refresh Desktop icon cache immediately
$code = @'
using System;
using System.Runtime.InteropServices;
public class IconCacheRefresh {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
'@
try {
    Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue
    [IconCacheRefresh]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
} catch {}
Start-Process -FilePath "ie4uinit.exe" -ArgumentList "-show" -WindowStyle Hidden -ErrorAction SilentlyContinue

Write-Host "Atalho atualizado com novo icone dourado: $shortcutPath"
