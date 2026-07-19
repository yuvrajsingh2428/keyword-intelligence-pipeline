"""Unit tests for the Search Volume Engine."""

import time

import pandas as pd
import pytest

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.search_volume.engine import SearchVolumeEngine
from keyword_intelligence.search_volume.providers.mock import MockProvider
from keyword_intelligence.search_volume.providers.placeholder_google_ads import (
    GoogleAdsProvider,
)
from keyword_intelligence.search_volume.registry import (
    ProviderRegistry,
    ProviderResolver,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(search_volume_provider="mock", search_volume_batch_size=500)


@pytest.fixture
def registry() -> ProviderRegistry:
    r = ProviderRegistry()
    r.register(MockProvider())
    r.register(GoogleAdsProvider())
    return r


@pytest.fixture
def engine(settings: Settings, registry: ProviderRegistry) -> SearchVolumeEngine:
    return SearchVolumeEngine(settings=settings, registry=registry)


def test_provider_registry_and_resolver(registry: ProviderRegistry) -> None:
    resolver = ProviderResolver(registry)

    provider = resolver.resolve("mock")
    assert provider.provider_name == "mock"
    assert provider.capabilities.max_batch_size == 1000

    provider_ads = resolver.resolve("google_ads")
    assert provider_ads.provider_name == "google_ads"

    with pytest.raises(ValueError, match="not found"):
        resolver.resolve("invalid_provider")


def test_oversized_batch_splitting(
    engine: SearchVolumeEngine, settings: Settings
) -> None:
    # MockProvider max_batch_size is 1000.
    # If we set configured batch size to 2000, engine should constrain to 1000.
    settings.search_volume_batch_size = 2000
    engine.config.batch_size = 2000

    # Generate 1500 keywords
    df = pd.DataFrame({"keyword": [f"kw_{i}" for i in range(1500)]})
    context = PipelineContext(settings)
    context.data = df

    result = engine.process(context)

    # Should have split into 2 batches (1000 and 500)
    assert result.statistics.batches_processed == 2
    assert result.statistics.total_keywords == 1500
    assert result.statistics.resolved_keywords == 1500
    assert result.statistics.cache_misses == 1500
    assert result.statistics.cache_hits == 0


def test_cache_hits(engine: SearchVolumeEngine, settings: Settings) -> None:
    df = pd.DataFrame({"keyword": ["apple", "banana"]})
    context = PipelineContext(settings)
    context.data = df

    # Run once to populate cache
    result1 = engine.process(context)
    assert result1.statistics.cache_misses == 2
    assert result1.statistics.cache_hits == 0

    # Run again with same context data
    result2 = engine.process(context)
    assert result2.statistics.cache_misses == 0
    assert result2.statistics.cache_hits == 2
    assert result2.statistics.batches_processed == 0  # No provider calls


def test_deterministic_mock_output(registry: ProviderRegistry) -> None:
    resolver = ProviderResolver(registry)
    provider = resolver.resolve("mock")

    # Fetch twice
    res1 = provider.fetch(["seo tools", "python course"])
    res2 = provider.fetch(["seo tools", "python course"])

    # Ensure they are identical
    assert res1["seo tools"].monthly_volume == res2["seo tools"].monthly_volume
    assert res1["seo tools"].competition == res2["seo tools"].competition
    assert res1["seo tools"].cpc == res2["seo tools"].cpc

    # Ensure they are within expected ranges
    vol = res1["seo tools"].monthly_volume
    assert 10 <= vol <= 500000

    cpc = res1["seo tools"].cpc
    assert 0.05 <= cpc <= 50.00

    comp = res1["seo tools"].competition
    assert comp in ("LOW", "MEDIUM", "HIGH")


def test_engine_updates_dataframe(
    engine: SearchVolumeEngine, settings: Settings
) -> None:
    df = pd.DataFrame({"keyword": ["apple"]})
    context = PipelineContext(settings)
    context.data = df

    engine.process(context)

    assert "search_volume" in context.data.columns
    assert "competition" in context.data.columns
    assert "cpc" in context.data.columns

    assert not pd.isna(context.data["search_volume"].iloc[0])


def test_engine_50k_benchmark(settings: Settings, registry: ProviderRegistry) -> None:
    """Benchmark search volume engine with 50,000 keywords."""
    settings.search_volume_batch_size = 1000
    engine = SearchVolumeEngine(settings=settings, registry=registry)

    # Generate 50k unique keywords
    df = pd.DataFrame({"keyword": [f"synthetic kw {i}" for i in range(50000)]})
    context = PipelineContext(settings)
    context.data = df

    start_time = time.perf_counter()
    result = engine.process(context)
    duration = time.perf_counter() - start_time

    # Assert processed efficiently
    # 50k keywords / 1000 batch size = 50 batches
    # MockProvider sleeps 5ms per batch -> 250ms total sleep time.
    # Total time should be well under 5 seconds.
    assert duration < 5.0, f"Benchmark took too long: {duration:.2f}s"
    assert result.statistics.batches_processed == 50
    assert result.statistics.resolved_keywords == 50000
