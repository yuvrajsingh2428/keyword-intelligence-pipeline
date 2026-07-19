"""Analytics engine computing statistics from PipelineContext."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.reporting.models import (
    AnalyticsSummary,
    CategoryDistribution,
    DatasetStatistics,
    IntentDistribution,
    PipelineTimingStatistics,
    QualityDistribution,
    RelevanceDistribution,
    SearchVolumeStatistics,
)


class AnalyticsEngine:
    """Computes strongly-typed analytics from a PipelineContext.

    All business logic for metric computation lives here.
    Templates and exporters must never perform analytical calculations.
    """

    def compute(self, context: PipelineContext) -> AnalyticsSummary:
        """Compute the full analytics summary.

        Args:
            context: A populated pipeline context.

        Returns:
            An AnalyticsSummary containing all computed metrics.
        """
        df = context.data if context.has_data else pd.DataFrame()

        return AnalyticsSummary(
            dataset=self._dataset_stats(df, context),
            relevance=self._relevance_dist(df),
            intent=self._intent_dist(df),
            categories=self._category_dist(df),
            quality=self._quality_dist(df),
            search_volume=self._search_volume_stats(df),
        )

    def compute_timing(
        self,
        context: PipelineContext,
    ) -> PipelineTimingStatistics:
        """Compute pipeline timing statistics.

        Args:
            context: A populated pipeline context.

        Returns:
            PipelineTimingStatistics with stage-level breakdown.
        """
        stage_timings: dict[str, float] = {}
        for sm in context.stage_metrics:
            stage_timings[sm.stage_name] = sm.processing_time_ms

        return PipelineTimingStatistics(
            total_execution_time_ms=(context.pipeline_metrics.total_time_ms),
            stage_timings=stage_timings,
        )

    # ------------------------------------------------------------------
    # Private computation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dataset_stats(
        df: pd.DataFrame,
        context: PipelineContext,
    ) -> DatasetStatistics:
        total = len(df)
        unique = int(df["keyword"].nunique()) if "keyword" in df.columns else total
        removed = context.pipeline_metrics.total_rows_removed

        return DatasetStatistics(
            total_keywords=total,
            unique_keywords=unique,
            duplicate_keywords=total - unique,
            removed_keywords=removed,
        )

    @staticmethod
    def _relevance_dist(df: pd.DataFrame) -> RelevanceDistribution:
        if "business_relevance" not in df.columns:
            return RelevanceDistribution()

        counts = df["business_relevance"].value_counts()
        return RelevanceDistribution(
            relevant=int(counts.get("RELEVANT", 0)),
            irrelevant=int(counts.get("IRRELEVANT", 0)),
            uncertain=int(counts.get("UNCERTAIN", 0)),
        )

    @staticmethod
    def _intent_dist(df: pd.DataFrame) -> IntentDistribution:
        if "intent" not in df.columns:
            return IntentDistribution()

        counts = df["intent"].value_counts()
        return IntentDistribution(
            informational=int(counts.get("Informational", 0)),
            commercial=int(counts.get("Commercial", 0)),
            transactional=int(counts.get("Transactional", 0)),
            navigational=int(counts.get("Navigational", 0)),
            unknown=int(counts.get("Unknown", 0)),
        )

    @staticmethod
    def _category_dist(df: pd.DataFrame) -> CategoryDistribution:
        if "matched_category" not in df.columns:
            return CategoryDistribution()

        raw_counts = df["matched_category"].value_counts()
        return CategoryDistribution(
            counts={str(k): int(v) for k, v in raw_counts.items()},
        )

    @staticmethod
    def _quality_dist(df: pd.DataFrame) -> QualityDistribution:
        if "quality" not in df.columns:
            return QualityDistribution()

        counts = df["quality"].value_counts()
        return QualityDistribution(
            good=int(counts.get("GOOD", 0)),
            weak=int(counts.get("WEAK", 0)),
            spam=int(counts.get("SPAM", 0)),
            duplicate=int(counts.get("DUPLICATE", 0)),
            unknown=int(counts.get("UNKNOWN", 0)),
        )

    @staticmethod
    def _search_volume_stats(
        df: pd.DataFrame,
    ) -> SearchVolumeStatistics:
        if "search_volume" not in df.columns:
            return SearchVolumeStatistics()

        vol = pd.to_numeric(df["search_volume"], errors="coerce")
        valid = vol.dropna()
        missing = int(vol.isna().sum())

        top_kw: list[dict[str, Any]] = []
        if not valid.empty and "keyword" in df.columns:
            top_idx = valid.nlargest(10).index
            for idx in top_idx:
                top_kw.append(
                    {
                        "keyword": str(df.at[idx, "keyword"]),
                        "volume": int(valid.loc[idx:idx].iloc[0]),
                    }
                )

        return SearchVolumeStatistics(
            average_volume=float(np.mean(valid)) if not valid.empty else 0.0,
            median_volume=float(np.median(valid)) if not valid.empty else 0.0,
            min_volume=float(np.min(valid)) if not valid.empty else 0.0,
            max_volume=float(np.max(valid)) if not valid.empty else 0.0,
            total_with_volume=len(valid),
            total_without_volume=missing,
            top_keywords=top_kw,
        )
