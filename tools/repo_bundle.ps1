<#
AGI / CAS Repository Bundler

Description:
    Creates a portable repository bundle for review, upload, archival, or cross-conversation transfer.
    The script generates:
        1. A full text bundle containing selected readable files.
        2. A manifest JSON file containing file paths, sizes, hashes, and bundle metadata.
        3. An optional delta bundle when a previous manifest is supplied.

    The script supports two primary operating modes:
        - code : Bundles source-code and configuration-oriented text files.
        - arch : Bundles architecture/documentation-oriented text files and records binary docs in the manifest.

    The output folder is excluded from future scans so the script does not rebundle its own prior bundles.

Project file location:
    tools/repo_bundle.ps1

Examples:
    # Create a code bundle from the current repository
    .\tools\repo_bundle.ps1 -BundleType code -Version v0.1.0

    # Create an architecture/documentation bundle
    .\tools\repo_bundle.ps1 -BundleType arch -Version v0.1.0

    # Create a bundle from a specific repository path
    .\tools\repo_bundle.ps1 -RepoRoot "C:\path\to\agi-system" -BundleType code -Version v0.1.0

    # Create a delta bundle by comparing against a previous manifest
    .\tools\repo_bundle.ps1 -BundleType code -Version v0.1.1 -PreviousManifestPath "artifacts\bundles\agi-bundle_code_20260426_101500.manifest.json"

Parameters:
    -RepoRoot              Repository root. Defaults to current directory. If Git is available, the script resolves to the Git root.
    -BundleType            code, arch, or all. Defaults to code.
    -Version               User-defined version label written into the manifest and bundle header.
    -OutputDir             Output directory relative to repo root. Defaults to artifacts/bundles.
    -PreviousManifestPath  Optional previous manifest for generating a delta bundle.
    -MaxTextFileKB         Maximum readable text file size to include inline in the full bundle. Larger files are listed but skipped.

Notes:
    - Binary files such as .docx, .pdf, .png, .jpg, and .jpeg are recorded in the manifest but not embedded in the text bundle.
    - The script is designed for upload to ChatGPT or another reviewer, so the generated bundle favors readability and traceability.
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [ValidateSet("code", "arch", "all")]
    [string]$BundleType = "code",
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

function Resolve-RepoRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StartPath
    )

    try {
        $toplevel = (& git -C $StartPath rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($toplevel)) {
            return $toplevel.Trim()
        }
    }
    catch {
        # Fall back to the supplied path when Git is unavailable or the path is not a Git repository.
    }

    return (Resolve-Path $StartPath).Path
}

function Get-GitInfo {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $info = [ordered]@{
        available = $false
        branch    = ""
        commit    = ""
    }

    try {
        & git -C $Root --version 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) { return $info }

        $info.available = $true
        $info.branch = (& git -C $Root rev-parse --abbrev-ref HEAD).Trim()
        $info.commit = (& git -C $Root rev-parse HEAD).Trim()
    }
    catch {
        # Keep default Git info if any Git command fails.
    }

    return $info
}

# =====================================================
# FILE SELECTION
# =====================================================

function Convert-ToRepoRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$FullName
    )

    # Compatible with Windows PowerShell 5.1 and PowerShell 7+.
    # Avoids [System.IO.Path]::GetRelativePath(), which is unavailable in older .NET Framework versions.
    $rootResolved = (Resolve-Path -LiteralPath $Root).ProviderPath
    $fileResolved = (Resolve-Path -LiteralPath $FullName).ProviderPath

    if (-not $rootResolved.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $rootResolved = $rootResolved + [System.IO.Path]::DirectorySeparatorChar
    }

    $rootUri = New-Object System.Uri($rootResolved)
    $fileUri = New-Object System.Uri($fileResolved)

    $relativeUri = $rootUri.MakeRelativeUri($fileUri)
    $relativePath = [System.Uri]::UnescapeDataString($relativeUri.ToString())

    return $relativePath.Replace([char]92, [char]47)
}

function Is-ExcludedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $p = $RelativePath -replace '\\', '/'

    $excludedPatterns = @(
        ".git/",
        "__pycache__/",
        ".venv/",
        "venv/",
        "node_modules/",
		"docs\\architecture\\architecture_normalized",
		"docs\\architecture\\architecture_raw",
        "artifacts/bundles/"
    )

    foreach ($pattern in $excludedPatterns) {
        if ($p -like "*$pattern*") { return $true }
    }

    return $false
}

function Get-BundleExtensionRules {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("code", "arch", "all")]
        [string]$BundleType
    )

    $codeTextExt = @(
        ".py", ".ps1", ".psm1", ".psd1",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".md", ".txt", ".csv",
        ".sql",
        ".bat", ".cmd", ".sh",
        ".html", ".css", ".js", ".ts"
    )

    $archTextExt = @(
        ".md", ".txt", ".rst", ".csv", ".json", ".yaml", ".yml",
        ".mmd", ".mermaid", ".puml", ".plantuml"
    )

    $archBinaryExt = @(
        ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".svg", ".pptx", ".xlsx", ".drawio"
    )

    switch ($BundleType) {
        "code" {
            return [ordered]@{
                TextExtensions     = $codeTextExt
                ManifestOnlyExt     = @()
            }
        }
        "arch" {
            return [ordered]@{
                TextExtensions     = $archTextExt
                ManifestOnlyExt     = $archBinaryExt
            }
        }
        "all" {
            return [ordered]@{
                TextExtensions     = ($codeTextExt + $archTextExt | Sort-Object -Unique)
                ManifestOnlyExt     = $archBinaryExt
            }
        }
    }
}

