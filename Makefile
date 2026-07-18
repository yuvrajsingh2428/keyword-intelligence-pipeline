# ============================================================================
# Keyword Intelligence Pipeline — Makefile
# ============================================================================
# Cross-platform developer commands. On Windows, install make via:
#   choco install make    OR    scoop install make
# Or use the PowerShell scripts in scripts/ instead.
# ============================================================================

.PHONY: setup run lint format typecheck test check-all clean pre-commit-install help

# Default target
.DEFAULT_GOAL := help

# --- Variables ---
PYTHON := python
VENV := .venv
PIP := $(VENV)/Scripts/pip
PYTEST := $(VENV)/Scripts/pytest
BLACK := $(VENV)/Scripts/black
RUFF := $(VENV)/Scripts/ruff
MYPY := $(VENV)/Scripts/mypy
STREAMLIT := $(VENV)/Scripts/streamlit
PRE_COMMIT := $(VENV)/Scripts/pre-commit

SRC := keyword_intelligence
TESTS := tests

# --- Targets ---

help: ## Show this help message
	@echo Available targets:
	@echo.
	@findstr /R "^[a-zA-Z_-]*:.*##" $(MAKEFILE_LIST) 2>nul || echo   Run 'make <target>' where target is one of the above.
	@echo.
	@echo   setup              Create venv and install all dependencies
	@echo   run                Start the Streamlit application
	@echo   lint               Run Ruff linter
	@echo   format             Format code with Black and Ruff
	@echo   typecheck          Run MyPy type checker
	@echo   test               Run pytest with coverage
	@echo   check-all          Run all quality checks (lint + format check + typecheck + test)
	@echo   clean              Remove build artifacts and caches
	@echo   pre-commit-install Install pre-commit git hooks

setup: ## Create venv and install all dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	@echo.
	@echo Setup complete. Activate venv with: .venv\Scripts\activate

run: ## Start the Streamlit application
	$(STREAMLIT) run app.py

lint: ## Run Ruff linter
	$(RUFF) check $(SRC)/ $(TESTS)/

format: ## Format code with Black and Ruff
	$(BLACK) $(SRC)/ $(TESTS)/
	$(RUFF) check --fix $(SRC)/ $(TESTS)/

typecheck: ## Run MyPy type checker
	$(MYPY) $(SRC)/

test: ## Run pytest with coverage
	$(PYTEST) $(TESTS)/ -v --tb=short --cov=$(SRC) --cov-report=term-missing

check-all: lint typecheck test ## Run all quality checks
	$(BLACK) --check $(SRC)/ $(TESTS)/
	@echo.
	@echo All checks passed!

clean: ## Remove build artifacts and caches
	@if exist $(VENV) rmdir /s /q $(VENV)
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist .mypy_cache rmdir /s /q .mypy_cache
	@if exist .ruff_cache rmdir /s /q .ruff_cache
	@if exist htmlcov rmdir /s /q htmlcov
	@if exist dist rmdir /s /q dist
	@if exist build rmdir /s /q build
	@if exist *.egg-info rmdir /s /q *.egg-info
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@echo Cleaned.

pre-commit-install: ## Install pre-commit git hooks
	$(PRE_COMMIT) install
	@echo Pre-commit hooks installed.
