<#
.SYNOPSIS
  Bundles repository files into a single reviewable text file (code/arch),
  and optionally zips binary diagram assets. Produces a manifest for incremental comparisons.

.DESCRIPTION
  - Creates versioned bundle names
  - Captures Git state (branch, commit, status)
  - Writes a manifest.json (path, size, mtime, sha256)
  - Optional incremental comparison against a previous manifest
  - Copies itself into /tools if requested

.NOTES
  PowerShell 5.1+ should work. For best UTF-8 behavior, PowerShell 7+ is recommended.
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoRoot = (Get-Location).Path,

  [Parameter(Mandatory = $false)]
  [ValidateSet("code","arch","all")]
  [string]$BundleType = "all",

  [Parameter(Mandatory = $false)]
  [string]$Version = "v0.0.0",

  [Parameter(Mandatory = $false)]
  [string]$OutputDir = "artifacts/bundles",

  [Parameter(Mandatory = $false)]
  [string]$PreviousManifestPath = "",

  [Parameter(Mandatory = $false)]
  [int]$MaxTextFileKB = 512,

  [Parameter(Mandatory = $false)]
  [switch]$ZipDiagrams,

  [Parameter(Mandatory = $false)]
  [string]$DocsDir = "docs/architecture",

  [Parameter(Mandatory = $false)]
  [string]$DiagramsDir = "docs/architecture/diagrams",

  [Parameter(Mandatory = $false)]
  [switch]$CopyScriptToTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot([string]$StartPath) {
  try {
    $toplevel = (& git -C $StartPath rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $toplevel) { return $toplevel.Trim() }
  } catch {}
  return (Resolve-Path $StartPath).Path
}

function Get-GitInfo([string]$Root) {
  $info = [ordered]@{
    available = $false
    branch    = ""
    commit    = ""
    dirty     = $false
    status    = ""
  }

  try {
    & git -C $Root --version 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) { return $info }

    $info.available = $true
    $info.branch = ((& git -C $Root rev-parse --abbrev-ref HEAD) 2>$null).Trim()
    $info.commit = ((& git -C $Root rev-parse HEAD) 2>$null).Trim()

    $status = (& git -C $Root status --porcelain=v1) 2>$null
    $info.status = ($status -join "`n").Trim()
    $info.dirty = -not [string]::IsNullOrWhiteSpace($info.status)
  } catch {}

  return $info
}

function Is-ExcludedPath([string]$RelativePath) {
  $p = $RelativePath -replace '\\','/'

  $excludedDirs = @(
    ".git/", ".venv/", "venv/", "__pycache__/", ".pytest_cache/",
    "node_modules/", "dist/", "build/", ".mypy_cache/", ".ruff_cache/",
    ".idea/", ".vscode/"
  )

  foreach ($d in $excludedDirs) {
    if ($p.StartsWith($d)) { return $true }
    if ($p -like "*/$d*")  { return $true }
  }

  return $false
}

function Try-ReadTextFile([string]$FullPath) {
  # Prefer UTF-8; fall back to default if needed
  try {
    return Get-Content -LiteralPath $FullPath -Raw -Encoding UTF8
  } catch {
    try {
      return Get-Content -LiteralPath $FullPath -Raw -Encoding Default
    } catch {
      return $null
    }
  }
}

function New-ManifestEntry([string]$Root, [System.IO.FileInfo]$File) {
  $rel = [IO.Path]::GetRelativePath($Root, $File.FullName)
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash.ToLowerInvariant()
  return [ordered]@{
    path  = ($rel -replace '\\','/')
    size  = $File.Length
    mtime = $File.LastWriteTimeUtc.ToString("o")
    sha256 = $hash
  }
}

