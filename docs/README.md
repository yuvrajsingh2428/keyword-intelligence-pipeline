# Keyword Intelligence Pipeline - Documentation

Welcome to the internal documentation for the Keyword Intelligence Pipeline.

## Architecture (C4 Model)

### System Context

```mermaid
C4Context
  title System Context for Keyword Intelligence Pipeline
  
  Person(analyst, "Marketing Analyst", "Uploads keyword CSV files and downloads reports.")
  
  System(kip, "Keyword Intelligence Pipeline", "Processes, cleans, deduplicates, and classifies SEO keywords.")
  
  System_Ext(google, "Google Ads API", "Provides search volume data.")
  System_Ext(ollama, "Ollama / LLMs", "Provides AI intent classification.")
  
  Rel(analyst, kip, "Uploads CSVs & views dashboard")
  Rel(kip, google, "Fetches search volume")
  Rel(kip, ollama, "Requests AI classification")
```

### Container Diagram

```mermaid
C4Container
  title Container Diagram for Keyword Intelligence Pipeline

  Person(analyst, "Analyst", "User")
  
  Container_Boundary(c1, "Keyword Intelligence Pipeline") {
    Container(ui, "Streamlit Dashboard", "Python, Streamlit", "Provides the UI.")
    Container(orch, "Pipeline Orchestrator", "Python", "Manages the execution flow.")
    Container(engines, "Intelligence Engines", "Python", "Duplicate Detection, Search Volume, AI.")
    Container(plugin, "Plugin Manager", "Python", "Auto-discovers extensions.")
  }
  
  Rel(analyst, ui, "Interacts with")
  Rel(ui, orch, "Triggers via PipelineRunner")
  Rel(orch, engines, "Orchestrates")
  Rel(orch, plugin, "Loads stages from")
```

## Developer Guides
- [Plugin Author Guide](./plugins.md)
- [Troubleshooting](./troubleshooting.md)
