"""End-to-end integration tests for the Keyword Intelligence Pipeline."""

import pytest

from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.models.pipeline import PipelineConfig
from keyword_intelligence.pipeline.pipeline import Pipeline


@pytest.fixture(autouse=True)
def init_app():
    bootstrap()


def test_production_integration_end_to_end():
    """Verify that the pipeline correctly processes known Lenovo products deterministically."""

    # 1. Create a mocked input file in memory
    test_keywords = [
        "ThinkPad X1 Carbon",
        "Legion 5",
        "Yoga 9i",
        "IdeaPad Slim",
        "ThinkBook",
        "Docking Station",
        "Laptop Battery",
        "Gaming Laptop",
        "Running Shoes",
        "Diamond Rings",
        "Baby Food",
    ]

    csv_content = "keyword\n" + "\n".join(test_keywords)
    csv_bytes = csv_content.encode("utf-8")

    # 2. Run Pipeline
    pipeline = Pipeline(
        config=PipelineConfig(
            enable_validation=True,
            enable_preprocessing=True,
            enable_normalization=True,
            enable_duplicate_detection=True,
            enable_business_context=True,
            enable_decision_engine=True,
            enable_ai=True,
        )
    )

    result, context = pipeline.run(
        input_file=csv_bytes,
        file_name="test_dataset.csv",
        company_name="Lenovo",
        website="https://www.lenovo.com/us",
    )

    # 3. Assertions
    assert result.success is True
    df = context.data
    assert not df.empty

    # Check that not everything defaulted to irrelevant
    assert not (df["relevant"] == False).all()

    # Verify specific classifications
    thinkpad_row = df[
        df["keyword"].str.contains("ThinkPad X1", case=False, na=False)
    ].iloc[0]
    assert thinkpad_row["relevant"] == True
    assert thinkpad_row["classification_stage"] == "Decision Engine"
    assert thinkpad_row["processing_method"] == "Deterministic"
    assert thinkpad_row["brand"].lower() == "lenovo"
    assert thinkpad_row["relevance_score"] >= 0.85

    running_shoes_row = df[
        df["keyword"].str.contains("Running Shoes", case=False, na=False)
    ].iloc[0]
    assert running_shoes_row["relevant"] == False
