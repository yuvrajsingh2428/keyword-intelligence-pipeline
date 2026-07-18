# ============================================================================
# Keyword Intelligence Pipeline — Test Script
# ============================================================================
# Runs pytest with coverage reporting. Run from the project root:
#   .\scripts\test.ps1
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Pytest = Join-Path $ProjectRoot ".venv\Scripts\pytest.exe"
$TestDir = Join-Path $ProjectRoot "tests"

if (-Not (Test-Path $Pytest)) {
    Write-Host "Error: pytest not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "=== Running Tests ===" -ForegroundColor Cyan
Write-Host ""

& $Pytest $TestDir `
    -v `
    --tb=short `
    --cov=keyword_intelligence `
    --cov-report=term-missing

$ExitCode = $LASTEXITCODE

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "=== All Tests Passed ===" -ForegroundColor Green
} else {
    Write-Host "=== Tests Failed ===" -ForegroundColor Red
}

exit $ExitCode
