# ============================================================================
# Keyword Intelligence Pipeline — Run Script
# ============================================================================
# Starts the Streamlit application. Run from the project root:
#   .\scripts\run.ps1
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$StreamlitPath = Join-Path $ProjectRoot ".venv\Scripts\streamlit.exe"

if (-Not (Test-Path $StreamlitPath)) {
    Write-Host "Error: Streamlit not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Starting Keyword Intelligence Pipeline..." -ForegroundColor Cyan
& $StreamlitPath run (Join-Path $ProjectRoot "keyword_intelligence\ui\app.py")
