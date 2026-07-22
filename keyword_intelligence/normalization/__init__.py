"""Keyword Normalization module.

This module provides configurable normalization strategies to standardise
keyword representations prior to duplicate detection and AI classification.
"""

from keyword_intelligence.normalization.engine import NormalizationEngine
from keyword_intelligence.normalization.models import NormalizationConfig
from keyword_intelligence.normalization.strategies import (
    BaseNormalizationStrategy,
    CaseNormalizer,
    DictionaryNormalizer,
    PunctuationNormalizer,
    UnicodeNormalizer,
    WhitespaceNormalizer,
)

__all__ = [
    "BaseNormalizationStrategy",
    "CaseNormalizer",
    "DictionaryNormalizer",
    "NormalizationConfig",
    "NormalizationEngine",
    "PunctuationNormalizer",
    "UnicodeNormalizer",
    "WhitespaceNormalizer",
]
