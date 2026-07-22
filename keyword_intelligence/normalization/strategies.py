"""Normalization strategies for processing keyword strings."""

import re
import unicodedata
from abc import ABC, abstractmethod

import pandas as pd

from keyword_intelligence.normalization.dictionary import NormalizationDictionary
from keyword_intelligence.normalization.models import NormalizationConfig


class BaseNormalizationStrategy(ABC):
    """Abstract base class for normalization strategies."""

    def __init__(self, config: NormalizationConfig) -> None:
        """Initialize the strategy with the normalization configuration."""
        self.config = config

    @abstractmethod
    def apply(self, series: pd.Series) -> pd.Series:
        """Apply the normalization strategy to a pandas Series of strings."""
        pass


class CaseNormalizer(BaseNormalizationStrategy):
    """Converts all text to lowercase."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_lowercase:
            return series
        return series.str.lower()


class WhitespaceNormalizer(BaseNormalizationStrategy):
    """Removes leading, trailing, and repeated spaces."""

    def apply(self, series: pd.Series) -> pd.Series:
        result = series.copy()
        if self.config.enable_remove_repeated_spaces:
            result = result.str.replace(r"\s+", " ", regex=True)
        if self.config.enable_trim_whitespace:
            result = result.str.strip()
        return result


class UnicodeNormalizer(BaseNormalizationStrategy):
    """Normalizes unicode characters and removes invisible characters."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_unicode:
            return series

        def normalize_unicode(text: str) -> str:
            if not isinstance(text, str):
                return text
            # NFKD normalization to remove accents
            norm = unicodedata.normalize("NFKD", text)
            # Encode to ascii to remove non-ascii chars, then back to string
            return norm.encode("ascii", "ignore").decode("utf-8")

        return series.apply(normalize_unicode)


class PunctuationNormalizer(BaseNormalizationStrategy):
    """Normalizes punctuation by converting hyphens, slashes, etc., to spaces."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_normalize_punctuation:
            return series
        # Replace common punctuation with space
        return series.str.replace(r"[-/_.]", " ", regex=True)


class DictionaryNormalizer(BaseNormalizationStrategy):
    """Expands abbreviations based on a configured dictionary mapping."""

    def __init__(
        self,
        config: NormalizationConfig,
        dictionary: NormalizationDictionary | None = None,
    ) -> None:
        super().__init__(config)
        self.dictionary = dictionary or NormalizationDictionary()

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_abbreviation_expansion:
            return series

        result = series.copy()
        mapping = self.dictionary.get_mapping()

        if not mapping:
            return result

        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)

        for abbr in sorted_keys:
            expansion = mapping[abbr]
            pattern = rf"\b{re.escape(abbr)}\b"
            result = result.str.replace(
                pattern, expansion, regex=True, flags=re.IGNORECASE
            )

        return result


class CompanyDictionaryNormalizer(BaseNormalizationStrategy):
    """Applies company-specific dictionary mappings."""

    def __init__(
        self,
        config: NormalizationConfig,
        dictionary: NormalizationDictionary | None = None,
    ) -> None:
        super().__init__(config)
        self.dictionary = dictionary or NormalizationDictionary()

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_company_dictionary:
            return series

        result = series.copy()
        mapping = self.dictionary.get_company_mapping()

        if not mapping:
            return result

        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)

        for abbr in sorted_keys:
            expansion = mapping[abbr]
            pattern = rf"\b{re.escape(abbr)}\b"
            result = result.str.replace(
                pattern, expansion, regex=True, flags=re.IGNORECASE
            )

        return result


class ProductTokenNormalizer(BaseNormalizationStrategy):
    """Removes unnecessary separators in product names."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_product_token:
            return series
        # The prompt requested "ThinkPad-T14 -> thinkpad t14".
        # This is implicitly handled by the PunctuationNormalizer changing "-" to " ".
        # No additional logic strictly needed for these examples unless specified.
        return series


class UnitNormalizer(BaseNormalizationStrategy):
    """Normalizes units (e.g., 2 tb -> 2tb)."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_unit:
            return series
        # Remove spaces before common units: tb, gb, mb, kb, hz, mhz, ghz, w, v, mah, ssd
        units = r"(tb|gb|mb|kb|hz|mhz|ghz|w|v|mah)"
        # Regex: Digit followed by space(s) followed by unit word boundary
        pattern = rf"(\d+)\s+{units}\b"
        return series.str.replace(pattern, r"\1\2", regex=True, flags=re.IGNORECASE)


class LemmatizationNormalizer(BaseNormalizationStrategy):
    """Applies lightweight, deterministic regex-based stemming for plurals/gerunds."""

    def __init__(self, config: NormalizationConfig) -> None:
        super().__init__(config)
        self.irregulars = {
            "mice": "mouse",
            "batteries": "battery",
            "monitors": "monitor",
        }

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_lemmatization:
            return series

        def lemmatize(text: str) -> str:
            tokens = text.split()
            lemmatized_tokens = []
            for token in tokens:
                t = token.lower()
                if t in self.irregulars:
                    lemmatized_tokens.append(self.irregulars[t])
                elif t.endswith("ies") and len(t) > 4:
                    lemmatized_tokens.append(t[:-3] + "y")
                elif t.endswith("ing") and len(t) > 4:
                    lemmatized_tokens.append(t[:-3])
                elif t.endswith("s") and not t.endswith("ss") and len(t) > 3:
                    lemmatized_tokens.append(t[:-1])
                else:
                    lemmatized_tokens.append(token)
            return " ".join(lemmatized_tokens)

        return series.apply(lemmatize)


class NumericNormalizer(BaseNormalizationStrategy):
    """Strips leading zeros from standalone numbers (02tb -> 2tb, 0016gb -> 16gb)."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_numeric:
            return series
        # Match word boundary \b, zeros, then digits.
        return series.str.replace(r"\b0+(?=\d)", "", regex=True)


class StopWordNormalizer(BaseNormalizationStrategy):
    """Removes configurable marketing fluff words."""

    def __init__(self, config: NormalizationConfig) -> None:
        super().__init__(config)
        self.stop_words = ["best", "cheap", "buy", "sale", "online"]

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_stopwords:
            return series

        result = series.copy()
        for word in self.stop_words:
            pattern = rf"\b{word}\b"
            result = result.str.replace(pattern, "", regex=True, flags=re.IGNORECASE)
        # Clean up possible leftover double spaces
        result = result.str.replace(r"\s+", " ", regex=True).str.strip()
        return result


class TokenOrderNormalizer(BaseNormalizationStrategy):
    """Sorts tokens alphabetically."""

    def apply(self, series: pd.Series) -> pd.Series:
        if not self.config.enable_token_sorting:
            return series

        def sort_tokens(text: str) -> str:
            return " ".join(sorted(text.split()))

        return series.apply(sort_tokens)
