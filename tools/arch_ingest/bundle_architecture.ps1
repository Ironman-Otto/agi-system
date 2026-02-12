param(
    [string]$SourceDir = "C:\dev\architecture_normalized",
    [string]$OutputFile = "C:\dev\architecture_normalized\architecture_full_bundle_v1.txt"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$sb = New-Object System.Text.StringBuilder

# Header
$null = $sb.AppendLine("# =========================================")
$null = $sb.AppendLine("# ARCHITECTURE FULL BUNDLE")
$null = $sb.AppendLine("# Version: v1")
$null = $sb.AppendLine("# Generated: $timestamp")
$null = $sb.AppendLine("# Source: $SourceDir")
$null = $sb.AppendLine("# =========================================")
$null = $sb.AppendLine("")

# Collect files
$files = Get-ChildItem $SourceDir -Recurse -File |
    Where-Object {
        ($_.Extension -in ".txt", ".md") -and
        $_.Name -notmatch "full_bundle" -and
        $_.Name -notmatch "cmb_core_architecture_v1.0" -and
        $_.Name -notmatch "extraction_failures"
    } |
    Sort-Object FullName


# Manifest
$null = $sb.AppendLine("# ---------- FILE MANIFEST ----------")
foreach ($file in $files) {
    $null = $sb.AppendLine("# $($file.Name) | $([math]::Round($file.Length/1KB,2)) KB")
}
$null = $sb.AppendLine("# -----------------------------------")
$null = $sb.AppendLine("")

# File Contents
foreach ($file in $files) {
    $null = $sb.AppendLine("# ===== FILE START =====")
    $null = $sb.AppendLine("# File: $($file.Name)")
    $null = $sb.AppendLine("# Size: $($file.Length) bytes")
    $null = $sb.AppendLine("# -----------------------------------")
    $null = $sb.AppendLine("")

    $content = Get-Content $file.FullName -Raw
    $null = $sb.AppendLine($content)

    $null = $sb.AppendLine("")
    $null = $sb.AppendLine("# ===== FILE END =====")
    $null = $sb.AppendLine("")
}

$sb.ToString() | Set-Content $OutputFile -Encoding UTF8

Write-Host "Architecture bundle generated:"
Write-Host $OutputFile
Write-Host "Files found:" $files.Count
