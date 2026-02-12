<#
AGI Repository Bundler – Modular Version
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$BundleType = "all",
    [string]$Version = "v0.0.0",
    [string]$OutputDir = "artifacts/bundles",
    [string]$PreviousManifestPath = "",
    [int]$MaxTextFileKB = 512
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =====================================================
# REPOSITORY INSPECTION
# =====================================================

function Resolve-RepoRoot($StartPath) {
    try {
        $toplevel = (& git -C $StartPath rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0) { return $toplevel.Trim() }
    } catch {}
    return (Resolve-Path $StartPath).Path
}

function Get-GitInfo($Root) {
    $info = @{
        available = $false
        branch = ""
        commit = ""
    }

    try {
        & git -C $Root --version 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) { return $info }

        $info.available = $true
        $info.branch = (& git -C $Root rev-parse --abbrev-ref HEAD).Trim()
        $info.commit = (& git -C $Root rev-parse HEAD).Trim()
    } catch {}

    return $info
}

# =====================================================
# FILE SELECTION
# =====================================================

function Is-ExcludedPath($RelativePath) {
    $p = $RelativePath -replace '\\','/'

    $excluded = @(".git/","__pycache__/",".venv/","venv/","node_modules/")
    foreach ($d in $excluded) {
        if ($p -like "*$d*") { return $true }
    }
    return $false
}

function Get-SelectedFiles($Root, $BundleType) {

    $codeExt = @(".py",".ps1",".json",".yaml",".yml",".md",".txt")
    $archExt = @(".docx",".md",".txt")

    $includeExt = switch ($BundleType) {
        "code" { $codeExt }
        "arch" { $archExt }
        default { ($codeExt + $archExt) | Select-Object -Unique }
    }

    $files = Get-ChildItem -Path $Root -Recurse -File

    $selected = @()

    foreach ($f in $files) {
        $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
        if (Is-ExcludedPath $rel) { continue }

        if ($includeExt -contains $f.Extension.ToLower()) {
            $selected += $f
        }
    }

    return $selected
}

# =====================================================
# MANIFEST SYSTEM
# =====================================================

function Build-Manifest($Root, $Files, $GitInfo, $BundleType, $Version) {

    $entries = @()

    foreach ($f in $Files) {
        $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)
        $hash = (Get-FileHash $f.FullName -Algorithm SHA256).Hash

        $entries += @{
            path = $rel -replace '\\','/'
            size = $f.Length
            sha256 = $hash
        }
    }

    return @{
        schema = "agi.bundle.v2"
        bundle_type = $BundleType
        version = $Version
        created = (Get-Date).ToString("o")
        git = $GitInfo
        file_count = $entries.Count
        files = $entries
    }
}

function Write-Manifest($Manifest, $Path) {
    $json = $Manifest | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($Path, $json)
}

function Load-Manifest($Path) {
    if (-not (Test-Path $Path)) { return $null }
    return Get-Content $Path -Raw | ConvertFrom-Json
}

function Compare-Manifests($Old, $New) {

    if (-not $Old) { return $null }

    $oldMap = @{}
    foreach ($f in $Old.files) { $oldMap[$f.path] = $f }

    $newMap = @{}
    foreach ($f in $New.files) { $newMap[$f.path] = $f }

    $added = @()
    $removed = @()
    $changed = @()

    foreach ($k in $newMap.Keys) {
        if (-not $oldMap.ContainsKey($k)) { $added += $k; continue }
        if ($oldMap[$k].sha256 -ne $newMap[$k].sha256) { $changed += $k }
    }

    foreach ($k in $oldMap.Keys) {
        if (-not $newMap.ContainsKey($k)) { $removed += $k }
    }

    return @{
        added = $added
        removed = $removed
        changed = $changed
    }
}

# =====================================================
# BUNDLE WRITERS
# =====================================================

function Write-FullBundle($Root, $Files, $Manifest, $OutputPath, $MaxKB) {

    $sb = New-Object System.Text.StringBuilder

    $sb.AppendLine("# AGI FULL BUNDLE") | Out-Null
    $sb.AppendLine("# Version: $($Manifest.version)") | Out-Null
    $sb.AppendLine("# Created: $($Manifest.created)") | Out-Null
    $sb.AppendLine("") | Out-Null

    foreach ($f in $Files | Sort-Object FullName) {

        $rel = [IO.Path]::GetRelativePath($Root, $f.FullName)

        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("# FILE: $rel") | Out-Null
        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("") | Out-Null

        if (($f.Length / 1KB) -gt $MaxKB) {
            $sb.AppendLine("# SKIPPED (too large)") | Out-Null
            continue
        }

        $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $sb.AppendLine($content) | Out-Null
        }

        $sb.AppendLine("") | Out-Null
    }

    [System.IO.File]::WriteAllText($OutputPath, $sb.ToString())
}

function Write-DeltaBundle($Root, $Files, $Diff, $OutputPath) {

    if (-not $Diff) { return }
    if (($Diff.changed.Count + $Diff.added.Count) -eq 0) { return }

    $sb = New-Object System.Text.StringBuilder
    $sb.AppendLine("# AGI DELTA BUNDLE") | Out-Null
    $sb.AppendLine("") | Out-Null

    foreach ($path in ($Diff.changed + $Diff.added)) {

        $file = $Files | Where-Object {
            ([IO.Path]::GetRelativePath($Root, $_.FullName) -replace '\\','/') -eq $path
        }

        if ($file) {
            $sb.AppendLine("# FILE: $path") | Out-Null
            $sb.AppendLine("") | Out-Null
            $sb.AppendLine((Get-Content $file.FullName -Raw)) | Out-Null
            $sb.AppendLine("") | Out-Null
        }
    }

    [System.IO.File]::WriteAllText($OutputPath, $sb.ToString())
}

# =====================================================
# MAIN EXECUTION
# =====================================================

$RepoRoot = Resolve-RepoRoot $RepoRoot
$GitInfo = Get-GitInfo $RepoRoot

$Files = Get-SelectedFiles $RepoRoot $BundleType
$Manifest = Build-Manifest $RepoRoot $Files $GitInfo $BundleType $Version

$oldManifest = Load-Manifest $PreviousManifestPath
$Diff = Compare-Manifests $oldManifest $Manifest

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDirFull = Join-Path $RepoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputDirFull | Out-Null

$fullBundlePath = Join-Path $outputDirFull "agi-bundle_$timestamp.txt"
$manifestPath = Join-Path $outputDirFull "agi-bundle_$timestamp.manifest.json"
$deltaPath = Join-Path $outputDirFull "agi-bundle_delta_$timestamp.txt"

Write-FullBundle $RepoRoot $Files $Manifest $fullBundlePath $MaxTextFileKB
Write-Manifest $Manifest $manifestPath
Write-DeltaBundle $RepoRoot $Files $Diff $deltaPath

Write-Host "Full bundle written: $fullBundlePath"
Write-Host "Manifest written: $manifestPath"
if ($Diff) { Write-Host "Delta bundle written: $deltaPath" }
