"""Benchmark test for Duplicate Detection Engine."""

import time

import pandas as pd

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.duplicate_detection.engine import DuplicateDetectionEngine
from keyword_intelligence.pipeline.context import PipelineContext


def generate_synthetic_data(num_rows: int) -> pd.DataFrame:
    """Generate a synthetic dataset with distinct, exact, normalized, and fuzzy duplicates."""
    base_keywords = [
        "seo agency",
        "digital marketing",
        "python programming",
        "content strategy",
        "link building",
    ]

    # We will repeat these, slightly mutating them
    data = []

    # Roughly 20% distinct, 80% duplicates of various types
    for i in range(num_rows):
        base = base_keywords[i % len(base_keywords)]
        if i % 10 == 0:
            data.append(base)  # Exact
        elif i % 10 == 1:
            data.append(base.upper() + "  ")  # Normalized
        elif i % 10 == 2:
            data.append(base + "x")  # Fuzzy
        elif i % 10 == 3:
            data.append(base + str(i))  # Semi-distinct
        else:
            data.append(f"unique keyword {i}")  # Distinct

    return pd.DataFrame({"keyword": data})


def test_engine_50k_benchmark():
    """Benchmark the engine with 50,000 rows to ensure it avoids O(N^2) timeouts."""
    settings = Settings()
    settings.duplicate_max_group_size = 500  # allow larger groups for synthetic

    engine = DuplicateDetectionEngine(settings)

    # Generate 50k rows
    df = generate_synthetic_data(50000)
    context = PipelineContext(settings)
    context.data = df

    start_time = time.perf_counter()
    result = engine.process(context)
    duration = time.perf_counter() - start_time

    # Assert it processes in a reasonable amount of time (e.g., < 15 seconds)
    # The fuzzy grouping strategy should keep this very fast
    assert duration < 15.0, f"Benchmark took too long: {duration:.2f}s"
    assert result.duplicates_removed > 0
    assert result.statistics.total_keywords == 50000
