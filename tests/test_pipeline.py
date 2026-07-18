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
        stage.execute(context)

        assert context.has_data
        df = context.data
        assert len(df) == 3
        assert "Keyword" in df.columns
        assert df.iloc[0]["Keyword"] == "seo optimization"

    def test_load_valid_xlsx(self, settings):
        """Test loading a valid Excel file."""
        context = PipelineContext(settings)
        stage = LoaderStage("tests/fixtures/valid.xlsx")
        stage.execute(context)

        assert context.has_data
        df = context.data
        assert len(df) == 3
        assert "Keyword" in df.columns

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

    def test_unicode_csv(self, settings):
        """Test loading a CSV with unicode characters."""
        context = PipelineContext(settings)
        stage = LoaderStage("tests/fixtures/unicode.csv")
        stage.execute(context)

        assert context.has_data
        df = context.data
        assert len(df) == 3
        assert "Search Keyword" in df.columns
        assert df.iloc[0]["Search Keyword"] == "optimización seo ✨"


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
        stage.execute(context)

        df = context.data
        # Check columns were renamed
        assert list(df.columns) == ["keyword", "volume", "cpc"]

        # Check metadata
        result = context.metadata["validation_result"]
        assert result.success is True
        assert result.renamed_columns["search keyword"] == "keyword"

    def test_missing_keyword_column(self, settings):
        """Test that missing the keyword column raises an error."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame({"volume": [100], "cpc": [1.5]})

        stage = ValidatorStage()
        with pytest.raises(SchemaValidationError, match="Required column 'keyword'"):
            stage.execute(context)

    def test_drops_empty_rows(self, settings):
        """Test that completely empty rows are dropped."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame(
            {"keyword": ["seo", None, "content"], "volume": [100, None, 200]}
        )

        stage = ValidatorStage()
        stage.execute(context)

        df = context.data
        assert len(df) == 2
        result = context.metadata["validation_result"]
        assert result.dropped_rows == 1


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
        stage.execute(context)

        df = context.data
        keywords = df["keyword"].tolist()

        # Should be lowercased, trimmed, multiple spaces collapsed
        assert keywords[0] == "seo optimization"
        assert keywords[1] == "content marketing"
        assert keywords[2] == "digital"

        # The 4th row was empty spaces, it should be dropped
        assert len(df) == 3

    def test_duplicate_dropping(self, settings):
        """Test that exact duplicates are dropped after normalization."""
        context = PipelineContext(settings)
        context.data = pd.DataFrame({"keyword": ["seo", "SEO", " seo ", "content"]})

        stage = PreprocessorStage()
        stage.execute(context)

        df = context.data
        keywords = df["keyword"].tolist()

        assert len(df) == 2
        assert keywords == ["seo", "content"]
