Add-Type -AssemblyName System.Drawing

$width = 900
$height = 383
$out = Join-Path $PSScriptRoot "wechat-cover-ai-creator-studio.png"

$bmp = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

function New-Brush($hex) {
    return New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml($hex))
}

function New-Pen($hex, $size = 1) {
    return New-Object System.Drawing.Pen ([System.Drawing.ColorTranslator]::FromHtml($hex)), $size
}

function Draw-RoundedRect($graphics, $brush, [float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    $graphics.FillPath($brush, $path)
    $path.Dispose()
}

function Draw-RoundedRectStroke($graphics, $pen, [float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    $graphics.DrawPath($pen, $path)
    $path.Dispose()
}

$bgRect = New-Object System.Drawing.Rectangle 0, 0, $width, $height
$bgBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    $bgRect,
    [System.Drawing.ColorTranslator]::FromHtml("#101828"),
    [System.Drawing.ColorTranslator]::FromHtml("#113447"),
    18
)
$g.FillRectangle($bgBrush, $bgRect)

$overlay = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    $bgRect,
    [System.Drawing.Color]::FromArgb(70, 30, 180, 160),
    [System.Drawing.Color]::FromArgb(20, 255, 255, 255),
    0
)
$g.FillRectangle($overlay, $bgRect)

$gridPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(28, 255, 255, 255)), 1
for ($x = 0; $x -lt $width; $x += 36) { $g.DrawLine($gridPen, $x, 0, $x, $height) }
for ($y = 0; $y -lt $height; $y += 36) { $g.DrawLine($gridPen, 0, $y, $width, $y) }

$accentPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(120, 76, 211, 194)), 2
$g.DrawBezier($accentPen, 555, 40, 670, 120, 680, 245, 855, 330)
$g.DrawBezier($accentPen, 470, 330, 600, 260, 720, 355, 885, 250)

$fontTitle = New-Object System.Drawing.Font "Microsoft YaHei UI", 40, ([System.Drawing.FontStyle]::Bold)
$fontSub = New-Object System.Drawing.Font "Microsoft YaHei UI", 22, ([System.Drawing.FontStyle]::Bold)
$fontBody = New-Object System.Drawing.Font "Microsoft YaHei UI", 13, ([System.Drawing.FontStyle]::Regular)
$fontSmall = New-Object System.Drawing.Font "Microsoft YaHei UI", 10, ([System.Drawing.FontStyle]::Regular)
$fontBadge = New-Object System.Drawing.Font "Segoe UI", 11, ([System.Drawing.FontStyle]::Bold)
$fontMono = New-Object System.Drawing.Font "Consolas", 12, ([System.Drawing.FontStyle]::Regular)

$white = New-Brush "#F8FAFC"
$muted = New-Brush "#B8C7D9"
$cyan = New-Brush "#66E3D4"
$green = New-Brush "#A7F3D0"
$darkPanel = New-Brush "#162235"
$panel = New-Brush "#1B2B40"
$panel2 = New-Brush "#22334B"
$line = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(95, 148, 163, 184)), 1

Draw-RoundedRect $g (New-Brush "#1F3A4A") 48 42 130 34 17
$g.DrawString("OPEN SOURCE", $fontBadge, $green, 66, 51)

$g.DrawString("AI Creator", $fontTitle, $white, 48, 94)
$g.DrawString("Studio", $fontTitle, $cyan, 48, 145)
$g.DrawString("AI 视频创作工具开源发布", $fontSub, $white, 48, 213)
$g.DrawString("从产品信息到分镜脚本、关键帧与视频片段", $fontBody, $muted, 51, 258)
$g.DrawString("GitHub: harvey503/AI-Creator-Studio", $fontMono, $cyan, 52, 304)

Draw-RoundedRect $g (New-Brush "#0F172A") 470 50 365 275 12
Draw-RoundedRectStroke $g $line 470 50 365 275 12

Draw-RoundedRect $g $panel 492 72 320 54 8
$g.DrawString("Product Brief", $fontSmall, $muted, 512, 82)
$g.DrawString("智能拆解商品卖点与目标市场", $fontBody, $white, 512, 101)

Draw-RoundedRect $g $panel2 492 146 320 54 8
$g.DrawString("AI Strategy", $fontSmall, $muted, 512, 156)
$g.DrawString("生成合规策略、文化备注与黄金钩子", $fontBody, $white, 512, 175)

Draw-RoundedRect $g $panel 492 220 88 72 8
Draw-RoundedRect $g $panel 608 220 88 72 8
Draw-RoundedRect $g $panel 724 220 88 72 8

$thumbBrush1 = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Rectangle 504, 232, 64, 36),
    [System.Drawing.ColorTranslator]::FromHtml("#E879F9"),
    [System.Drawing.ColorTranslator]::FromHtml("#38BDF8"),
    30
)
$thumbBrush2 = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Rectangle 620, 232, 64, 36),
    [System.Drawing.ColorTranslator]::FromHtml("#34D399"),
    [System.Drawing.ColorTranslator]::FromHtml("#FBBF24"),
    30
)
$thumbBrush3 = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Rectangle 736, 232, 64, 36),
    [System.Drawing.ColorTranslator]::FromHtml("#60A5FA"),
    [System.Drawing.ColorTranslator]::FromHtml("#F472B6"),
    30
)
Draw-RoundedRect $g $thumbBrush1 504 232 64 36 6
Draw-RoundedRect $g $thumbBrush2 620 232 64 36 6
Draw-RoundedRect $g $thumbBrush3 736 232 64 36 6
$g.DrawString("Shot 01", $fontSmall, $muted, 514, 272)
$g.DrawString("Shot 02", $fontSmall, $muted, 630, 272)
$g.DrawString("Shot 03", $fontSmall, $muted, 746, 272)

$nodeBrush = New-Brush "#66E3D4"
foreach ($point in @(@(470,99), @(470,173), @(470,255), @(835,99), @(835,255))) {
    $g.FillEllipse($nodeBrush, $point[0] - 4, $point[1] - 4, 8, 8)
}

Draw-RoundedRect $g (New-Brush "#12202F") 560 338 285 28 14
$g.DrawString("Product -> Strategy -> Storyboard -> Video", $fontSmall, $muted, 583, 345)

$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)

$g.Dispose()
$bmp.Dispose()

Write-Output $out

