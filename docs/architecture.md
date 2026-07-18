# Architecture

> System architecture documentation for the Keyword Intelligence Pipeline.

## Package Diagram

```mermaid
graph TD
    APP["app.py<br/>(Streamlit Entrypoint)"]

    subgraph keyword_intelligence
        CONFIG["config/<br/>Settings, Logging"]
        CORE["core/<br/>Logger, Exceptions"]
        MODELS["models/<br/>Data Models"]
        SERVICES["services/<br/>External Integrations"]
        PIPELINE["pipeline/<br/>Orchestration"]
        UTILS["utils/<br/>Helpers"]
        UI["ui/<br/>Streamlit Pages"]
    end

    APP --> UI
    APP --> CONFIG
    UI --> CONFIG
    UI --> CORE
    PIPELINE --> CONFIG
    PIPELINE --> CORE
    PIPELINE --> SERVICES
    PIPELINE --> MODELS
    SERVICES --> CONFIG
    SERVICES --> CORE
    SERVICES --> MODELS
    MODELS --> CORE
    CORE --> CONFIG
```

## Layer Responsibilities

| Layer | Package | Responsibility | Depends On |
|---|---|---|---|
| **Presentation** | `ui/` | Streamlit page rendering, user interaction | config, core, models |
| **Orchestration** | `pipeline/` | Pipeline stage execution, context management | config, core, services, models |
| **Service** | `services/` | External API integrations (LLM, search, DB) | config, core, models |
| **Domain** | `models/` | Pydantic data models, validation | core |
| **Infrastructure** | `core/` | Logger factory, exception hierarchy | config |
| **Configuration** | `config/` | Settings, logging config | *(none — leaf dependency)* |
| **Utilities** | `utils/` | Stateless helper functions | *(none — leaf dependency)* |

## Dependency Rules

1. **Config and Utils are leaf dependencies** — they depend on nothing internal.
2. **Core depends only on Config** — logger and exceptions may reference settings.
3. **Models depend on Core** — data models may use base exceptions.
4. **Services depend on Config, Core, and Models** — never on Pipeline or UI.
5. **Pipeline depends on everything except UI** — orchestrates services and models.
6. **UI depends on everything except Pipeline internals** — renders data, delegates to pipeline.
7. **No circular dependencies** — dependency graph is a DAG.

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Pipeline as Pipeline Engine
    participant Service as LLM Service
    participant Model as Data Models

    User->>UI: Submit keywords
    UI->>Pipeline: Create PipelineContext
    Pipeline->>Service: Request analysis
    Service->>Service: Call LLM API
    Service->>Model: Parse response into models
    Model-->>Pipeline: Validated data
    Pipeline-->>UI: Pipeline results
    UI-->>User: Render dashboard
```

## Dependency Injection Pattern

The application uses **constructor injection** for all service dependencies:

```
Settings (singleton)
    └── injected into → BaseService.__init__(settings)
        └── injected into → PipelineContext(settings, services)
            └── passed to → Stage.execute(context)
```

### How It Works

1. **Settings** is created once via `get_settings()` (cached singleton).
2. **Services** receive `Settings` in their constructor — they never read `os.environ`.
3. **PipelineContext** carries settings + initialized services through the pipeline.
4. **Stages** receive the context and access dependencies through it.

### Benefits

- **Testability**: Mock `Settings` or inject test doubles for any service.
- **Explicitness**: Every dependency is visible in the constructor signature.
- **No globals**: No module-level singletons beyond the `Settings` cache.

## Future LLM Provider Interface

> **Status**: Documented design — implementation deferred to Phase 2.

### Interface Design

```python
class BaseLLMProvider(BaseService):
    """Abstract interface for LLM provider integrations."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a text completion."""

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider connectivity and credentials."""
```

### Provider Implementations (Phase 2+)

| Provider | Class | Model Examples |
|---|---|---|
| Google | `GoogleLLMProvider` | gemini-2.5-flash, gemini-2.5-pro |
| OpenAI | `OpenAILLMProvider` | gpt-4o, gpt-4o-mini |
| Anthropic | `AnthropicLLMProvider` | claude-sonnet-4, claude-haiku |

### Registration Pattern

```python
# In pipeline setup (Phase 2+)
provider = GoogleLLMProvider(settings)
await provider.initialize()
context.register_service("llm", provider)

# In pipeline stages
llm = context.get_service("llm", BaseLLMProvider)
result = await llm.generate(prompt)
```

### Provider Selection

The provider is selected via the `AI_PROVIDER` environment variable:

```
AI_PROVIDER=google → GoogleLLMProvider
AI_PROVIDER=openai → OpenAILLMProvider
AI_PROVIDER=anthropic → AnthropicLLMProvider
```

A factory function resolves the provider class from the string identifier, keeping the pipeline code provider-agnostic.
