"""Unit tests for the data ingestion pipeline stages."""

import pandas as pd
import pytest

from keyword_intelligence.core.exceptions import (
    DataSourceError,
    SchemaValidationError,
    UnsupportedFileExtensionError,
)
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stages.loader import LoaderStage
from keyword_intelligence.pipeline.stages.preprocessor import PreprocessorStage
from keyword_intelligence.pipeline.stages.validator import ValidatorStage


class TestLoaderStage:
    """Tests for the LoaderStage."""

    def test_load_valid_csv(self, settings):
        """Test loading a valid UTF-8 CSV."""
        context = PipelineContext(settings)
        stage = LoaderStage("tests/fixtures/valid.csv")
        context = stage.execute(context)

        assert context.has_data
        df = context.data
        assert len(df) == 3
        assert "Keyword" in df.columns
        assert df.iloc[0]["Keyword"] == "seo optimization"

        # Check dataset metadata
        assert context.dataset_metadata.file_name == "valid.csv"
        assert context.dataset_metadata.checksum != ""
        assert context.dataset_metadata.total_rows == 3
        assert context.dataset_metadata.total_columns == 3

    def test_invalid_extension(self, settings):
        """Test that invalid extensions raise an error."""
        context = PipelineContext(settings)
        stage = LoaderStage("tests/fixtures/invalid_extension.txt")
        with pytest.raises(UnsupportedFileExtensionError):
            stage.execute(context)

    def test_file_not_found(self, settings):
        """Test that missing files raise an error."""
        context = PipelineContext(settings)
        stage = LoaderStage("tests/fixtures/does_not_exist.csv")
        with pytest.raises(DataSourceError, match="File not found"):
            stage.execute(context)


class TestValidatorStage:
    """Tests for the ValidatorStage."""

    def test_valid_schema_aliases(self, settings):
        """Test that valid aliases are correctly mapped to canonical names."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame(
            {
                "Search Keyword ": ["seo"],
                "Search Volume": [100],
                "cost per click": [1.5],
                "UNKNOWN_COL": ["drop_me"],
            }
        )

        stage = ValidatorStage()
        context = stage.execute(context)

        df = context.data
        assert list(df.columns) == ["keyword", "volume", "cpc"]

        # Unknown col dropped should raise a warning
        assert len(context.warnings) == 1
        assert context.warnings[0].code == "UNMAPPED_COLUMNS_DROPPED"

    def test_missing_keyword_column(self, settings):
        """Test that missing the keyword column raises an error."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame({"volume": [100], "cpc": [1.5]})

        stage = ValidatorStage()
        with pytest.raises(SchemaValidationError, match="Required column 'keyword'"):
            stage.execute(context)


class TestPreprocessorStage:
    """Tests for the PreprocessorStage."""

    def test_text_normalization(self, settings):
        """Test lowercasing and whitespace trimming."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame(
            {
                "keyword": [
                    "  SEO optimization  ",
                    "Content   Marketing",
                    "DIGITAL",
                    "   ",
                ]
            }
        )

        stage = PreprocessorStage()
        context = stage.execute(context)

        df = context.data
        keywords = df["keyword"].tolist()

        assert keywords[0] == "seo optimization"
        assert keywords[1] == "content marketing"
        assert keywords[2] == "digital"
        assert len(df) == 3

    def test_configuration_flags(self, settings):
        """Test disabling preprocessing via configuration flags."""
        settings.enable_lowercase = False
        settings.enable_trim_whitespace = False
        settings.enable_normalize_spaces = False

        context = PipelineContext(settings)
        context.data = pd.DataFrame({"keyword": ["  SEO optimization  "]})

        stage = PreprocessorStage()
        context = stage.execute(context)

        df = context.data
        keywords = df["keyword"].tolist()

        # Since lowercasing and trimming are disabled, it remains unchanged
        assert keywords[0] == "  SEO optimization  "
