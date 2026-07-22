"""Unit tests for the Keyword Normalization module."""

import pandas as pd
import pytest

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.normalization.dictionary import NormalizationDictionary
from keyword_intelligence.normalization.engine import NormalizationEngine
from keyword_intelligence.normalization.models import NormalizationConfig
from keyword_intelligence.normalization.strategies import (
    CaseNormalizer,
    CompanyDictionaryNormalizer,
    DictionaryNormalizer,
    LemmatizationNormalizer,
    NumericNormalizer,
    ProductTokenNormalizer,
    PunctuationNormalizer,
    StopWordNormalizer,
    TokenOrderNormalizer,
    UnicodeNormalizer,
    UnitNormalizer,
    WhitespaceNormalizer,
)


@pytest.fixture
def config():
    """Provides a default normalization configuration with everything enabled."""
    return NormalizationConfig(
        enable_lowercase=True,
        enable_trim_whitespace=True,
        enable_remove_repeated_spaces=True,
        enable_unicode=True,
        enable_normalize_punctuation=True,
        enable_abbreviation_expansion=True,
        enable_product_token=True,
        enable_unit=True,
        enable_company_dictionary=True,
        enable_lemmatization=True,
        enable_numeric=True,
        enable_stopwords=True,
        enable_token_sorting=True,
    )


@pytest.fixture
def dictionary():
    """Provides the standard dictionary."""
    d = NormalizationDictionary()
    d._company_mapping = {"lenovo legion": "legion"}
    return d


def test_case_normalizer(config):
    normalizer = CaseNormalizer(config)
    data = pd.Series(["LENOVO LAPTOP"])
    assert normalizer.apply(data).iloc[0] == "lenovo laptop"


def test_whitespace_normalizer(config):
    normalizer = WhitespaceNormalizer(config)
    data = pd.Series(["  gaming    laptop  "])
    assert normalizer.apply(data).iloc[0] == "gaming laptop"


