<#
File: tools/publishing/convert-paper.ps1
Description:
    Converts a standardized research paper downloaded from ChatGPT Canvas as DOCX into:
        1. Markdown (.md)
        2. LaTeX (.tex)
        3. PDF (.pdf)

    Intended pipeline:
        Canvas -> DOCX -> Markdown -> LaTeX -> PDF

    This script assumes the DOCX was generated from the standard academic canvas format:
        Title
        Metadata
        Abstract
        1. Introduction
        2. Background and Motivation
        3. Definitions and Terminology
        4. Core Theory or Model
        5. Architecture Implications
        6. Computational or Mathematical Implications
        7. AGI Relevance
        8. Original Contributions
        9. Open Questions
        10. Future Research
        11. Conclusion
        References
        Appendices

Required software:
    1. Pandoc
       Official install page:
       https://pandoc.org/installing.html

    2. A LaTeX distribution
       Recommended for Windows: MiKTeX
       Official install page:
       https://miktex.org/howto/install-miktex

       Alternative: TeX Live
       Official Windows page:
       https://tug.org/texlive/windows.html

Recommended Windows installation:
    Option A: Manual Install
        1. Install Pandoc using the Windows MSI installer.
        2. Install MiKTeX using the Basic MiKTeX Installer.
        3. During MiKTeX setup, allow missing packages to be installed automatically.
        4. Restart PowerShell or restart the computer so PATH updates are available.

    Option B: Winget Install, if available
        winget install --id JohnMacFarlane.Pandoc -e
        winget install --id MiKTeX.MiKTeX -e

How to call:
    .\convert-paper.ps1 -InputDocx "C:\path\to\paper.docx"

Optional:
    .\convert-paper.ps1 -InputDocx "C:\path\to\paper.docx" -OutputDir "C:\path\to\output"

Outputs:
    output_folder/
        paper.md
        paper.tex
        paper.pdf
        media/

Notes:
    - The media folder stores extracted images from the DOCX.
    - PDF generation uses xelatex by default because it handles fonts and Unicode better than pdflatex.
    - If PDF generation fails due to missing LaTeX packages, open MiKTeX Console and update/install missing packages.
    - For Office Depot printing, inspect the PDF visually before submission.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$InputDocx,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir = "",

    [Parameter(Mandatory = $false)]
    [string]$PdfEngine = "xelatex"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

function Assert-FileExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Input file not found: $Path"
    }
}

function New-CleanDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

# ------------------------------------------------------------
# Validate input and tools
# ------------------------------------------------------------

Assert-FileExists -Path $InputDocx

if (-not (Test-CommandExists -CommandName "pandoc")) {
    throw "Pandoc was not found in PATH. Install Pandoc, then restart PowerShell. See: https://pandoc.org/installing.html"
}

if (-not (Test-CommandExists -CommandName $PdfEngine)) {
    throw "The LaTeX PDF engine '$PdfEngine' was not found in PATH. Install MiKTeX or TeX Live, then restart PowerShell."
}

$inputItem = Get-Item -LiteralPath $InputDocx
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($inputItem.Name)

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $inputItem.DirectoryName ($baseName + "_converted")
}

New-CleanDirectory -Path $OutputDir

$mediaDir = Join-Path $OutputDir "media"
New-CleanDirectory -Path $mediaDir

$markdownFile = Join-Path $OutputDir ($baseName + ".md")
$latexFile    = Join-Path $OutputDir ($baseName + ".tex")
$pdfFile      = Join-Path $OutputDir ($baseName + ".pdf")

Write-Host "Input DOCX: $InputDocx"
Write-Host "Output Dir: $OutputDir"
Write-Host "PDF Engine: $PdfEngine"

# ------------------------------------------------------------
# Step 1: DOCX -> Markdown
# ------------------------------------------------------------

Write-Step "Converting DOCX to Markdown"

pandoc `
    "$InputDocx" `
    --from docx `
    --to markdown+pipe_tables+grid_tables `
    --extract-media="$OutputDir" `
    --wrap=none `
    --standalone `
    --output "$markdownFile"

if (-not (Test-Path -LiteralPath $markdownFile -PathType Leaf)) {
    throw "Markdown conversion failed: $markdownFile was not created."
}

# ------------------------------------------------------------
# Step 2: Markdown -> LaTeX
# ------------------------------------------------------------

Write-Step "Converting Markdown to LaTeX"

pandoc `
    "$markdownFile" `
    --from markdown+pipe_tables+grid_tables `
    --to latex `
    --standalone `
    --number-sections `
    --toc `
    --metadata documentclass=article `
    --metadata classoption=11pt `
    --metadata geometry:margin=1in `
    --output "$latexFile"

if (-not (Test-Path -LiteralPath $latexFile -PathType Leaf)) {
    throw "LaTeX conversion failed: $latexFile was not created."
}

# ------------------------------------------------------------
# Step 3: Markdown -> PDF through LaTeX
# ------------------------------------------------------------

Write-Step "Generating PDF"

pandoc `
    "$markdownFile" `
    --from markdown+pipe_tables+grid_tables `
    --standalone `
    --number-sections `
    --toc `
    --metadata documentclass=article `
    --metadata classoption=11pt `
    --metadata geometry:margin=1in `
    --pdf-engine=$PdfEngine `
    --output "$pdfFile"

if (-not (Test-Path -LiteralPath $pdfFile -PathType Leaf)) {
    throw "PDF generation failed: $pdfFile was not created."
}

# ------------------------------------------------------------
# Final report
# ------------------------------------------------------------

Write-Step "Conversion complete"

Write-Host "Markdown: $markdownFile" -ForegroundColor Green
Write-Host "LaTeX:    $latexFile" -ForegroundColor Green
Write-Host "PDF:      $pdfFile" -ForegroundColor Green
Write-Host "Media:    $mediaDir" -ForegroundColor Green

Write-Host ""
Write-Host "Recommended final check:" -ForegroundColor Yellow
Write-Host "1. Open the PDF."
Write-Host "2. Verify title page, headings, tables, figures, references, and page breaks."
Write-Host "3. If the PDF looks correct, it should be suitable for print submission."
