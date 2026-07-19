"""Executive report template — formats data only."""

from __future__ import annotations

from keyword_intelligence.reporting.models import ReportResult


class ExecutiveTemplate:
    """Produces the executive-level report.

    Stakeholder-oriented: emphasises classification outcomes,
    keyword quality, and volume insights over technical details.
    """

    @staticmethod
    def render(report: ReportResult) -> dict[str, object]:
        """Render the executive report.

        Args:
            report: The complete ReportResult.

        Returns:
            A formatted dictionary for executive consumption.
        """
        e = report.executive
        a = report.analytics
        sv = a.search_volume

        return {
            "title": e.title,
            "generated_at": str(e.generated_at),
            "total_keywords": e.total_keywords_analysed,
            "relevant_keywords": e.relevant_keywords,
            "irrelevant_keywords": e.irrelevant_keywords,
            "average_confidence": round(e.average_confidence, 2),
            "top_category": e.top_category,
            "dominant_intent": e.dominant_intent,
            "pipeline_health": e.pipeline_health,
            "search_volume": {
                "average": round(sv.average_volume, 2),
                "median": round(sv.median_volume, 2),
                "top_keywords": sv.top_keywords[:5],
            },
            "quality": {
                "good": a.quality.good,
                "weak": a.quality.weak,
                "spam": a.quality.spam,
            },
            "warnings": e.warnings_count,
            "errors": e.errors_count,
        }
