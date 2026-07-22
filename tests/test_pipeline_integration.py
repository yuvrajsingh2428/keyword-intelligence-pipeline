"""Integration tests for the unified Pipeline runner."""

import pandas as pd
import pytest

from keyword_intelligence.models import PipelineConfig, PipelineResult
from keyword_intelligence.pipeline.pipeline import Pipeline


@pytest.fixture
def dummy_csv_bytes():
    """Returns bytes of a minimal valid CSV for testing."""
    csv_content = (
        "keyword,search_volume,cpc\n"
        "lenovo laptop,1000,1.5\n"
        "lenovo laptops,800,1.6\n"
        "gaming laptop,5000,2.0\n"
        "cheap tv,200,0.5\n"
    )
    return csv_content.encode("utf-8")


def test_pipeline_end_to_end(dummy_csv_bytes):
    """Test that the pipeline executes all standard stages successfully."""

    pipeline = Pipeline()

    # We pass bytes mimicking a Streamlit upload
    result, context = pipeline.run(
        input_file=dummy_csv_bytes,
        file_name="test_data.csv",
        company_name="Lenovo",
        website="lenovo.com",
        industry="Electronics",
    )

    # Check Result Type
    assert isinstance(result, PipelineResult)
    assert result.success is True
    assert result.overall_status == "SUCCESS"
    assert result.total_rows_processed == 4

    # Check that dataframes exist in context
    assert context.has_data is True
    assert isinstance(context.data, pd.DataFrame)
    assert "normalized_keyword" in context.data.columns

    # Check that stage metrics recorded multiple stages
    stage_names = [s.stage_name for s in result.stage_metrics]
    assert "LOADER" in stage_names
    assert "VALIDATION" in stage_names
    assert "PREPROCESSING" in stage_names
    assert "NORMALIZATION" in stage_names
    assert "DUPLICATE_DETECTION" in stage_names


def test_pipeline_config(dummy_csv_bytes):
    """Test that PipelineConfig properly enables/disables stages."""

    config = PipelineConfig(enable_preprocessing=False, enable_normalization=False)

    pipeline = Pipeline(config=config)
    result, context = pipeline.run(input_file=dummy_csv_bytes)

    stage_names = [s.stage_name for s in result.stage_metrics]
    assert "LOADER" in stage_names
    assert "VALIDATION" in stage_names
    assert "DUPLICATE_DETECTION" in stage_names
    assert "PREPROCESSING" not in stage_names
    assert "NORMALIZATION" not in stage_names


def test_pipeline_invalid_file():
    """Test that pipeline fails gracefully with invalid files."""

    pipeline = Pipeline()

    # Pass invalid bytes
    result, context = pipeline.run(
        input_file=b"this is not a valid dataset", file_name="test_data.txt"
    )

    # It should either fail loader or validator
    assert result.success is False
    assert result.overall_status == "FAILED"
    assert len(result.errors) > 0
