"""Summary report template — formats data only."""

from __future__ import annotations

from keyword_intelligence.reporting.models import (
    ReportResult,
)


class SummaryTemplate:
    """Produces a compact summary report.

    This template selects the most useful subset of data from
    the analytics and pipeline summaries. No business logic
    is performed here — only formatting and field selection.
    """

    @staticmethod
    def render(report: ReportResult) -> dict[str, object]:
        """Render the summary template.

        Args:
            report: The complete ReportResult.

        Returns:
            A dictionary suitable for display or serialisation.
        """
        exec_summary = report.executive
        analytics = report.analytics

        return {
            "title": exec_summary.title,
            "generated_at": str(exec_summary.generated_at),
            "total_keywords": exec_summary.total_keywords_analysed,
            "relevant": analytics.relevance.relevant,
            "irrelevant": analytics.relevance.irrelevant,
            "uncertain": analytics.relevance.uncertain,
            "avg_confidence": round(exec_summary.average_confidence, 2),
            "top_category": exec_summary.top_category,
            "dominant_intent": exec_summary.dominant_intent,
            "pipeline_health": exec_summary.pipeline_health,
        }
