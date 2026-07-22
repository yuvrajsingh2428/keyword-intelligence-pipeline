"""Models for the Column Resolver module."""

from enum import Enum

from pydantic import BaseModel


class ResolutionMethod(str, Enum):
    """Method used to resolve the column name."""

    EXACT = "Exact"
    ALIAS = "Alias"
    FUZZY = "Fuzzy"
    MANUAL = "Manual"


class ColumnResolutionResult(BaseModel):
    """Result of a column resolution operation."""

    original_column: str
    mapped_column: str = "keyword"
    method: ResolutionMethod
    confidence_score: float
