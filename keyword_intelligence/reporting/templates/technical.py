"""Technical report template — formats data only."""

from __future__ import annotations

from keyword_intelligence.reporting.models import ReportResult


class TechnicalTemplate:
    """Produces the engineer-oriented technical report.

    Contains stage timings, error traces, cache ratios,
    and dataset transformation details.
    """

    @staticmethod
    def render(report: ReportResult) -> dict[str, object]:
        """Render the technical report.

        Args:
            report: The complete ReportResult.

        Returns:
            A formatted dictionary for technical review.
        """
        t = report.technical
        p = report.pipeline

        return {
            "execution_id": t.execution_id,
            "pipeline_version": t.pipeline_version,
            "stages_executed": t.stages_executed,
            "total_execution_time_ms": round(p.timing.total_execution_time_ms, 2),
            "stage_timings": {
                k: round(v, 2) for k, v in p.timing.stage_timings.items()
            },
            "dataset": {
                "total": t.dataset.total_keywords,
                "unique": t.dataset.unique_keywords,
                "duplicates": t.dataset.duplicate_keywords,
                "removed": t.dataset.removed_keywords,
            },
            "warnings": t.warnings,
            "errors": t.errors,
        }