function Get-SelectedFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [ValidateSet("code", "arch", "all")]
        [string]$BundleType
    )

    $rules = Get-BundleExtensionRules -BundleType $BundleType
    $textExt = $rules.TextExtensions
    $manifestOnlyExt = $rules.ManifestOnlyExt

    $files = Get-ChildItem -Path $Root -Recurse -File
    $selected = @()

    foreach ($f in $files) {
        $rel = Convert-ToRepoRelativePath -Root $Root -FullName $f.FullName
        if (Is-ExcludedPath -RelativePath $rel) { continue }

        $ext = $f.Extension.ToLowerInvariant()
        if (($textExt -contains $ext) -or ($manifestOnlyExt -contains $ext)) {
            $selected += [PSCustomObject]@{
                FileInfo     = $f
                RelativePath = $rel
                Extension    = $ext
                IsText       = ($textExt -contains $ext)
            }
        }
    }

    return ($selected | Sort-Object RelativePath)
}

# =====================================================
# MANIFEST SYSTEM
# =====================================================

function Build-Manifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [array]$SelectedFiles,
        [Parameter(Mandatory = $true)]
        [hashtable]$GitInfo,
        [Parameter(Mandatory = $true)]
        [string]$BundleType,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $entries = @()

    foreach ($entry in $SelectedFiles) {
        $f = $entry.FileInfo
        $hash = (Get-FileHash $f.FullName -Algorithm SHA256).Hash

        $entries += [ordered]@{
            path            = $entry.RelativePath
            size            = $f.Length
            sha256          = $hash
            included_in_text = [bool]$entry.IsText
        }
    }

    return [ordered]@{
        schema      = "agi.bundle.v3"
        bundle_type = $BundleType
        version     = $Version
        created     = (Get-Date).ToString("o")
        git         = $GitInfo
        file_count  = $entries.Count
        files       = $entries
    }
}

function Write-TextFileUtf8 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Write-Manifest {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Manifest,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $json = $Manifest | ConvertTo-Json -Depth 20
    Write-TextFileUtf8 -Path $Path -Content $json
}

function Load-Manifest {
    param(
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (-not (Test-Path $Path)) { return $null }

    return (Get-Content $Path -Raw | ConvertFrom-Json)
}

function Compare-Manifests {
    param(
        $Old,
        [Parameter(Mandatory = $true)]
        [hashtable]$New
    )

    if (-not $Old) { return $null }

    $oldMap = @{}
    foreach ($f in $Old.files) { $oldMap[$f.path] = $f }

    $newMap = @{}
    foreach ($f in $New.files) { $newMap[$f.path] = $f }

    $added = @()
    $removed = @()
    $changed = @()

    foreach ($k in $newMap.Keys) {
        if (-not $oldMap.ContainsKey($k)) {
            $added += $k
            continue
        }
        if ($oldMap[$k].sha256 -ne $newMap[$k].sha256) {
            $changed += $k
        }
    }

    foreach ($k in $oldMap.Keys) {
        if (-not $newMap.ContainsKey($k)) {
            $removed += $k
        }
    }

    return [ordered]@{
        added   = @($added | Sort-Object)
        removed = @($removed | Sort-Object)
        changed = @($changed | Sort-Object)
    }
}

# =====================================================
# BUNDLE WRITERS
# =====================================================

function Write-FullBundle {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [array]$SelectedFiles,
        [Parameter(Mandatory = $true)]
        [hashtable]$Manifest,
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,
        [Parameter(Mandatory = $true)]
        [int]$MaxKB
    )

    $sb = New-Object System.Text.StringBuilder

    $sb.AppendLine("# AGI / CAS FULL BUNDLE") | Out-Null
    $sb.AppendLine("# Bundle Type: $($Manifest.bundle_type)") | Out-Null
    $sb.AppendLine("# Version: $($Manifest.version)") | Out-Null
    $sb.AppendLine("# Created: $($Manifest.created)") | Out-Null
    $sb.AppendLine("# Schema: $($Manifest.schema)") | Out-Null
    $sb.AppendLine("") | Out-Null

    foreach ($entry in $SelectedFiles | Where-Object { $_.IsText } | Sort-Object RelativePath) {
        $f = $entry.FileInfo
        $rel = $entry.RelativePath

        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("# FILE: $rel") | Out-Null
        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("") | Out-Null

        if (($f.Length / 1KB) -gt $MaxKB) {
            $sb.AppendLine("# SKIPPED: file is larger than MaxTextFileKB ($MaxKB KB).") | Out-Null
            $sb.AppendLine("") | Out-Null
            continue
        }

        try {
            $content = Get-Content $f.FullName -Raw -ErrorAction Stop
            if (-not [string]::IsNullOrEmpty($content)) {
                $sb.AppendLine($content) | Out-Null
            }
        }
        catch {
            $sb.AppendLine("# SKIPPED: unable to read file as text. Error: $($_.Exception.Message)") | Out-Null
        }

        $sb.AppendLine("") | Out-Null
    }

    $manifestOnly = @($SelectedFiles | Where-Object { -not $_.IsText } | Sort-Object RelativePath)
    if ($manifestOnly.Count -gt 0) {
        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("# MANIFEST-ONLY FILES") | Out-Null
        $sb.AppendLine("# These files were hashed and recorded in the manifest but were not embedded in this text bundle.") | Out-Null
        $sb.AppendLine("# ==================================================") | Out-Null
        foreach ($entry in $manifestOnly) {
            $sb.AppendLine("# $($entry.RelativePath)") | Out-Null
        }
        $sb.AppendLine("") | Out-Null
    }

    Write-TextFileUtf8 -Path $OutputPath -Content $sb.ToString()
}

