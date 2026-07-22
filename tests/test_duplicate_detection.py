"""Unit tests for the Duplicate Detection Engine and strategies."""

import pandas as pd
import pytest

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.duplicate_detection.canonicalization import (
    CanonicalizationService,
)
from keyword_intelligence.duplicate_detection.config import DuplicateDetectionConfig
from keyword_intelligence.duplicate_detection.engine import DuplicateDetectionEngine
from keyword_intelligence.duplicate_detection.models import DuplicateCandidate
from keyword_intelligence.pipeline.context import PipelineContext


@pytest.fixture
def engine():
    settings = Settings()
    return DuplicateDetectionEngine(settings)


@pytest.fixture
def sample_context():
    df = pd.DataFrame(
        {
            "keyword": [
                "seo services",
                "seo services",  # exact duplicate
                "SEO  Services",  # normalized duplicate (spaces inside, but leading/trailing stripped like Preprocessor does)
                "seoo services",  # fuzzy duplicate
                "content marketing",  # distinct
            ]
        }
    )
    settings = Settings()
    context = PipelineContext(settings)
    context.data = df
    return context


def test_exact_strategy(engine, sample_context):
    strategy = engine.registry.get_strategies()[0]
    assert strategy.strategy_name == "ExactMatch"

    candidates = strategy.detect(sample_context, set())
    assert len(candidates) >= 1
    assert any(c.match_type == "exact" for c in candidates)


def test_normalized_strategy(engine, sample_context):
    strategy = engine.registry.get_strategies()[1]
    assert strategy.strategy_name == "NormalizedMatch"

    candidates = strategy.detect(sample_context, set())
    # Should catch " SEO  Services " vs "seo services"
    assert any(c.match_type == "normalized" for c in candidates)


def test_fuzzy_strategy(engine, sample_context):
    strategy = engine.registry.get_strategies()[2]
    assert strategy.strategy_name == "FuzzyMatch"

    # Needs a threshold that allows "seoo services" to match "seo services"
    engine.config.fuzzy_threshold = 85.0

    candidates = strategy.detect(sample_context, set())
    assert any(c.match_type == "fuzzy" for c in candidates)


def test_engine_process_end_to_end(engine, sample_context):
    result = engine.process(sample_context)

    # Expect 1 duplicate group containing the canonical 'seo services' and its duplicates
    assert len(result.duplicate_groups) == 1
    group = result.duplicate_groups[0]

    assert (
        len(group.duplicates) == 2
    )  # normalized, fuzzy (exact matches are dropped from dataframe but don't add new nodes to the string-based graph)
    assert "content marketing" not in group.duplicates

    # Pipeline preserves all rows, but marks duplicates in 'status'
    assert len(sample_context.data) == 5
    assert (sample_context.data["status"] == "ACTIVE").sum() == 2
    assert (sample_context.data["status"] == "DUPLICATE").sum() == 3
    assert sample_context.data["keyword"].tolist() == [
        "seo services",
        "seo services",
        "SEO  Services",
        "seoo services",
        "content marketing",
    ]


def test_canonicalization_service():
    config = DuplicateDetectionConfig()
    service = CanonicalizationService(config)

    candidates = [
        DuplicateCandidate(
            original_keyword="a",
            matched_keyword="b",
            matched_by_strategy="Test",
            confidence=95.0,
            match_type="test",
            explanation="",
        ),
        DuplicateCandidate(
            original_keyword="b",
            matched_keyword="c",
            matched_by_strategy="Test",
            confidence=90.0,
            match_type="test",
            explanation="",
        ),
    ]

    # Graph should build connected component {a, b, c} and choose canonical = "a" (length tie breaker uses arbitrary or first, "a" is fine)
    groups = service.process_candidates(candidates, None)

    assert len(groups) == 1
    assert len(groups[0].duplicates) == 2
