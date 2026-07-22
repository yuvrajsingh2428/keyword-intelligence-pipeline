"""Decision Engine."""

from __future__ import annotations

from keyword_intelligence.decision.models import DecisionEnum, KeywordDecision


class DecisionEngine:
    """Evaluates business context to make a final keyword decision."""

    def __init__(
        self, confidence_threshold: float = 0.85, review_threshold: float = 0.50
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.review_threshold = review_threshold

    def decide(
        self,
        retail_relevance: bool | None,
        business_confidence: float,
        requires_ai: bool,
        deterministic_reason: str | None,
        brand_ev: str | None = None,
        category_ev: str | None = None,
        family_ev: str | None = None,
        product_ev: str | None = None,
        tech_ev: str | None = None,
        synonym_ev: str | None = None,
    ) -> KeywordDecision:
        """Evaluate a single keyword's context and return a decision."""
        # 1. DROP: Irrelevant according to retail rules
        if retail_relevance is False:
            return KeywordDecision(
                decision=DecisionEnum.DROP,
                decision_reason=f"Dropped by retail rule: {deterministic_reason}",
                decision_confidence=1.0,
            )

        # 2a. KEEP: Explicit Product Evidence override
        if (product_ev or family_ev) and business_confidence >= self.confidence_threshold:
            return KeywordDecision(
                decision=DecisionEnum.KEEP,
                decision_reason=f"Confident deterministic match: {deterministic_reason} (Explicit Product Match)",
                decision_confidence=business_confidence,
            )

        # 2b. KEEP: High confidence deterministic match
        if not requires_ai and business_confidence >= self.confidence_threshold:
            return KeywordDecision(
                decision=DecisionEnum.KEEP,
                decision_reason=f"Confident deterministic match: {deterministic_reason}",
                decision_confidence=business_confidence,
            )

        # 3. REVIEW: Conflicting logic or anomaly (e.g. requires_ai is False but confidence is strangely low)
        if not requires_ai and business_confidence < self.review_threshold:
            return KeywordDecision(
                decision=DecisionEnum.REVIEW,
                decision_reason=f"Review flagged: Deterministic but low confidence ({business_confidence})",
                decision_confidence=business_confidence,
            )

        # 4. SEND_TO_AI: All other cases (requires AI, or confidence is moderate)
        return KeywordDecision(
            decision=DecisionEnum.SEND_TO_AI,
            decision_reason="Requires AI Classification for accurate decision",
            decision_confidence=business_confidence,
        )
