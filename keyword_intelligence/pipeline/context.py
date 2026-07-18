"""Pipeline execution context for the Keyword Intelligence Pipeline.

This module defines the PipelineContext — a runtime container that carries
all dependencies, state, and results through a pipeline execution. It is
the central mechanism for dependency injection and inter-stage communication.

NOTE: This is a **design-only stub** for Phase 1. The class signature and
docstrings document the architectural intent. Implementation will follow
in Phase 2 when the pipeline engine is built.

Architecture Overview:
    The PipelineContext is created once per pipeline run and passed through
    each stage in sequence. Each stage reads its inputs from the context,
    performs its work, and writes its outputs back to the context.

    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
    │  Stage 1 │────▶│  Stage 2 │────▶│  Stage 3 │────▶│  Stage N │
    └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                │                │                │
         └────────────────┴────────────────┴────────────────┘
                                │
                         PipelineContext
                     (shared state container)

Dependency Injection Pattern:
    The PipelineContext acts as a service locator for pipeline stages.
    Instead of each stage constructing its own dependencies, the context
    provides pre-initialized services:

        context.settings     → Application configuration
        context.logger       → Bound logger with pipeline context
        context.services     → Dict of initialized service instances
        context.artifacts    → Dict of stage outputs / intermediate results
        context.metadata     → Pipeline run metadata (ID, timestamps, etc.)

Future LLM Provider Interface:
    The context will carry an LLM provider that implements a standard
    interface, allowing stages to request AI completions without knowing
    which provider (Google, OpenAI, Anthropic) is configured:

        class BaseLLMProvider(ABC):
            async def generate(prompt, **kwargs) -> str
            async def embed(texts) -> list[list[float]]
            async def health_check() -> bool

    The provider is registered in the context at pipeline startup:

        context.services["llm"] = GoogleLLMProvider(settings)
        # or
        context.services["llm"] = OpenAILLMProvider(settings)

    Stages access it generically:

        llm = context.services["llm"]
        result = await llm.generate(prompt)

Example Usage (Phase 2+):
    context = PipelineContext(
        settings=get_settings(),
        pipeline_id="kw-analysis-2024-01-15",
    )
    await context.initialize_services()

    for stage in pipeline.stages:
        await stage.execute(context)

    report = context.artifacts["final_report"]
"""

from __future__ import annotations


class PipelineContext:
    """Runtime container for pipeline execution state.

    Carries dependencies (settings, logger, services), intermediate
    results (artifacts), and execution metadata through the pipeline.
    Created once per pipeline run and shared across all stages.

    This class is a Phase 1 design stub. See module docstring for
    the full architectural design and dependency injection patterns.

    Attributes:
        pipeline_id: Unique identifier for this pipeline run.
        settings: Application configuration instance.
        artifacts: Dictionary of stage outputs keyed by stage name.
        metadata: Pipeline run metadata (timestamps, status, etc.).
    """

    pass  # Implementation deferred to Phase 2
