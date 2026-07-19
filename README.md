# 🚀 Keyword Intelligence Pipeline

An AI-powered keyword intelligence pipeline for automated keyword analysis, clustering, and strategic content recommendations.

[![CI](https://github.com/your-org/keyword-intelligence-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/keyword-intelligence-pipeline/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/badge/linting-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

---

## 📋 Overview

The Keyword Intelligence Pipeline is an enterprise-grade automated keyword analysis tool. It ingests raw keyword datasets and enriches them by combining deterministic business logic with AI-powered classification. By analyzing a target company's business context, it intelligently filters, deduplicates, and categorizes keywords to surface the most relevant strategic content opportunities.

**Current Status**: Production Ready ✅

## ✨ Features

- **Business Context Extraction**: Automatically understands the target company's industry, products, and services from their domain.
- **Deterministic Classification**: High-speed, rule-based keyword filtering to reduce unnecessary AI workload.
- **AI-powered Keyword Classification**: Uses Large Language Models (LLMs) to accurately determine keyword relevance, intent, and semantic clustering.
- **Duplicate Detection**: Identifies and removes exact and semantically duplicate keywords.
- **Search Volume Enrichment**: Fetches and aligns keyword search volume and CPC metrics.
- **Multi-Key Gemini Failover**: Robust AI layer that gracefully handles quota limits by rotating through multiple API keys.
- **OpenRouter Fallback**: Ensures uninterrupted processing by automatically falling back to OpenRouter if primary providers fail.
- **Streamlit Dashboard**: A professional, real-time UI for uploading datasets, monitoring pipeline progress, and reviewing results.
- **Excel & JSON Reporting**: Produces clean, actionable Excel files for end-users and detailed JSON payloads for technical integration.

## 🔄 Pipeline Workflow

Upload Dataset
↓
Validation
↓
Business Context
↓
Duplicate Detection
↓
Search Volume
↓
AI Classification
↓
Report Generation

## 🛡️ AI Resilience

The pipeline features a highly resilient AI orchestration layer designed for production reliability:
- **Automatic Gemini API key rotation**: Seamlessly cycles through up to 5 configured Google Gemini keys.
- **Graceful quota handling**: Automatically detects `429 Too Many Requests` or quota limits and fails over without interrupting the pipeline.
- **Automatic OpenRouter fallback**: If all primary Gemini keys are exhausted, the engine delegates unresolved keywords to OpenRouter.
- **Guaranteed Pipeline Completion**: In the absolute worst-case scenario where all AI providers are down, the pipeline still completes using deterministic matches and produces a valid output.

## 💻 Demo Workflow

1. **Upload**: Provide a CSV/Excel dataset and enter the target company's domain.
2. **Process**: The pipeline extracts business context and streams provider status directly to the UI.
3. **Review**: View the comprehensive Pipeline Summary card and classification preview.
4. **Download**: Export the completed analysis as a full report or filtered relevant keywords in Excel.

## 🏗️ Architecture

```
keyword_intelligence/
├── config/               → Settings management, logging configuration
├── core/                 → Logger factory, exception hierarchy, constants
├── models/               → Pydantic data models
├── ai_intelligence/      → AI Provider registry, API integrations
├── business_context/     → Business context extraction, enrichment, validation
├── duplicate_detection/  → Canonicalization, keyword deduplication
├── search_volume/        → Volume fetching, batching
├── pipeline/             → Pipeline orchestration and stage definitions
├── reporting/            → Analytics, formatting, and file export
└── ui/                   → Streamlit presentation layer
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
streamlit run keyword_intelligence\ui\app.py
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

### Environment Variables

Configure your pipeline by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Primary Configuration Variables:**
- `APP_ENV`: Deployment environment (`development`, `staging`, `production`).
- `LOG_LEVEL`: Application logging level (e.g., `INFO`, `DEBUG`).
- `GOOGLE_GEMINI_API_KEY_1` to `5`: API keys for the primary Google Gemini provider. The system will automatically rotate through these.
- `OPENROUTER_API_KEY`: API key for the OpenRouter fallback provider.
- `OPENROUTER_MODEL`: The specific model to use for the OpenRouter fallback.

*Note: Never commit your `.env` file or expose your API keys in version control.*

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
| **Phase 2** | AI Integration (LLM providers) | ✅ Complete |
| **Phase 3** | Data Pipeline (ingestion, caching) | ✅ Complete |
| **Phase 4** | Analysis & Reporting | ✅ Complete |
| **Phase 5** | Production Hardening | ✅ Complete |

See [docs/roadmap.md](docs/roadmap.md) for detailed phase descriptions.

## 📄 License

This project is licensed under the MIT License.
