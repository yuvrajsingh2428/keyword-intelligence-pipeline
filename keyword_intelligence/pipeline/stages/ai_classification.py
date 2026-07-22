"""Pipeline stage adapter for AI Classification Engine."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.ai_intelligence.engine import AIEngine
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.stage import BaseStage


class AIClassificationStage(BaseStage):
    """Pipeline stage that invokes the AI Classification Engine."""

    def __init__(self, engine: AIEngine) -> None:
        """Initialize the stage with an engine instance."""
        self.engine = engine

    @property
    def stage_type(self) -> StageType:
        """Return the type identifier of the stage."""
        return StageType.AI_CLASSIFICATION

    @property
    def stage_version(self) -> str:
        """Return the version of this stage implementation."""
        return "1.0.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the AI intelligence engine."""
        # Logging removed

        stats = self.engine.process(context)

        df = context.data
        if not context.has_data:
            return context

        # Reconstruct before AI counts
        total_rows = len(df)
        duplicates = (df["status"] == "DUPLICATE").sum() if "status" in df.columns else 0
        keep = (df["decision"] == "KEEP").sum() if "decision" in df.columns else 0
        drop = (df["decision"] == "DROP").sum() if "decision" in df.columns else 0
        review = (df["decision"] == "REVIEW").sum() if "decision" in df.columns else 0
        send = (df["decision"] == "SEND_TO_AI").sum() if "decision" in df.columns else total_rows

        entry_trace = (
            f"Before AI Starts\n"
            f"Received by AI: {send}\n"
            f"Excluded:\n"
            f"Duplicate: {duplicates}\n"
            f"KEEP: {keep}\n"
            f"DROP: {drop}\n"
            f"REVIEW: {review}\n"
        )
        
        if stats:
            exit_trace = (
                f"\nAI Exit Trace\n"
                f"Processed: {stats.resolved_keywords}\n"
                f"Relevant: {(df['ai_relevance'] == 'RELEVANT').sum() if 'ai_relevance' in df.columns else 0}\n"
                f"Irrelevant: {(df['ai_relevance'] == 'IRRELEVANT').sum() if 'ai_relevance' in df.columns else 0}\n"
                f"Fallback: {stats.unresolved_keywords}\n"
                f"Errors: {stats.failed_responses}\n"
                f"Retries: {stats.retries}"
            )
        else:
            exit_trace = ""

        context.stage_diagnostics[self.stage_type.value] = f"{entry_trace}{exit_trace}"

        return context