def test_unicode_normalizer(config):
    normalizer = UnicodeNormalizer(config)
    data = pd.Series(["café", "naïve"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "cafe"
    assert result.iloc[1] == "naive"


def test_punctuation_normalizer(config):
    normalizer = PunctuationNormalizer(config)
    data = pd.Series(
        ["gaming-laptop", "gaming/laptop", "gaming_laptop", "gaming.laptop"]
    )
    result = normalizer.apply(data)
    assert (result == "gaming laptop").all()


def test_dictionary_normalizer(config, dictionary):
    normalizer = DictionaryNormalizer(config, dictionary)
    data = pd.Series(["ergo mouse", "buy a tv", "128gb usb stick"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "ergonomic mouse"
    assert result.iloc[1] == "buy a television"
    assert result.iloc[2] == "128gb usb flash drive"


def test_company_dictionary_normalizer(config, dictionary):
    normalizer = CompanyDictionaryNormalizer(config, dictionary)
    data = pd.Series(["buy lenovo legion laptop"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "buy legion laptop"


def test_product_token_normalizer(config):
    normalizer = ProductTokenNormalizer(config)
    data = pd.Series(["thinkpad t14"])
    assert normalizer.apply(data).iloc[0] == "thinkpad t14"


def test_unit_normalizer(config):
    normalizer = UnitNormalizer(config)
    data = pd.Series(["2 tb", "256 gb", "500 gb ssd"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "2tb"
    assert result.iloc[1] == "256gb"
    assert result.iloc[2] == "500gb ssd"


def test_lemmatization_normalizer(config):
    normalizer = LemmatizationNormalizer(config)
    data = pd.Series(["running", "batteries", "monitors", "mice"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "run"
    assert result.iloc[1] == "battery"
    assert result.iloc[2] == "monitor"
    assert result.iloc[3] == "mouse"


def test_numeric_normalizer(config):
    normalizer = NumericNormalizer(config)
    data = pd.Series(["02tb", "0016gb", "t14", "thinkpad t014"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "2tb"
    assert result.iloc[1] == "16gb"
    assert result.iloc[2] == "t14"
    assert result.iloc[3] == "thinkpad t014"


def test_stop_word_normalizer(config):
    normalizer = StopWordNormalizer(config)
    data = pd.Series(["best gaming laptop", "cheap gaming laptop"])
    result = normalizer.apply(data)
    assert result.iloc[0] == "gaming laptop"
    assert result.iloc[1] == "gaming laptop"


def test_token_order_normalizer(config):
    # Setup standard config (where it is disabled by default)
    default_config = NormalizationConfig()
    normalizer = TokenOrderNormalizer(default_config)
    data = pd.Series(["laptop gaming", "gaming laptop"])
    result = normalizer.apply(data)
    # Disabled by default, so order shouldn't change
    assert result.iloc[0] == "laptop gaming"

    # Enable explicitly
    default_config.enable_token_sorting = True
    result_enabled = normalizer.apply(data)
    assert result_enabled.iloc[0] == "gaming laptop"


def test_normalization_engine_integration():
    """Test the facade engine applying all strategies in order based on user prompt examples."""
    settings = Settings()
    # Explicitly enable everything for the integration test
    settings.enable_unicode = True
    settings.enable_lemmatization = True
    settings.enable_stopwords = True
    settings.enable_token_sorting = True
    settings.enable_company_dictionary = True

    engine = NormalizationEngine(settings)
    engine.dictionary._company_mapping = {"lenovo legion": "legion"}

    data = pd.Series(
        [
            "LENOVO LAPTOP",
            "gaming-laptop",
            "gaming    laptop",
            "ergo mouse",
            "USB Stick",
            "mice",
            "batteries",
            "café",
            "ThinkPad-T14",
            "500 GB SSD",
        ]
    )

    res = engine.normalize_series(data)
    result = res.normalized_series

    assert result.iloc[0] == "laptop lenovo"
    assert result.iloc[1] == "gaming laptop"
    assert result.iloc[2] == "gaming laptop"
    assert result.iloc[3] == "ergonomic mouse"
    assert result.iloc[4] == "drive flash usb"
    assert result.iloc[5] == "mouse"
    assert result.iloc[6] == "battery"
    assert result.iloc[7] == "cafe"
    assert result.iloc[8] == "t14 thinkpad"
    assert result.iloc[9] == "500gb ssd"


def test_engine_idempotency():
    """Test that applying normalization twice yields the exact same result as once."""
    settings = Settings()
    engine = NormalizationEngine(settings)
    data = pd.Series(["  Ergo-Mouse  ", "buy a tv!", "02 TB SSD drives"])

    # First pass
    res1 = engine.normalize_series(data)

    # Second pass
    res2 = engine.normalize_series(res1.normalized_series)

    # Output values must be identical
    pd.testing.assert_series_equal(res1.normalized_series, res2.normalized_series)

    # On the second pass, the trace should be empty because no strategies modified the text
    assert (res2.trace_series == "").all()


def test_engine_tracing_and_metrics():
    """Test that traces correctly record only the strategies that modify a keyword."""
    settings = Settings()
    engine = NormalizationEngine(settings)

    data = pd.Series(["Ergo-Mouse", "perfectly normalized keyword"])
    res = engine.normalize_series(data)

    # "Ergo-Mouse" will hit CaseNormalizer ("ergo-mouse"), PunctuationNormalizer ("ergo mouse"), DictionaryNormalizer ("ergonomic mouse")
    trace1 = res.trace_series.iloc[0]
    assert "CaseNormalizer" in trace1
    assert "PunctuationNormalizer" in trace1
    assert "DictionaryNormalizer" in trace1
    assert "WhitespaceNormalizer" not in trace1

    # "perfectly normalized keyword" should hit nothing
    trace2 = res.trace_series.iloc[1]
    assert trace2 == ""

    # Check metrics
    metrics = res.metrics
    assert metrics.total_processed == 2
    assert metrics.total_modified == 1
    assert metrics.modifications_per_strategy["CaseNormalizer"] == 1
