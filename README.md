# 🚀 Keyword Intelligence Pipeline

An AI-powered keyword intelligence pipeline for automated keyword analysis, clustering, and strategic content recommendations.

[![CI](https://github.com/your-org/keyword-intelligence-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/keyword-intelligence-pipeline/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/badge/linting-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

---

## 📋 Overview

The Keyword Intelligence Pipeline is an internal tool that automates keyword research and analysis using AI. It ingests keyword data, performs clustering and deduplication, and generates strategic content recommendations.

**Current Status**: Phase 1 — Project Foundation ✅

## 🏗️ Architecture

```
keyword_intelligence/
├── config/       → Settings management, logging configuration
├── core/         → Logger factory, exception hierarchy
├── models/       → Pydantic data models
├── services/     → External service integrations (LLM, search APIs)
├── pipeline/     → Pipeline orchestration and context management
├── utils/        → Stateless helper functions
└── ui/           → Streamlit presentation layer
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation, dependency injection patterns, and future LLM provider interface design.

## ⚡ Quick Start

### Prerequisites

- Python 3.12+
- Git

### Setup

**Windows (PowerShell):**

```powershell
# Clone the repository
git clone https://github.com/your-org/keyword-intelligence-pipeline.git
cd keyword-intelligence-pipeline

# Run the setup script (creates venv, installs deps, configures hooks)
.\scripts\setup.ps1

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Start the application
streamlit run app.py
```

**Linux / macOS (Make):**

```bash
# Clone the repository
git clone https://github.com/your-org/keyword-intelligence-pipeline.git
cd keyword-intelligence-pipeline

# Run setup (creates venv, installs deps, configures hooks)
make setup

# Activate the virtual environment
source .venv/bin/activate

# Start the application
make run
```

### Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your local settings
# See .env.example for documentation of all available variables
```

## 🛠️ Development

### Commands

| Action | Makefile | PowerShell |
|---|---|---|
| Setup (venv + deps + hooks) | `make setup` | `.\scripts\setup.ps1` |
| Run Streamlit | `make run` | `.\scripts\run.ps1` |
| Format code | `make format` | `.\scripts\format.ps1` |
| Lint code | `make lint` | `.\scripts\lint.ps1` |
| Type check | `make typecheck` | *(included in lint.ps1)* |
| Run tests | `make test` | `.\scripts\test.ps1` |
| All checks | `make check-all` | `.\scripts\lint.ps1; .\scripts\test.ps1` |

### Code Quality

This project enforces code quality through:

- **[Black](https://github.com/psf/black)** — Opinionated code formatter (line length: 88)
- **[Ruff](https://github.com/astral-sh/ruff)** — Fast Python linter with Google docstring convention
- **[MyPy](https://mypy-lang.org/)** — Static type checker in strict mode
- **[pre-commit](https://pre-commit.com/)** — Git hooks run formatters and linters before every commit

All tools are configured in [`pyproject.toml`](pyproject.toml).

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=keyword_intelligence --cov-report=term-missing

# Run only smoke tests
pytest tests/ -v -m smoke

# Run only settings tests
pytest tests/ -v -m settings
```

### VS Code Integration

The project includes optional VS Code configuration in `.vscode/`:

- **settings.json** — Python interpreter, formatter, linter settings
- **extensions.json** — Recommended extensions
- **launch.json** — Debug configurations for Streamlit and pytest

Install recommended extensions when prompted by VS Code for the best development experience.

## 📁 Project Structure

```
keyword-intelligence-pipeline/
├── app.py                      # Streamlit entrypoint
├── pyproject.toml              # Project config + tool settings
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example                # Environment variable template
├── Makefile                    # Developer commands (Make)
├── scripts/                    # Developer commands (PowerShell)
├── .github/workflows/ci.yml   # CI pipeline
├── .vscode/                    # VS Code workspace config
├── docs/                       # Project documentation
│   ├── architecture.md         # System architecture
│   ├── roadmap.md              # Phase delivery plan
│   └── decision-log.md        # Architecture decisions
├── assets/                     # Static assets
├── logs/                       # Runtime log output
├── keyword_intelligence/       # Application source code
│   ├── config/                 # Settings + logging config
│   ├── core/                   # Logger, exceptions
│   ├── models/                 # Pydantic data models
│   ├── services/               # Service integrations
│   ├── pipeline/               # Pipeline orchestration
│   ├── utils/                  # Helper functions
│   └── ui/                     # Streamlit pages
└── tests/                      # Test suite
    ├── fixtures/               # Test data
    ├── test_smoke.py           # Smoke tests
    └── test_settings.py        # Configuration tests
```

## 🗺️ Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase 1** | Project Foundation | ✅ Complete |
| **Phase 2** | AI Integration (LLM providers) | 📋 Planned |
| **Phase 3** | Data Pipeline (ingestion, caching) | 📋 Planned |
| **Phase 4** | Analysis & Reporting | 📋 Planned |
| **Phase 5** | Production Hardening | 📋 Planned |

See [docs/roadmap.md](docs/roadmap.md) for detailed phase descriptions.

## 📄 License

This project is licensed under the MIT License.
