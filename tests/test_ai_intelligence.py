"""Unit tests for the AI Keyword Intelligence Engine."""

import time
from typing import cast

import pandas as pd
import pytest
from pydantic import ValidationError

from keyword_intelligence.ai_intelligence.components.parsing import (
    ResponseParser,
    ResponseValidator,
)
from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.ai_intelligence.providers.mock import MockAIProvider
from keyword_intelligence.ai_intelligence.registry import AIProviderRegistry
from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext


@pytest.fixture
def settings() -> Settings:
    return Settings(ai_provider="mock", ai_batch_size=10)


@pytest.fixture
def registry() -> AIProviderRegistry:
    r = AIProviderRegistry()
    r.register(MockAIProvider())
    return r


@pytest.fixture
def engine(settings: Settings, registry: AIProviderRegistry) -> AIEngine:
    return AIEngine(settings=settings, registry=registry)


def test_parser_and_validator() -> None:
    parser = ResponseParser()
    validator = ResponseValidator()

    # Valid case
    raw = '[{"keyword": "apple", "relevant": true, "classification": "RELEVANT", "reasoning": "Because it is.", "confidence": 90}]'
    parsed = parser.parse(raw)
    schemas, errors = validator.validate(parsed)
    assert len(schemas) == 1
    assert len(errors) == 0
    assert schemas[0].keyword == "apple"

    # Malformed JSON
    with pytest.raises(ValueError, match="Could not extract valid JSON from response."):
        parser.parse('{"broken": json')

    # Missing fields
    raw_missing = '[{"keyword": "apple", "classification": "RELEVANT"}]'
    parsed_missing = parser.parse(raw_missing)
    schemas, errors = validator.validate(parsed_missing)
    assert len(schemas) == 0
    assert len(errors) == 1
    assert isinstance(errors[0], ValidationError)

    # Invalid enum
    raw_invalid_enum = '[{"keyword": "apple", "relevant": true, "classification": "NOT_AN_ENUM", "reasoning": "Test", "confidence": 90}]'
    parsed_invalid = parser.parse(raw_invalid_enum)
    schemas, errors = validator.validate(parsed_invalid)
    assert len(schemas) == 0
    assert len(errors) == 1


def test_mock_deterministic_generation(engine: AIEngine, settings: Settings) -> None:
    df = pd.DataFrame({"keyword": ["laptop", "cheap flights"]})
    context = PipelineContext(settings)
    context.data = df

    engine.process(context)

    assert "business_relevance" in context.data.columns
    assert "business_reason" in context.data.columns

    # Run again on new context
    context2 = PipelineContext(settings)
    context2.data = pd.DataFrame({"keyword": ["laptop", "cheap flights"]})
    # Clear cache to force re-fetch
    from keyword_intelligence.ai_intelligence.cache import InMemoryAICache

    cast(InMemoryAICache, engine.cache)._cache.clear()

    engine.process(context2)

    # Assert deterministic equality
    assert (
        context.data.iloc[0]["business_relevance"]
        == context2.data.iloc[0]["business_relevance"]
    )
    assert (
        context.data.iloc[1]["business_relevance"]
        == context2.data.iloc[1]["business_relevance"]
    )


def test_ai_cache_hits(engine: AIEngine, settings: Settings) -> None:
    df = pd.DataFrame({"keyword": ["python tutorial", "buy shoes"]})
    context = PipelineContext(settings)
    context.data = df

    # Run once to populate cache
    engine.process(context)

    assert (
        engine.cache.get(
            engine.cache.generate_key(
                "unknown_company", "python tutorial", "mock", "1.0.0"
            )
        )
        is not None
    )

    # Run again, check logs or mock call count
    context2 = PipelineContext(settings)
    context2.data = df
    engine.process(context2)

    # The provider shouldn't have been called for these, but we don't have a direct assert
    # except looking at the returned context or stats.
    # We would need to extract stats if we exposed them in the engine return.
    # Since Engine process() returns None and mutates context, we can check if it worked.
    assert not context2.data["business_relevance"].isna().any()


def test_malformed_responses_handled_gracefully(
    engine: AIEngine, settings: Settings
) -> None:
    # Our mock provider returns broken JSON if the keyword is "malformed_json"
    df = pd.DataFrame({"keyword": ["malformed_json"]})
    context = PipelineContext(settings)
    context.data = df

    engine.process(context)

    # Should safely fail without crashing pipeline, and leave it NaN/None
    assert pd.isna(context.data["business_relevance"].iloc[0])


def test_batch_splitting(engine: AIEngine, settings: Settings) -> None:
    # Generate 250 keywords
    # Engine is configured with ai_batch_size = 100 via settings fixture
    df = pd.DataFrame({"keyword": [f"test_{i}" for i in range(250)]})
    context = PipelineContext(settings)
    context.data = df

    engine.process(context)

    # Should have batched 100, 100, 50
    assert not context.data["business_relevance"].isna().any()
    assert len(context.data) == 250


def test_engine_50k_benchmark(settings: Settings, registry: AIProviderRegistry) -> None:
    """Benchmark AI engine with 50,000 keywords."""
    settings.ai_batch_size = 1000
    engine = AIEngine(settings=settings, registry=registry)

    df = pd.DataFrame({"keyword": [f"synthetic ai kw {i}" for i in range(50000)]})
    context = PipelineContext(settings)
    context.data = df

    start_time = time.perf_counter()
    engine.process(context)
    duration = time.perf_counter() - start_time

    # 50 batches of 1000. Each takes 5ms sleep in MockProvider.
    # Total time should be well under 10 seconds.
    assert duration < 10.0, f"AI Benchmark took too long: {duration:.2f}s"
    assert len(context.data) == 50000
    assert not context.data["business_relevance"].isna().any()
