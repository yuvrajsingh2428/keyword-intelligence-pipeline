"""Decision Engine Models."""

from __future__ import annotations

from enum import Enum

from keyword_intelligence.models.base import AppBaseModel


class DecisionEnum(str, Enum):
    """The final decision for a keyword."""

    KEEP = "KEEP"
    DROP = "DROP"
    SEND_TO_AI = "SEND_TO_AI"
    REVIEW = "REVIEW"


class KeywordDecision(AppBaseModel):
    """The decision output for a single keyword."""

    decision: DecisionEnum
    decision_reason: str
    decision_confidence: float
    processing_method: str = "Deterministic"
