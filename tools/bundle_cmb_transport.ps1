param(
    [string]$RepoRoot = "C:\dev\agi-system",
    [string]$OutputFile = "C:\dev\agi-system\code_bundles\cmb_transport_bundle_v1.txt"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$sb = New-Object System.Text.StringBuilder

$null = $sb.AppendLine("# =========================================")
$null = $sb.AppendLine("# CMB TRANSPORT CODE BUNDLE")
$null = $sb.AppendLine("# Version: v1")
$null = $sb.AppendLine("# Generated: $timestamp")
$null = $sb.AppendLine("# =========================================")
$null = $sb.AppendLine("")

# --- Collect Files from Authoritative Transport Directories ---

$cmbPath = Join-Path $RepoRoot "src\core\cmb"
$messagesPath = Join-Path $RepoRoot "src\core\messages"

$files = @()

if (Test-Path $cmbPath) {
    $files += Get-ChildItem $cmbPath -Recurse -File -Include *.py
}

if (Test-Path $messagesPath) {
    $files += Get-ChildItem $messagesPath -Recurse -File -Include *.py
}

$files = $files | Sort-Object FullName

# --- Manifest ---

$null = $sb.AppendLine("# -------- FILE MANIFEST --------")
foreach ($file in $files) {
    $null = $sb.AppendLine("# $($file.FullName)")
}
$null = $sb.AppendLine("# --------------------------------")
$null = $sb.AppendLine("")

# --- Append Files ---

foreach ($file in $files) {
    $null = $sb.AppendLine("# ====================================")
    $null = $sb.AppendLine("# FILE: $($file.FullName)")
    $null = $sb.AppendLine("# ====================================")
    $null = $sb.AppendLine("")

    $content = Get-Content $file.FullName -Raw
    $null = $sb.AppendLine($content)
    $null = $sb.AppendLine("")
}

$sb.ToString() | Set-Content $OutputFile -Encoding UTF8

Write-Host ""
Write-Host "CMB Transport bundle generated:"
Write-Host $OutputFile
Write-Host "Files included:" $files.Count
