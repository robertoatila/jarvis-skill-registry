Add-Type -AssemblyName System.Drawing

$sourcePath = 'C:\Users\Ad\.gemini\antigravity-ide\brain\fe66c4d5-66b3-49e5-9e09-d35eac39d799\jarvis_icon_1788577979758.jpg'
$assetsDir = 'E:\.skill-registry\ui\assets'
if (-not (Test-Path $assetsDir)) {
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
}

$pngPath = Join-Path $assetsDir 'jarvis_core.png'
Copy-Item -Path $sourcePath -Destination $pngPath -Force

$icoPath = Join-Path $assetsDir 'jarvis.ico'
$img = [System.Drawing.Image]::FromFile($sourcePath)
$thumb = New-Object System.Drawing.Bitmap($img, 256, 256)
$hIcon = $thumb.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($hIcon)
$fileStream = New-Object System.IO.FileStream($icoPath, [System.IO.FileMode]::Create)
$icon.Save($fileStream)
$fileStream.Close()
$thumb.Dispose()
$img.Dispose()

Write-Host "Created ICO: $icoPath"
Write-Host "Created PNG: $pngPath"
