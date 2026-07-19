"""Application bootstrapping and container wiring."""

from __future__ import annotations

from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.business_context.engine import BusinessContextEngine
from keyword_intelligence.config.settings import Settings, get_settings
from keyword_intelligence.core.container import container
from keyword_intelligence.duplicate_detection.engine import DuplicateDetectionEngine
from keyword_intelligence.observability.events import EventBus
from keyword_intelligence.observability.health import HealthAggregator
from keyword_intelligence.observability.metrics import MetricsCollector
from keyword_intelligence.pipeline.orchestrator import PipelineOrchestrator
from keyword_intelligence.pipeline.registry import StageRegistry
from keyword_intelligence.reporting.engine import ReportEngine
from keyword_intelligence.search_volume.engine import SearchVolumeEngine


def bootstrap() -> None:
    """Wire up all dependencies in the IoC container."""
    # 1. Configuration
    settings = get_settings()
    container.register_instance(Settings, settings)

    # 2. Observability
    container.register_instance(EventBus, EventBus())
    container.register_instance(MetricsCollector, MetricsCollector())
    container.register_instance(HealthAggregator, HealthAggregator())

    # 3. Engines
    from keyword_intelligence.ai_intelligence.registry import (
        AIProviderRegistry,
        AIProviderResolver,
    )

    # We need a resolver for the BusinessContextEngine, which uses the same AI infrastructure.
    # The registry is initialized internally in AIEngine, but we can extract it or just instantiate it.
    # Let's register AIProviderRegistry explicitly so it can be shared.
    container.register(
        AIProviderRegistry, lambda: _build_ai_registry(container.resolve(Settings))
    )
    container.register(
        AIProviderResolver,
        lambda: AIProviderResolver(container.resolve(AIProviderRegistry)),
    )

    container.register(
        BusinessContextEngine,
        lambda: BusinessContextEngine(
            container.resolve(Settings), container.resolve(AIProviderResolver)
        ),
    )
    container.register(
        DuplicateDetectionEngine,
        lambda: DuplicateDetectionEngine(container.resolve(Settings)),
    )
    container.register(
        SearchVolumeEngine,
        lambda: SearchVolumeEngine(container.resolve(Settings)),
    )
    container.register(
        AIEngine,
        lambda: AIEngine(
            settings=container.resolve(Settings),
            registry=container.resolve(AIProviderRegistry),
        ),
    )
    container.register(
        ReportEngine,
        lambda: ReportEngine(container.resolve(Settings)),
    )

    # 4. Pipeline
    container.register(
        StageRegistry,
        lambda: StageRegistry(),
    )
    container.register(
        PipelineOrchestrator,
        lambda: PipelineOrchestrator(
            settings=container.resolve(Settings),
            registry=container.resolve(StageRegistry),
        ),
    )


def _build_ai_registry(settings: Settings):
    from loguru import logger

    from keyword_intelligence.ai_intelligence.providers.gemini import GeminiProvider
    from keyword_intelligence.ai_intelligence.providers.mock import MockAIProvider
    from keyword_intelligence.ai_intelligence.providers.ollama import OllamaProvider
    from keyword_intelligence.ai_intelligence.providers.openrouter import (
        OpenRouterProvider,
    )
    from keyword_intelligence.ai_intelligence.registry import AIProviderRegistry

    registry = AIProviderRegistry()

    registry.register(MockAIProvider())
    registry.register(OllamaProvider(settings))

    try:
        openrouter = OpenRouterProvider(settings)
        if openrouter.health_check():
            registry.register(openrouter)
        else:
            logger.warning("OpenRouter health check failed. Skipping registration.")
    except Exception as e:
        logger.warning(f"Could not register OpenRouterProvider: {e}")

    try:
        registry.register(GeminiProvider(settings))
    except ValueError as e:
        logger.warning(f"Could not register GeminiProvider: {e}")

    return registry
