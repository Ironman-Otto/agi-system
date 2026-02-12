<#
.SYNOPSIS
  Generates repository layout files:
    - filelayout.txt (human readable tree)
    - filelayout.json (machine-readable structure)

.DESCRIPTION
  Designed for AGI repo governance and drift tooling.
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$OutputDir = ".",
    [switch]$IncludeSizes,
    [switch]$IncludeTimestamps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------
# Resolve Repo Root
# ---------------------------------------------

function Resolve-RepoRoot($StartPath) {
    try {
        $toplevel = (& git -C $StartPath rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0) { return $toplevel.Trim() }
    } catch {}
    return (Resolve-Path $StartPath).Path
}

# ---------------------------------------------
# Exclusion Rules
# ---------------------------------------------

function Is-Excluded($RelativePath) {
    $p = $RelativePath -replace '\\','/'

    $excluded = @(
        ".git/",
        ".venv/",
        "venv/",
        "__pycache__/",
        "node_modules/",
        "dist/",
        "build/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/"
    )

    foreach ($e in $excluded) {
        if ($p -like "*$e*") { return $true }
    }

    return $false
}

# ---------------------------------------------
# Build Tree Structure
# ---------------------------------------------

function Build-Layout($Root) {

    $items = Get-ChildItem -Path $Root -Recurse -Force |
             Sort-Object FullName

    $layout = @()

    foreach ($item in $items) {

        $rel = [IO.Path]::GetRelativePath($Root, $item.FullName)
        if ([string]::IsNullOrWhiteSpace($rel)) { continue }
        if (Is-Excluded $rel) { continue }

        $entry = @{
            path = $rel -replace '\\','/'
            type = if ($item.PSIsContainer) { "directory" } else { "file" }
        }

        if (-not $item.PSIsContainer) {
            if ($IncludeSizes) {
                $entry["size"] = $item.Length
            }
            if ($IncludeTimestamps) {
                $entry["mtime"] = $item.LastWriteTimeUtc.ToString("o")
            }
        }

        $layout += $entry
    }

    return $layout
}

# ---------------------------------------------
# Write Human-Readable Tree
# ---------------------------------------------

function Write-TreeText($Layout, $Path) {

    $sb = New-Object System.Text.StringBuilder
    $sb.AppendLine("AGI Repository Layout") | Out-Null
    $sb.AppendLine("Generated: $(Get-Date -Format o)") | Out-Null
    $sb.AppendLine("") | Out-Null

    foreach ($entry in $Layout) {

        $indentLevel = ($entry.path.Split('/').Count - 1)
        $indent = ("  " * $indentLevel)

        if ($entry.type -eq "directory") {
            $sb.AppendLine("$indent[$($entry.path.Split('/')[-1])]") | Out-Null
        }
        else {
            $line = "$indent$($entry.path.Split('/')[-1])"

            if ($entry.ContainsKey("size")) {
                $line += "  ($($entry.size) bytes)"
            }

            $sb.AppendLine($line) | Out-Null
        }
    }

    [System.IO.File]::WriteAllText($Path, $sb.ToString())
}

# ---------------------------------------------
# MAIN
# ---------------------------------------------

$RepoRoot = Resolve-RepoRoot $RepoRoot
Write-Host "Resolved repo root: $RepoRoot"

$layout = Build-Layout $RepoRoot

$outputTxt = Join-Path $OutputDir "filelayout.txt"
$outputJson = Join-Path $OutputDir "filelayout.json"

Write-TreeText $layout $outputTxt

$layout | ConvertTo-Json -Depth 10 | Out-File $outputJson -Encoding utf8

Write-Host "Generated:"
Write-Host "  $outputTxt"
Write-Host "  $outputJson"
