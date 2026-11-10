Add-Type -AssemblyName System.Drawing

function Generate-JarvisIcon {
    param([string]$outputPath)

    $bmp = New-Object System.Drawing.Bitmap 32, 32
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([System.Drawing.Color]::Transparent)

    $bgBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#070b12'))
    $g.FillRectangle($bgBrush, 0, 0, 32, 32)

    $cyanColor = [System.Drawing.ColorTranslator]::FromHtml('#5de0ec')
    $pen = New-Object System.Drawing.Pen $cyanColor, 2.2
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $p1 = New-Object System.Drawing.PointF 16, 3
    $p2 = New-Object System.Drawing.PointF 28, 10
    $p3 = New-Object System.Drawing.PointF 28, 22
    $p4 = New-Object System.Drawing.PointF 16, 29
    $p5 = New-Object System.Drawing.PointF 4, 22
    $p6 = New-Object System.Drawing.PointF 4, 10
    $hexPoints = [System.Drawing.PointF[]]@($p1, $p2, $p3, $p4, $p5, $p6)
    $g.DrawPolygon($pen, $hexPoints)

    $j1 = New-Object System.Drawing.PointF 10, 11
    $j2 = New-Object System.Drawing.PointF 21, 11
    $j3 = New-Object System.Drawing.PointF 21, 19
    $j4 = New-Object System.Drawing.PointF 16, 22
    $j5 = New-Object System.Drawing.PointF 11, 19
    $jPoints = [System.Drawing.PointF[]]@($j1, $j2, $j3, $j4, $j5)
    $g.DrawLines($pen, $jPoints)

    $hIcon = $bmp.GetHicon()
    $icon = [System.Drawing.Icon]::FromHandle($hIcon)
    $fs = New-Object System.IO.FileStream $outputPath, ([System.IO.FileMode]::Create)
    $icon.Save($fs)
    $fs.Close()
    $icon.Dispose()
    $bmp.Dispose()
    $g.Dispose()
    Write-Output "Generated icon at $outputPath"
}

Generate-JarvisIcon 'ui/assets/jarvis.ico'
Generate-JarvisIcon 'site/favicon.ico'
Copy-Item 'site/favicon.svg' 'ui/favicon.svg' -Force
Copy-Item 'site/favicon.svg' 'ui/assets/favicon.svg' -Force
Write-Output "Favicons successfully updated to Cobalt Titanium Cyan"
