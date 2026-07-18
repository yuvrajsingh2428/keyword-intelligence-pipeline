# ============================================================================
# Keyword Intelligence Pipeline — Format Script
# ============================================================================
# Formats code with Black and applies Ruff auto-fixes.
# Run from the project root:
#   .\scripts\format.ps1
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvScripts = Join-Path $ProjectRoot ".venv\Scripts"

$Black = Join-Path $VenvScripts "black.exe"
$Ruff = Join-Path $VenvScripts "ruff.exe"

$SrcDir = Join-Path $ProjectRoot "keyword_intelligence"
$TestDir = Join-Path $ProjectRoot "tests"

Write-Host "=== Formatting Code ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Black formatter
Write-Host "[1/2] Formatting with Black..." -ForegroundColor Yellow
& $Black $SrcDir $TestDir

# Step 2: Ruff auto-fix
Write-Host "[2/2] Applying Ruff fixes..." -ForegroundColor Yellow
& $Ruff check --fix $SrcDir $TestDir

Write-Host ""
Write-Host "=== Formatting Complete ===" -ForegroundColor Green
