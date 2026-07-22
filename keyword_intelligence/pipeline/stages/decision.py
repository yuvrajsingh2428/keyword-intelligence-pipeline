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
        # Logging removed

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
                import pandas as pd
                retail_relevance = row.get("business_relevance")
                business_confidence = float(row.get("business_confidence", 0.0))
                requires_ai = bool(row.get("requires_ai", True))
                deterministic_reason = row.get("business_reason")
                
                brand_ev = row.get("business_brand") if not pd.isna(row.get("business_brand")) else None
                cat_ev = row.get("business_category") if not pd.isna(row.get("business_category")) else None
                fam_ev = row.get("business_product_family") if not pd.isna(row.get("business_product_family")) else None
                prod_ev = row.get("business_product") if not pd.isna(row.get("business_product")) else None
                tech_ev = row.get("business_technology") if not pd.isna(row.get("business_technology")) else None
                syn_ev = row.get("business_synonym") if not pd.isna(row.get("business_synonym")) else None

                res = self.engine.decide(
                    retail_relevance,
                    business_confidence,
                    requires_ai,
                    deterministic_reason,
                    brand_ev,
                    cat_ev,
                    fam_ev,
                    prod_ev,
                    tech_ev,
                    syn_ev,
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

        brand_ev = df["business_brand"].notna().sum() if "business_brand" in df.columns else 0
        cat_ev = df["business_category"].notna().sum() if "business_category" in df.columns else 0
        prod_ev = df["business_product"].notna().sum() if "business_product" in df.columns else 0
        fam_ev = df["business_product_family"].notna().sum() if "business_product_family" in df.columns else 0
        tech_ev = df["business_technology"].notna().sum() if "business_technology" in df.columns else 0
        unknown = df["requires_ai"].sum() if "requires_ai" in df.columns else 0

        trace = (
            f"KEEP: {keep}\n"
            f"DROP: {drop}\n"
            f"SEND_TO_AI: {send}\n"
            f"REVIEW: {review}\n\n"
            f"WHY\n"
            f"Brand Evidence: {brand_ev}\n"
            f"Category Evidence: {cat_ev}\n"
            f"Product Evidence: {prod_ev}\n"
            f"Family Evidence: {fam_ev}\n"
            f"Technology Evidence: {tech_ev}\n"
            f"Unknown: {unknown}"
        )
        context.stage_diagnostics[self.stage_type.value] = trace

        return context
