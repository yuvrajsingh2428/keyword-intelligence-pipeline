"""Tests for Decision Engine."""

from keyword_intelligence.decision.engine import DecisionEngine
from keyword_intelligence.decision.models import DecisionEnum


def test_decision_drop():
    """Test dropping a keyword based on retail rules."""
    engine = DecisionEngine()

    decision = engine.decide(
        retail_relevance=False,
        business_confidence=1.0,
        requires_ai=False,
        deterministic_reason="Competitor product",
    )

    assert decision.decision == DecisionEnum.DROP
    assert "retail rule" in decision.decision_reason.lower()


def test_decision_keep():
    """Test keeping a highly confident deterministic match."""
    engine = DecisionEngine(confidence_threshold=0.85)

    decision = engine.decide(
        retail_relevance=True,
        business_confidence=0.95,
        requires_ai=False,
        deterministic_reason="Product Family Match",
    )

    assert decision.decision == DecisionEnum.KEEP
    assert "confident" in decision.decision_reason.lower()


def test_decision_review():
    """Test flagging an anomaly for manual review."""
    engine = DecisionEngine(review_threshold=0.50)

    decision = engine.decide(
        retail_relevance=True,
        business_confidence=0.40,
        requires_ai=False,
        deterministic_reason="Weak synonym match",
    )

    assert decision.decision == DecisionEnum.REVIEW
    assert "review flagged" in decision.decision_reason.lower()


def test_decision_send_to_ai():
    """Test sending an unknown or moderate confidence keyword to AI."""
    engine = DecisionEngine(confidence_threshold=0.85, review_threshold=0.50)

    # Requires AI explicitly
    decision1 = engine.decide(
        retail_relevance=None,
        business_confidence=0.0,
        requires_ai=True,
        deterministic_reason="Unknown keyword",
    )
    assert decision1.decision == DecisionEnum.SEND_TO_AI

    # Does not require AI, but falls in the uncertainty band (0.50 <= x < 0.85)
    decision2 = engine.decide(
        retail_relevance=True,
        business_confidence=0.75,
        requires_ai=False,
        deterministic_reason="Category Match only",
    )
    assert decision2.decision == DecisionEnum.SEND_TO_AI
