# Pipeline Execution Architecture

The Keyword Intelligence Pipeline has been refactored to cleanly decouple its core execution engine from user interfaces. The pipeline can now be triggered from the CLI, the Streamlit UI, a REST API, or automated scheduled jobs, with all interfaces relying on the exact same execution logic.

## Architecture

```text
project/
│
├── keyword_intelligence/
│   ├── pipeline/
│   │   ├── pipeline.py          # Universal Pipeline facade
│   │   ├── orchestrator.py      # Core stage orchestrator
│   │   └── context.py           # In-memory data payload
│   │
│   ├── interfaces/
│   │   ├── cli_runner.py        # CLI adapter and stdout formatting
│   │   ├── streamlit_runner.py  # Streamlit state and UI integration
│   │   └── api_runner.py        # REST API integration stub
│   │
│   └── models/
│       └── pipeline.py          # Contains PipelineResult schema
│
└── run_pipeline.py              # Root script for CLI execution
```

## How It Works

1. **`Pipeline`**: The `keyword_intelligence.pipeline.pipeline.Pipeline` class is the central orchestrator entry point. It handles registering all internal stages (Validation, Preprocessing, Normalization, Duplicate Detection, etc.) and exposes a simple `.run()` method.
2. **`PipelineResult`**: The execution outputs a unified `PipelineResult` object, containing the original dataframe, processed dataframe, normalization metrics, duplicate groups, and stage execution timings.
3. **`Runners`**: Interfaces adapt their environments to the Pipeline. 
   - `CliRunner` injects an event listener to stream real-time execution speeds to the console.
   - `StreamlitRunner` injects Streamlit state tracking and bridges the UI to the backend engine.

## Execution

### Command Line (CLI)

You can execute the pipeline directly from your terminal.

```bash
python run_pipeline.py path/to/dataset.csv \
  --company "Lenovo" \
  --website "lenovo.com" \
  --output-dir "output"
```

The runner will output the sequence in the terminal:
```text
------------------------------------------------
Running Validation...
✓ Completed (0.12 sec)

Running Preprocessing...
✓ Completed (0.04 sec)
...
```

Outputs will be saved in the `output/` directory (or your specified path).

### Streamlit UI

The Streamlit UI runs exactly the same pipeline.
```bash
streamlit run app.py
```
Inside `app.py`, the `StreamlitRunner` handles bridging the Streamlit `st.session_state` to the `Pipeline.run()` execution block, generating reports in memory for immediate downloading.

### API & Schedulers (Future)

To integrate a future API, update `interfaces/api_runner.py` to map incoming JSON payloads to `Pipeline.run()`, and serialize the `PipelineResult.execution_summary` as JSON responses. Scheduled jobs can directly invoke the `CliRunner` or write a minimal script instantiating `Pipeline`.
