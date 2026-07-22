"""Integration tests for Pipeline Observability and Verification."""

import json

import pandas as pd
import pytest

from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.models import PipelineConfig
from keyword_intelligence.pipeline.pipeline import Pipeline


@pytest.fixture(scope="module", autouse=True)
def init_container():
    """Ensure the container is bootstrapped."""
    bootstrap()


@pytest.fixture
def mock_dataset(tmp_path):
    """Create a mock CSV dataset."""
    df = pd.DataFrame(
        {
            "keyword": ["lenovo laptop", "apple mac", "mens shirt", "cool gadget"],
            "search_volume": [1000, 500, 200, 100],
        }
    )
    file_path = tmp_path / "test_data.csv"
    df.to_csv(file_path, index=False)
    return file_path


def test_successful_pipeline_observability(mock_dataset, tmp_path):
    """Test that a successful pipeline run generates all expected artifacts."""

    config = PipelineConfig(
        enable_validation=True,
        enable_preprocessing=True,
        enable_normalization=True,
        enable_duplicate_detection=True,
        enable_business_context=True,
        enable_decision_engine=True,
        enable_ai=False,
        report_directory=str(tmp_path / "reports"),
    )

    pipeline = Pipeline(config=config)
    result, context = pipeline.run(mock_dataset, "test_data.csv", "Lenovo")

    assert result.success is True
    assert result.overall_status == "SUCCESS"
    assert result.execution_summary["status"] == "SUCCESS"
    assert "run_id" in result.execution_summary

    run_id = result.execution_summary["run_id"]
    output_dir = tmp_path / "reports" / run_id

    assert output_dir.exists()
    assert (output_dir / "pipeline.log").exists()
    assert (output_dir / "filtered_keywords.csv").exists()
    assert (output_dir / "execution_summary.json").exists()
    assert (output_dir / "pipeline_metrics.json").exists()
    assert (output_dir / "stage_metrics.json").exists()

    with open(output_dir / "execution_summary.json") as f:
        summary = json.load(f)
        assert summary["rows_processed"] == 4
        assert "decisions" in summary

    with open(output_dir / "pipeline.log") as f:
        log_content = f.read()
        assert "Starting pipeline execution" in log_content
        assert "✓ Completed" in log_content


def test_pipeline_failure_handling(tmp_path):
    """Test that a pipeline failure gracefully halts and persists artifacts."""

    config = PipelineConfig(
        enable_validation=True, report_directory=str(tmp_path / "reports_failed")
    )

    # Pass a non-existent file to force a failure in LoaderStage
    pipeline = Pipeline(config=config)

    # It should not raise an exception to the caller, it should return gracefully with success=False
    result, context = pipeline.run("does_not_exist.csv", "does_not_exist.csv")

    assert result.success is False
    assert result.overall_status == "FAILED"
    assert len(result.errors) > 0
    assert result.execution_summary["status"] == "FAILED"

    run_id = result.execution_summary["run_id"]
    output_dir = tmp_path / "reports_failed" / run_id

    assert output_dir.exists()
    assert (output_dir / "pipeline.log").exists()
    assert (output_dir / "execution_summary.json").exists()
    assert (output_dir / "pipeline_metrics.json").exists()

    # Ensure the error was logged
    with open(output_dir / "pipeline.log") as f:
        log_content = f.read()
        assert (
            "CRITICAL_FAILURE" in log_content
            or "Pipeline execution failed critically" in log_content
        )
