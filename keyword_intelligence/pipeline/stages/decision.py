"""Decision Engine stage for the pipeline."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.decision.engine import DecisionEngine
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class DecisionEngineStage(BaseStage):
    """Pipeline stage that makes deterministic decisions on keywords."""

    def __init__(self, engine: DecisionEngine) -> None:
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        return StageType.DECISION

    @property
    def stage_version(self) -> str:
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute decision engine logic on context."""
        logger.info(f"Executing stage {self.stage_type.value}")

        if not context.has_data:
            return context

        decisions = []
        reasons = []
        confidences = []

        keep = 0
        drop = 0
        send = 0
        review = 0

        df = context.data
        for _, row in df.iterrows():
            if row.get("status") == "DUPLICATE":
                decision_val = "DROP"
                res_reason = "Duplicate keyword"
                res_confidence = 1.0
            else:
                retail_relevance = row.get("business_relevance")
                business_confidence = float(row.get("business_confidence", 0.0))
                requires_ai = bool(row.get("requires_ai", True))
                deterministic_reason = row.get("business_reason")

                res = self.engine.decide(
                    retail_relevance,
                    business_confidence,
                    requires_ai,
                    deterministic_reason,
                )

                decision_val = (
                    res.decision.value
                    if hasattr(res.decision, "value")
                    else res.decision
                )
                res_reason = res.decision_reason
                res_confidence = res.decision_confidence

                if decision_val == "KEEP":
                    keep += 1
                elif decision_val == "DROP":
                    drop += 1
                elif decision_val == "SEND_TO_AI":
                    send += 1
                elif decision_val == "REVIEW":
                    review += 1

            decisions.append(decision_val)
            reasons.append(res_reason)
            confidences.append(res_confidence)

        context.data["decision"] = decisions
        context.data["decision_reason"] = reasons
        context.data["decision_confidence"] = confidences

        logger.info("\nDecision Engine")
        logger.info(f"KEEP: {keep}")
        logger.info(f"DROP: {drop}")
        logger.info(f"SEND_TO_AI: {send}")
        logger.info(f"REVIEW: {review}")

        return context
