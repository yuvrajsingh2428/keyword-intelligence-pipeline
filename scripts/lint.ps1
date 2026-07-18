# ============================================================================
# Keyword Intelligence Pipeline — Lint Script
# ============================================================================
# Runs Ruff linter, Black format check, and MyPy type checker.
# Run from the project root:
#   .\scripts\lint.ps1
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvScripts = Join-Path $ProjectRoot ".venv\Scripts"

$Ruff = Join-Path $VenvScripts "ruff.exe"
$Black = Join-Path $VenvScripts "black.exe"
$MyPy = Join-Path $VenvScripts "mypy.exe"

$SrcDir = Join-Path $ProjectRoot "keyword_intelligence"
$TestDir = Join-Path $ProjectRoot "tests"

Write-Host "=== Running Code Quality Checks ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Ruff linter
Write-Host "[1/3] Running Ruff linter..." -ForegroundColor Yellow
& $Ruff check $SrcDir $TestDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Step 2: Black format check
Write-Host "[2/3] Checking formatting with Black..." -ForegroundColor Yellow
& $Black --check $SrcDir $TestDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Step 3: MyPy type checker
Write-Host "[3/3] Running MyPy type checker..." -ForegroundColor Yellow
& $MyPy $SrcDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== All Checks Passed ===" -ForegroundColor Green
