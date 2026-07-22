# Keyword Intelligence Pipeline

## Overview

The Keyword Intelligence Pipeline is an enterprise-grade, automated keyword analysis tool designed to process raw keyword datasets and filter them based on the strategic business context of a target company. 

It solves the problem of manual, time-consuming keyword categorization by combining a high-speed **deterministic pipeline** with an **AI fallback engine**.

- **Dynamic Business Profile Generation**: The pipeline asynchronously crawls the target company's website (e.g., `apple.com`) to deterministically extract product families, brands, and categories without any hardcoded rules.
- **Deterministic Pipeline**: Keywords are matched against the dynamic profile using exact, normalized, and fuzzy matching to instantly classify relevant keywords.
- **AI Fallback**: Ambiguous keywords that fail deterministic matching are seamlessly delegated to a resilient Large Language Model (LLM) classification engine, which categorizes them and provides reasoning.
- **Output Artifacts**: Produces business-ready Excel workbooks, raw CSVs, and detailed telemetry JSONs.

## Features

- **Automated Website Crawling**: Dynamically extracts Business Context from any retailer.
- **Intelligent Column Resolution**: Automatically detects keyword columns in input datasets.
- **Fuzzy Duplicate Detection**: Identifies exact and semantically similar duplicates.
- **Deterministic Fast-Path**: Eliminates 20-40% of AI requests through high-confidence matching.
- **Resilient AI Execution**: Features rotating Gemini API keys and OpenRouter fallbacks for maximum uptime.
- **Comprehensive Reporting**: Generates metrics on pipeline health, stage duration, and LLM reduction percentages.

## Architecture

The system processes data through a strict pipeline flow:

```
Input Dataset
↓
Validation
↓
Normalization
↓
Duplicate Detection
↓
Business Context
↓
Decision Engine
↓
AI Classification
↓
Reporting
```

## Project Structure

- `keyword_intelligence/`: Core application logic.
  - `ai_intelligence/`: AI provider integrations (Gemini, OpenRouter).
  - `business_context/`: Website crawlers, HTML extractors, and LLM-assisted context enrichment.
  - `column_resolver/`: Dynamic schema detection.
  - `duplicate_detection/`: Fuzzy and semantic duplicate strategies.
  - `pipeline/`: Pipeline orchestration and stage definitions.
  - `reporting/`: Excel and JSON exporter modules.
- `tests/`: Unit and integration test suite.
- `examples/`: Sample input datasets for pipeline testing.
- `scripts/`: Development scripts.

## Requirements

- **Python**: 3.12+
- **Virtual Environment**: Recommended (venv)
- **Dependencies**: pandas, pydantic, beautifulsoup4, google-genai, etc. (See `requirements.txt`)

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/keyword-intelligence-pipeline.git

# Navigate to the directory
cd keyword-intelligence-pipeline

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Configure your pipeline by copying the example environment file:

```bash
cp .env.example .env
```

### Required Variables
- `APP_ENV`: Deployment environment (e.g., `production`, `development`).
- `LOG_LEVEL`: Output verbosity (e.g., `INFO`, `DEBUG`).

### Optional Variables (AI Providers)
At least one API key must be provided if using AI models:
- `GOOGLE_GEMINI_API_KEY_1` to `GOOGLE_GEMINI_API_KEY_5`: Primary Gemini API keys (the system auto-rotates these to avoid rate limits).
- `OPEN_ROUTER_API_KEY`: Fallback API key.
- `OPEN_ROUTER_MODEL`: Model identifier for OpenRouter (default: `google/gemini-2.5-flash`).

## Running the Pipeline

Execute the pipeline using the primary CLI runner:

```bash
python run_pipeline.py \
  --input examples/demo_dataset.csv \
  --company Lenovo \
  --website https://www.lenovo.com/us
```

### CLI Parameters
- `--input`: (Required) Path to the input `.csv`, `.xls`, or `.xlsx` file.
- `--company`: (Required) The name of the target company to analyze.
- `--website`: (Required) The URL of the target company to crawl for business context.
- `--industry`: (Optional) The industry of the company, aiding LLM enrichment.
- `--sheet`: (Optional) Specific sheet name to load if passing an Excel file.
- `--column`: (Optional) Explicitly define the keyword column to bypass dynamic resolution.
- `--output-dir`: (Optional) Directory to save all artifacts (default: `output`).

## Example

### Input (`demo_dataset.csv`)
| Keyword | Search Volume |
|---------|---------------|
| ThinkPad X1 Carbon | 12500 |
| Wedding Dress | 75000 |

### Output
The pipeline determines that "ThinkPad X1 Carbon" matches Lenovo's deterministic product families (`Relevant = True`), while "Wedding Dress" is rejected by the AI classification engine (`Relevant = False`).

## Output Files

All outputs are saved to a timestamped folder inside the `output/` directory (e.g., `output/2026-07-22_14-30-00/`).

- **`filtered_keywords.xlsx`**: A business-ready Excel workbook containing final results, visual pipeline summaries, AI decision logs.
- **`filtered_keywords.csv`**: A clean CSV of the final dataset, suitable for BI tool ingestion.
- **`duplicate_keywords.csv`**: (Generated if duplicates found) A list of keywords removed during the deduplication phase.
- **`execution_summary.json`**: High-level execution metrics (Rows Read, AI Reduction %, Final Runtime).
- **`pipeline_metrics.json`**: Detailed telemetry on AI token usage, fallback activations, and match counts.
- **`stage_metrics.json`**: Execution durations for every stage in the pipeline (Loader, Validator, Preprocessor, etc.).

## Cache

To reduce redundant website crawling and expensive LLM calls, the Business Context Engine leverages a disk cache.

- **Location**: `cache/business_profiles/`
- **How it works**: Profiles are cached using the key `{company}_{website}.json`. If a pipeline is run against `Lenovo` and `www.lenovo.com` twice in 24 hours, the second run bypasses the crawler and LLM enrichment completely.
- **How to clear it**: Simply delete the contents of the `cache/` directory or run `rm -rf cache/*`.

## Testing

The project uses `pytest` for all unit and integration testing.

```bash
# Run all tests
python -m pytest tests/ -v

# Run only integration tests
python -m pytest tests/integration/ -v
```

## Troubleshooting

- **Missing API key**: Ensure `.env` is created and `GOOGLE_GEMINI_API_KEY_1` is populated. If you lack keys, set `AI_PROVIDER=mock` in `.env` for testing.
- **Website unavailable**: If the crawler hits a 403/404 on the target website, the pipeline will issue a warning and gracefully degrade, utilizing only the provided CLI arguments to build a minimal Business Profile.
- **Empty dataset**: Ensure your CSV/Excel file is formatted correctly. The pipeline will automatically attempt to find the keyword column via fuzzy matching, but if it fails, pass `--column YourColumnName`.
- **Rate limits (429)**: The pipeline automatically rotates through Gemini keys. If all fail, it delegates to OpenRouter. Ensure multiple keys are populated in your `.env` for large datasets.