function Write-DeltaBundle {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [array]$SelectedFiles,
        $Diff,
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,
        [Parameter(Mandatory = $true)]
        [int]$MaxKB
    )

    if (-not $Diff) { return $false }

    $changedOrAdded = @($Diff.changed + $Diff.added | Sort-Object -Unique)
    if ($changedOrAdded.Count -eq 0) { return $false }

    $fileMap = @{}
    foreach ($entry in $SelectedFiles) {
        $fileMap[$entry.RelativePath] = $entry
    }

    $sb = New-Object System.Text.StringBuilder
    $sb.AppendLine("# AGI / CAS DELTA BUNDLE") | Out-Null
    $sb.AppendLine("# Includes changed and added text files only.") | Out-Null
    $sb.AppendLine("") | Out-Null

    foreach ($path in $changedOrAdded) {
        if (-not $fileMap.ContainsKey($path)) { continue }

        $entry = $fileMap[$path]
        $file = $entry.FileInfo

        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("# FILE: $path") | Out-Null
        $sb.AppendLine("# ==================================================") | Out-Null
        $sb.AppendLine("") | Out-Null

        if (-not $entry.IsText) {
            $sb.AppendLine("# SKIPPED: manifest-only file; not embedded in text delta bundle.") | Out-Null
            $sb.AppendLine("") | Out-Null
            continue
        }

        if (($file.Length / 1KB) -gt $MaxKB) {
            $sb.AppendLine("# SKIPPED: file is larger than MaxTextFileKB ($MaxKB KB).") | Out-Null
            $sb.AppendLine("") | Out-Null
            continue
        }

        try {
            $sb.AppendLine((Get-Content $file.FullName -Raw -ErrorAction Stop)) | Out-Null
        }
        catch {
            $sb.AppendLine("# SKIPPED: unable to read file as text. Error: $($_.Exception.Message)") | Out-Null
        }

        $sb.AppendLine("") | Out-Null
    }

    Write-TextFileUtf8 -Path $OutputPath -Content $sb.ToString()
    return $true
}

# =====================================================
# MAIN EXECUTION
# =====================================================

$RepoRoot = Resolve-RepoRoot -StartPath $RepoRoot
$GitInfo = Get-GitInfo -Root $RepoRoot

$SelectedFiles = Get-SelectedFiles -Root $RepoRoot -BundleType $BundleType
$Manifest = Build-Manifest -Root $RepoRoot -SelectedFiles $SelectedFiles -GitInfo $GitInfo -BundleType $BundleType -Version $Version

$oldManifest = Load-Manifest -Path $PreviousManifestPath
$Diff = Compare-Manifests -Old $oldManifest -New $Manifest

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDirFull = Join-Path $RepoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputDirFull | Out-Null

$fullBundlePath = Join-Path $outputDirFull "agi-bundle_${BundleType}_$timestamp.txt"
$manifestPath = Join-Path $outputDirFull "agi-bundle_${BundleType}_$timestamp.manifest.json"
$deltaPath = Join-Path $outputDirFull "agi-bundle_${BundleType}_delta_$timestamp.txt"

Write-FullBundle -Root $RepoRoot -SelectedFiles $SelectedFiles -Manifest $Manifest -OutputPath $fullBundlePath -MaxKB $MaxTextFileKB
Write-Manifest -Manifest $Manifest -Path $manifestPath
$deltaWritten = Write-DeltaBundle -Root $RepoRoot -SelectedFiles $SelectedFiles -Diff $Diff -OutputPath $deltaPath -MaxKB $MaxTextFileKB

$sizeKB = [math]::Round((Get-Item $fullBundlePath).Length / 1KB, 2)
Write-Host "Full bundle size: $sizeKB KB"

Write-Host "Full bundle written: $fullBundlePath"
Write-Host "Manifest written: $manifestPath"
if ($deltaWritten) {
    Write-Host "Delta bundle written: $deltaPath"
}
elseif ($Diff) {
    Write-Host "No delta bundle written: no added or changed files detected."
}
