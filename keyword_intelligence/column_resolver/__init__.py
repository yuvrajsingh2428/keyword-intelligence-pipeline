"""Column Resolver Module.

Automatically detects and standardizes keyword columns from tabular datasets.
"""

from keyword_intelligence.column_resolver.exceptions import KeywordColumnNotFoundError
from keyword_intelligence.column_resolver.models import (
    ColumnResolutionResult,
    ResolutionMethod,
)
from keyword_intelligence.column_resolver.resolver import ColumnResolver

__all__ = [
    "ColumnResolutionResult",
    "ColumnResolver",
    "KeywordColumnNotFoundError",
    "ResolutionMethod",
]
