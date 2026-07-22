"""Final Classification pipeline stage."""

from __future__ import annotations

import pandas as pd
from loguru import logger

from keyword_intelligence.business_context.engine import BusinessContextEngine
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class FinalClassificationStage(BaseStage):
    """Consolidates decisions into the final business output format.

    Generates:
        - relevant (bool)
        - relevance_score (float)
        - classified_by (str)
        - classification_stage (str)
        - reason (str)
        - processing_method (str)
        - brand (str)
        - category (str)
        - company_name (str)
        - company_website (str)
    """

    def __init__(
        self, engine: BusinessContextEngine, company_name: str, website: str
    ) -> None:
        self.engine = engine
        self.company_name = company_name
        self.website = website
        super().__init__()

    @property
    def stage_type(self) -> StageType:
        return StageType.REPORTING  # Reusing reporting stage type or could be custom

    @property
    def stage_version(self) -> str:
        return "1.0.0"

    @property
    def name(self) -> str:
        return "Final Classification"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute final classification logic."""
        if not context.has_data or context.data.empty:
            return context

        df = context.data.copy()

        # Get company context from dynamic profile (will hit cache)
        company_ctx = self.engine.process(self.company_name, self.website)

        # Logging removed

        def _compute_final_classification(row: pd.Series) -> pd.Series:
            decision = row.get("decision", "REVIEW")

            relevant = False
            relevance_score = 0.0
            classified_by = "Decision Engine"
            classification_stage = "Decision Engine"
            reason = row.get("decision_reason", "")
            processing_method = "Deterministic"
            brand = row.get("business_brand", "")
            category = row.get("business_category", "")

            # Map deterministic decision
            if decision == "KEEP":
                relevant = True
                conf = float(row.get("business_confidence", 0.0))
                relevance_score = min(conf, 1.0)
                classification_stage = "Decision Engine"

            elif decision == "DROP":
                relevant = False
                conf = float(row.get("business_confidence", 0.0))
                relevance_score = min(conf, 1.0)
                classification_stage = "Decision Engine"

            elif decision == "REVIEW":
                # By default treat review as irrelevant or unclassified
                relevant = False
                conf = float(row.get("business_confidence", 0.0))
                relevance_score = min(conf, 1.0)
                classification_stage = "Decision Engine"

            elif decision == "SEND_TO_AI":
                classified_by = "AI"
                classification_stage = "AI Classification"
                processing_method = "AI"

                ai_relevance = row.get("ai_relevance")
                ai_reason = row.get("ai_reason")
                ai_conf = row.get("ai_confidence", 0.0)
                ai_cat = row.get("ai_category")

                if pd.notna(ai_relevance):
                    relevant = ai_relevance == "RELEVANT"
                    if pd.notna(ai_conf):
                        relevance_score = min(float(ai_conf), 1.0)
                if pd.notna(ai_reason):
                    reason = ai_reason
                if pd.notna(ai_cat) and ai_cat != "Unknown":
                    category = ai_cat

            # Ensure numeric safety
            if pd.isna(relevance_score):
                relevance_score = 0.0

            return pd.Series(
                {
                    "relevant": relevant,
                    "relevance_score": round(relevance_score, 2),
                    "classified_by": classified_by,
                    "classification_stage": classification_stage,
                    "reason": str(reason) if pd.notna(reason) else "",
                    "brand": str(brand) if pd.notna(brand) else "",
                    "category": str(category) if pd.notna(category) else "",
                    "processing_method": processing_method,
                    "company_name": company_ctx.company_name,
                    "company_website": company_ctx.website,
                }
            )

        # Apply row-wise computation
        final_cols = df.apply(_compute_final_classification, axis=1)

        # Merge back to df
        for col in final_cols.columns:
            df[col] = final_cols[col]

        # Ensure 'duplicate_group' is mapped properly if available
        if "duplicate_group_id" in df.columns:
            df["duplicate_group"] = df["duplicate_group_id"]
        elif "duplicate_group" not in df.columns:
            df["duplicate_group"] = ""

        if "normalized_keyword" not in df.columns:
            df["normalized_keyword"] = df.get("keyword", "")

        context.data = df

        # Reconcile counts
        det_rel = ((df["processing_method"] == "Deterministic") & (df["relevant"] == True)).sum()
        ai_rel = ((df["processing_method"] == "AI") & (df["relevant"] == True)).sum()
        det_irrel = ((df["processing_method"] == "Deterministic") & (df["relevant"] == False) & (df.get("status", "") != "DUPLICATE")).sum()
        ai_irrel = ((df["processing_method"] == "AI") & (df["relevant"] == False) & (df.get("status", "") != "DUPLICATE")).sum()
        duplicates = (df.get("status", "") == "DUPLICATE").sum()
        
        final_rel = df["relevant"].sum()
        final_irrel = (~df["relevant"]).sum()
        
        trace = (
            f"Deterministic Relevant: {det_rel}\n"
            f"AI Relevant: {ai_rel}\n"
            f"Deterministic Irrelevant: {det_irrel}\n"
            f"AI Irrelevant: {ai_irrel}\n"
            f"Duplicates: {duplicates}\n"
            f"Final Relevant: {final_rel}\n"
            f"Final Irrelevant: {final_irrel}"
        )
        context.stage_diagnostics[self.stage_type.value] = trace

        if (
            (df["relevant"] == False).all()
            and (df["relevance_score"] == 0.0).all()
            and (df["classified_by"] == "Decision Engine").all()
            and len(df) > 0
        ):
            raise ValueError(
                "PipelineValidationError: All keywords classified as irrelevant by Decision Engine with 0 confidence. Business Context enrichment likely failed."
            )

        return context
