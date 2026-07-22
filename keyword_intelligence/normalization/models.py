"""Data models and configuration schemas for Keyword Normalization."""

from pydantic import BaseModel, Field


class NormalizationConfig(BaseModel):
    """Configuration settings for the normalization module."""

    # 1. Case
    enable_lowercase: bool = Field(
        default=True, description="Convert text to lowercase."
    )
    # 2. Whitespace
    enable_trim_whitespace: bool = Field(
        default=True, description="Remove leading and trailing whitespaces."
    )
    enable_remove_repeated_spaces: bool = Field(
        default=True, description="Condense multiple spaces into a single space."
    )
    # 3. Unicode
    enable_unicode: bool = Field(
        default=True, description="Normalize unicode and strip invisible chars."
    )
    # 4. Punctuation
    enable_normalize_punctuation: bool = Field(
        default=True, description="Convert common punctuation to spaces."
    )
    # 5. Dictionary
    enable_abbreviation_expansion: bool = Field(
        default=True, description="Expand common abbreviations."
    )
    dictionary_path: str | None = Field(
        default=None, description="Path to external JSON dictionary."
    )
    # 6. Product Token
    enable_product_token: bool = Field(
        default=True,
        description="Normalize product formats (ThinkPad-T14 -> thinkpad t14).",
    )
    # 7. Unit
    enable_unit: bool = Field(
        default=True, description="Collapse spaces before units (2 tb -> 2tb)."
    )
    # 8. Company Dictionary
    enable_company_dictionary: bool = Field(
        default=False, description="Apply company specific dictionary mappings."
    )
    company_dictionary_path: str | None = Field(
        default=None, description="Path to external company JSON dictionary."
    )
    # 9. Lemmatization
    enable_lemmatization: bool = Field(
        default=False, description="Apply lightweight regex stemming."
    )
    # 10. Numeric
    enable_numeric: bool = Field(
        default=True, description="Strip leading zeros from standalone numbers."
    )
    # 11. Stop Words
    enable_stopwords: bool = Field(
        default=False, description="Remove configurable marketing fluff words."
    )
    # 12. Token Order
    enable_token_sorting: bool = Field(
        default=False,
        description="Sort tokens alphabetically. Disabled by default because sorting tokens can introduce false positives and change search intent.",
    )

    @classmethod
    def from_settings(cls, settings) -> "NormalizationConfig":
        """Create config from application settings, allowing overrides."""
        return cls(
            enable_lowercase=getattr(settings, "enable_lowercase", True),
            enable_trim_whitespace=getattr(settings, "enable_trim_whitespace", True),
            enable_remove_repeated_spaces=getattr(
                settings, "enable_normalize_spaces", True
            ),
            enable_unicode=getattr(settings, "enable_unicode", True),
            enable_normalize_punctuation=getattr(
                settings, "enable_normalize_punctuation", True
            ),
            enable_abbreviation_expansion=getattr(
                settings, "enable_abbreviation_expansion", True
            ),
            dictionary_path=getattr(settings, "dictionary_path", None),
            enable_product_token=getattr(settings, "enable_product_token", True),
            enable_unit=getattr(settings, "enable_unit", True),
            enable_company_dictionary=getattr(
                settings, "enable_company_dictionary", False
            ),
            company_dictionary_path=getattr(settings, "company_dictionary_path", None),
            enable_lemmatization=getattr(settings, "enable_lemmatization", False),
            enable_numeric=getattr(settings, "enable_numeric", True),
            enable_stopwords=getattr(settings, "enable_stopwords", False),
            enable_token_sorting=getattr(settings, "enable_token_sorting", False),
        )


class NormalizationMetrics(BaseModel):
    """Tracks observability metrics for the normalization pipeline."""

    total_processed: int = 0
    total_modified: int = 0
    modifications_per_strategy: dict[str, int] = Field(default_factory=dict)

    def add_strategy_modifications(self, strategy_name: str, count: int) -> None:
        """Add the number of modifications performed by a specific strategy."""
        self.modifications_per_strategy[strategy_name] = count


from dataclasses import dataclass

import pandas as pd


@dataclass
class NormalizationResult:
    """The final result of the normalization engine."""

    normalized_series: pd.Series
    trace_series: pd.Series
    metrics: NormalizationMetrics
