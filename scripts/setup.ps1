# ============================================================================
# Keyword Intelligence Pipeline - Setup Script
# ============================================================================
# Creates a Python virtual environment, installs all dependencies, and
# configures pre-commit hooks. Run from the project root:
#   .\scripts\setup.ps1
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvPath = Join-Path $ProjectRoot ".venv"
$PipPath = Join-Path $VenvPath "Scripts\pip.exe"
$PreCommitPath = Join-Path $VenvPath "Scripts\pre-commit.exe"

Write-Host "=== Keyword Intelligence Pipeline - Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
if (-Not (Test-Path $VenvPath)) {
    Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
    py -m venv $VenvPath
} else {
    Write-Host "[1/5] Virtual environment already exists." -ForegroundColor Green
}

# Step 2: Upgrade pip
Write-Host "[2/5] Upgrading pip..." -ForegroundColor Yellow
& $PipPath install --upgrade pip | Out-Null

# Step 3: Install dependencies
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
& $PipPath install -r (Join-Path $ProjectRoot "requirements-dev.txt")

# Step 4: Install package in editable mode
Write-Host "[4/5] Installing package in editable mode..." -ForegroundColor Yellow
& $PipPath install -e $ProjectRoot

# Step 5: Install pre-commit hooks
if (Test-Path $PreCommitPath) {
    Write-Host "[5/5] Installing pre-commit hooks..." -ForegroundColor Yellow
    & $PreCommitPath install
} else {
    Write-Host "[5/5] Pre-commit not found, skipping hooks." -ForegroundColor DarkYellow
}

# Step 5: Copy .env.example to .env if needed
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"
if (-Not (Test-Path $EnvFile) -And (Test-Path $EnvExample)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Activate the virtual environment with:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
