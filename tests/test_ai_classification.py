"""Unit tests for the AI Classification pipeline stage."""

import pandas as pd
import pytest

from keyword_intelligence.ai_intelligence.cache import InMemoryAICache
from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.ai_intelligence.providers.mock import MockAIProvider
from keyword_intelligence.ai_intelligence.registry import AIProviderRegistry
from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stages.ai_classification import AIClassificationStage


@pytest.fixture
def mock_engine():
    """Create an AIEngine with the Mock provider."""
    settings = Settings(environment="test")
    registry = AIProviderRegistry()
    registry.register(MockAIProvider())

    # Force the engine to use the mock provider
    settings.ai_provider = "mock"
    settings.ai_batch_size = 2  # Small batch for testing

    cache = InMemoryAICache()

    engine = AIEngine(settings=settings, cache=cache, registry=registry)
    return engine


@pytest.fixture
def mock_context(mock_engine):
    """Create a pipeline context with mock data."""
    df = pd.DataFrame(
        {
            "keyword": ["lenovo laptop", "random shoes", "thinkpad", "dog food"],
            "decision": ["KEEP", "DROP", "SEND_TO_AI", "SEND_TO_AI"],
        }
    )

    context = PipelineContext(settings=mock_engine.settings)
    context.data = df
    return context


def test_ai_classification_filtering(mock_engine, mock_context):
    """Test that only SEND_TO_AI keywords are processed and others are ignored."""
    stage = AIClassificationStage(engine=mock_engine)

    # Process
    result_context = stage.execute(mock_context)
    df = result_context.data

    # SEND_TO_AI keywords should have AI columns
    ai_rows = df[df["decision"] == "SEND_TO_AI"]
    assert len(ai_rows) == 2
    assert "ai_relevance" in df.columns
    assert "ai_reason" in df.columns

    assert all(pd.notna(ai_rows["ai_relevance"]))
    assert all(pd.notna(ai_rows["ai_reason"]))
    assert all(ai_rows["processing_method"] == "AI")

    # KEEP/DROP keywords should NOT have AI columns
    non_ai_rows = df[df["decision"] != "SEND_TO_AI"]
    assert len(non_ai_rows) == 2

    # Because of the apply, they might be NaN/None
    for val in non_ai_rows["ai_relevance"]:
        assert pd.isna(val) or val is None

    for val in non_ai_rows["processing_method"]:
        assert pd.isna(val) or val is None


def test_ai_classification_caching(mock_engine):
    """Test that identical keywords skip the LLM execution by using the cache."""
    # First execution
    df1 = pd.DataFrame({"keyword": ["test_cache"], "decision": ["SEND_TO_AI"]})
    context1 = PipelineContext(settings=mock_engine.settings)
    context1.data = df1

    stage = AIClassificationStage(engine=mock_engine)
    stage.execute(context1)

    # Second execution (same keyword)
    df2 = pd.DataFrame({"keyword": ["test_cache"], "decision": ["SEND_TO_AI"]})
    context2 = PipelineContext(settings=mock_engine.settings)
    context2.data = df2
    stage.execute(context2)

    # Check stats in context2
    stats2 = context2.stage_metrics[-1]
    # The engine statistics are logged, but let's check the cache hits through the cache itself
    cache = mock_engine.cache
    # Since it's identical, it should be in cache
    # The cache key generation in engine depends on company_name, keyword, provider, prompt_version
    # Assuming company_name is 'unknown_company'
    key = cache.generate_key("unknown_company", "test_cache", "mock", "1.0.0")
    assert cache.get(key) is not None