function Load-Manifest([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Compare-Manifests($OldManifest, $NewManifest) {
  if ($null -eq $OldManifest -or $null -eq $NewManifest) { return $null }

  $oldMap = @{}
  foreach ($e in $OldManifest.files) { $oldMap[$e.path] = $e }

  $newMap = @{}
  foreach ($e in $NewManifest.files) { $newMap[$e.path] = $e }

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

  return [ordered]@{
    added = $added | Sort-Object
    removed = $removed | Sort-Object
    changed = $changed | Sort-Object
  }
}

# --- Main ---
$RepoRoot = Resolve-RepoRoot $RepoRoot
$git = Get-GitInfo $RepoRoot

$nowLocal = Get-Date
$ts = $nowLocal.ToString("yyyy-MM-dd_HHmmss")
$tz = $nowLocal.ToString("zzz") -replace ':',''
$shortSha = if ($git.available -and $git.commit.Length -ge 7) { $git.commit.Substring(0,7) } else { "nogit" }

$fullOutputDir = Join-Path $RepoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $fullOutputDir | Out-Null

# Decide what to include
$codeExt = @(".py",".ps1",".toml",".yml",".yaml",".json",".ini",".cfg",".md",".txt")
$archExt = @(".docx",".md",".txt")

$includeExt = @()
switch ($BundleType) {
  "code" { $includeExt = $codeExt }
  "arch" { $includeExt = $archExt }
  "all"  { $includeExt = ($codeExt + $archExt) | Select-Object -Unique }
}

# Collect files
$allFiles = Get-ChildItem -LiteralPath $RepoRoot -Recurse -File

$selected = New-Object System.Collections.Generic.List[System.IO.FileInfo]
foreach ($f in $allFiles) {
  $rel = [IO.Path]::GetRelativePath($RepoRoot, $f.FullName)
  $relN = ($rel -replace '\\','/')

  if (Is-ExcludedPath $relN) { continue }

  $ext = $f.Extension.ToLowerInvariant()
  if ($includeExt -contains $ext) {
    $selected.Add($f)
  }
}

# Prepare bundle filename
$bundleName = "agi-bundle_{0}_{1}_{2}_{3}_{4}.txt" -f $BundleType, $Version, $ts, $tz, $shortSha
$bundlePath = Join-Path $fullOutputDir $bundleName

# Build manifest
$manifestFiles = @()
foreach ($f in $selected) {
  $manifestFiles += (New-ManifestEntry $RepoRoot $f)
}

$manifest = [ordered]@{
  schema = "agi.bundle.manifest.v1"
  bundle_type = $BundleType
  version = $Version
  created_local = $nowLocal.ToString("o")
  created_utc = (Get-Date).ToUniversalTime().ToString("o")
  repo_root = ($RepoRoot -replace '\\','/')
  git = $git
  file_count = $manifestFiles.Count
  files = $manifestFiles
}

$oldManifest = Load-Manifest $PreviousManifestPath
$diff = $null
if ($oldManifest) {
  $diff = Compare-Manifests $oldManifest $manifest
  $manifest["diff_against_previous"] = $diff
  $manifest["previous_manifest_path"] = ($PreviousManifestPath -replace '\\','/')
}

# Write bundle
$sb = New-Object System.Text.StringBuilder

$null = $sb.AppendLine("# AGI REPOSITORY BUNDLE")
$null = $sb.AppendLine("# bundle_type: $BundleType")
$null = $sb.AppendLine("# version: $Version")
$null = $sb.AppendLine("# created_local: $($manifest.created_local)")
$null = $sb.AppendLine("# created_utc:   $($manifest.created_utc)")
$null = $sb.AppendLine("# repo_root: $($manifest.repo_root)")
$null = $sb.AppendLine("# git_available: $($git.available)")
if ($git.available) {
  $null = $sb.AppendLine("# git_branch: $($git.branch)")
  $null = $sb.AppendLine("# git_commit: $($git.commit)")
  $null = $sb.AppendLine("# git_dirty:  $($git.dirty)")
}
$null = $sb.AppendLine("")

# Embed filelayout.txt if present
$fileLayoutPath = Join-Path $RepoRoot "filelayout.txt"
if (Test-Path -LiteralPath $fileLayoutPath) {
  $null = $sb.AppendLine("# ------------------------------")
  $null = $sb.AppendLine("# FILE TREE (filelayout.txt)")
  $null = $sb.AppendLine("# ------------------------------")
  $null = $sb.AppendLine((Get-Content -LiteralPath $fileLayoutPath -Raw -Encoding UTF8))
  $null = $sb.AppendLine("")
}

# Diff summary (if any)
if ($diff) {
  $null = $sb.AppendLine("# ------------------------------")
  $null = $sb.AppendLine("# INCREMENTAL DIFF (vs previous manifest)")
  $null = $sb.AppendLine("# added:   $($diff.added.Count)")
  $null = $sb.AppendLine("# removed: $($diff.removed.Count)")
  $null = $sb.AppendLine("# changed: $($diff.changed.Count)")
  $null = $sb.AppendLine("# ------------------------------")
  if ($diff.changed.Count -gt 0) {
    $null = $sb.AppendLine("# CHANGED FILES:")
    foreach ($p in $diff.changed) { $null = $sb.AppendLine("#  - $p") }
    $null = $sb.AppendLine("")
  }
}

# Contents
foreach ($f in ($selected | Sort-Object FullName)) {
  $rel = [IO.Path]::GetRelativePath($RepoRoot, $f.FullName)
  $relN = ($rel -replace '\\','/')
  $entry = $manifestFiles | Where-Object { $_.path -eq $relN } | Select-Object -First 1

  $null = $sb.AppendLine("# ==================================================")
  $null = $sb.AppendLine("# FILE: $relN")
  $null = $sb.AppendLine("# size: $($entry.size) bytes")
  $null = $sb.AppendLine("# mtime_utc: $($entry.mtime)")
  $null = $sb.AppendLine("# sha256: $($entry.sha256)")
  $null = $sb.AppendLine("# ==================================================")
  $null = $sb.AppendLine("")

  # Skip huge text files
  if (($f.Length / 1KB) -gt $MaxTextFileKB) {
    $null = $sb.AppendLine("# [SKIPPED CONTENT: file exceeds MaxTextFileKB=$MaxTextFileKB]")
    $null = $sb.AppendLine("")
    continue
  }

  $content = $null
  $ext = $f.Extension.ToLowerInvariant()

  if ($ext -eq ".docx") {
    # DOCX is zipped XML; keep metadata only unless you add an extractor step
    $null = $sb.AppendLine("# [DOCX NOT INLINED: include a text-extraction step if desired]")
    $null = $sb.AppendLine("")
    continue
  }

  $content = Try-ReadTextFile $f.FullName
  if ($null -eq $content) {
    $null = $sb.AppendLine("# [UNREADABLE AS TEXT]")
    $null = $sb.AppendLine("")
    continue
  }

  $null = $sb.AppendLine($content.TrimEnd())
  $null = $sb.AppendLine("")
}

# Manifest JSON at end
$null = $sb.AppendLine("# ------------------------------")
$null = $sb.AppendLine("# MANIFEST JSON (v1)")
$null = $sb.AppendLine("# ------------------------------")
$manifestJson = ($manifest | ConvertTo-Json -Depth 10)
$null = $sb.AppendLine($manifestJson)

# Write file as UTF-8 (no BOM)
[System.IO.File]::WriteAllText($bundlePath, $sb.ToString(), New-Object System.Text.UTF8Encoding($false))
Write-Host "Wrote bundle: $bundlePath"

# Write manifest separately too
$manifestName = $bundleName -replace '\.txt$','.manifest.json'
$manifestPath = Join-Path $fullOutputDir $manifestName
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, New-Object System.Text.UTF8Encoding($false))
Write-Host "Wrote manifest: $manifestPath"

if ($diff -and ($diff.changed.Count -gt 0 -or $diff.added.Count -gt 0)) {

  $deltaName = $bundleName -replace "agi-bundle","agi-bundle_delta"
  $deltaPath = Join-Path $fullOutputDir $deltaName

  $deltaBuilder = New-Object System.Text.StringBuilder
  $deltaBuilder.AppendLine("# DELTA BUNDLE") | Out-Null

  foreach ($filePath in ($diff.changed + $diff.added)) {

      $fileObj = $selected | Where-Object {
          ([IO.Path]::GetRelativePath($RepoRoot, $_.FullName) -replace '\\','/') -eq $filePath
      }

      if ($fileObj) {
          $content = Get-Content -LiteralPath $fileObj.FullName -Raw -Encoding UTF8
          $deltaBuilder.AppendLine("# FILE: $filePath") | Out-Null
          $deltaBuilder.AppendLine($content) | Out-Null
      }
  }

  [System.IO.File]::WriteAllText($deltaPath, $deltaBuilder.ToString(), New-Object System.Text.UTF8Encoding($false))
  Write-Host "Wrote delta bundle: $deltaPath"
}


# Zip diagrams if requested
if ($ZipDiagrams) {
  $diagFull = Join-Path $RepoRoot $DiagramsDir
  if (Test-Path -LiteralPath $diagFull) {
    $zipName = "agi-bundle_diagrams_{0}_{1}_{2}_{3}_{4}.zip" -f $BundleType, $Version, $ts, $tz, $shortSha
    $zipPath = Join-Path $fullOutputDir $zipName
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $diagFull "*") -DestinationPath $zipPath
    Write-Host "Wrote diagrams zip: $zipPath"
  } else {
    Write-Host "Diagrams directory not found: $DiagramsDir"
  }
}

# Copy script into /tools if requested
if ($CopyScriptToTools) {
  $toolsDir = Join-Path $RepoRoot "tools"
  New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
  $dst = Join-Path $toolsDir (Split-Path -Leaf $PSCommandPath)
  if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
    Copy-Item -LiteralPath $PSCommandPath -Destination $dst -Force
    Write-Host "Copied script to: $dst"
  } else {
    Write-Host "Note: PSCommandPath unavailable; save this script into /tools manually."
  }
}
