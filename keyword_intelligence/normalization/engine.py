"""Orchestration engine for applying normalization strategies."""

from __future__ import annotations

import pandas as pd
from loguru import logger

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.normalization.dictionary import NormalizationDictionary
from keyword_intelligence.normalization.models import (
    NormalizationConfig,
    NormalizationMetrics,
    NormalizationResult,
)
from keyword_intelligence.normalization.strategies import (
    BaseNormalizationStrategy,
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


class NormalizationEngine:
    """Facade for applying multiple normalization strategies to keyword datasets."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the engine with application settings."""
        self.config = NormalizationConfig.from_settings(settings)
        # Pass the paths from the config to the dictionary
        self.dictionary = NormalizationDictionary(
            dictionary_path=self.config.dictionary_path,
            company_dictionary_path=self.config.company_dictionary_path,
        )

        self.strategies: list[BaseNormalizationStrategy] = [
            CaseNormalizer(self.config),
            WhitespaceNormalizer(self.config),
            UnicodeNormalizer(self.config),
            PunctuationNormalizer(self.config),
            DictionaryNormalizer(self.config, self.dictionary),
            CompanyDictionaryNormalizer(self.config, self.dictionary),
            ProductTokenNormalizer(self.config),
            UnitNormalizer(self.config),
            LemmatizationNormalizer(self.config),
            NumericNormalizer(self.config),
            StopWordNormalizer(self.config),
            TokenOrderNormalizer(self.config),
        ]

    def register_strategy(self, strategy: BaseNormalizationStrategy) -> None:
        """Add a custom strategy to the end of the normalization pipeline."""
        self.strategies.append(strategy)

    def normalize_series(self, series: pd.Series) -> NormalizationResult:
        """Apply all registered normalization strategies to a pandas Series.

        Args:
            series: The input Series of keywords.

        Returns:
            A NormalizationResult containing normalized keywords, traces, and metrics.
        """
        # Removing debug log
        original_series = series.copy().fillna("")
        current_series = original_series.copy()

        # Initialize trace series and metrics
        traces = pd.Series("", index=series.index)
        metrics = NormalizationMetrics(total_processed=len(series))

        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__
            # Removing debug log

            new_series = strategy.apply(current_series)

            # Vectorized check for modifications
            changed_mask = new_series != current_series
            modifications = changed_mask.sum()

            if modifications > 0:
                metrics.add_strategy_modifications(strategy_name, int(modifications))
                # Append strategy name to trace where changes occurred
                traces.loc[changed_mask] = (
                    traces.loc[changed_mask] + strategy_name + " -> "
                )

            current_series = new_series

        # Strip trailing " -> " from traces
        traces = traces.str.removesuffix(" -> ")

        # Calculate total modified
        final_changed_mask = current_series != original_series
        metrics.total_modified = int(final_changed_mask.sum())

        return NormalizationResult(
            normalized_series=current_series, trace_series=traces, metrics=metrics
        )
