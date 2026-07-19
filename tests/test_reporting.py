"""Unit tests for the Reporting & Export Engine."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import pytest

from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.reporting.analytics import AnalyticsEngine
from keyword_intelligence.reporting.engine import ReportEngine
from keyword_intelligence.reporting.exporters.csv import CSVExporter
from keyword_intelligence.reporting.exporters.json import JSONExporter
from keyword_intelligence.reporting.models import (
    ReportResult,
)
from keyword_intelligence.reporting.registry import (
    ExporterRegistry,
    ExporterResolver,
)
from keyword_intelligence.reporting.templates.executive import (
    ExecutiveTemplate,
)
from keyword_intelligence.reporting.templates.summary import (
    SummaryTemplate,
)
from keyword_intelligence.reporting.templates.technical import (
    TechnicalTemplate,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_context(
    n: int = 10,
    settings: Settings | None = None,
) -> PipelineContext:
    """Build a synthetic PipelineContext with *n* rows."""
    s = settings or Settings()
    ctx = PipelineContext(s)

    kws = [f"keyword_{i}" for i in range(n)]
    df = pd.DataFrame(
        {
            "keyword": kws,
            "business_relevance": ["RELEVANT"] * (n // 2)
            + ["IRRELEVANT"] * (n - n // 2),
            "matched_category": ["Laptop"] * (n // 3)
            + ["Gaming"] * (n // 3)
            + ["Unknown"] * (n - 2 * (n // 3)),
            "intent": ["Informational"] * (n // 2) + ["Commercial"] * (n - n // 2),
            "quality": ["GOOD"] * (n // 2) + ["WEAK"] * (n - n // 2),
            "ai_confidence": list(range(50, 50 + n)),
            "search_volume": list(range(100, 100 + n)),
        }
    )
    ctx.data = df
    return ctx


# ------------------------------------------------------------------
# Exporter Registry & Resolver
# ------------------------------------------------------------------


class TestExporterRegistry:
    """Tests for registry and resolver."""

    def test_register_and_get(self) -> None:
        reg = ExporterRegistry()
        reg.register(CSVExporter())
        assert reg.get("csv") is not None
        assert reg.get("nonexistent") is None

    def test_resolver_success(self) -> None:
        reg = ExporterRegistry()
        reg.register(CSVExporter())
        reg.register(JSONExporter())
        resolver = ExporterResolver(reg)

        exp = resolver.resolve("csv")
        assert exp.exporter_name == "csv"

    def test_resolver_failure(self) -> None:
        reg = ExporterRegistry()
        resolver = ExporterResolver(reg)
        with pytest.raises(ValueError, match="not found"):
            resolver.resolve("pdf")


# ------------------------------------------------------------------
# Analytics
# ------------------------------------------------------------------


class TestAnalyticsEngine:
    """Tests for analytics computation."""

    def test_dataset_statistics(self) -> None:
        ctx = _make_context(20)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        assert result.dataset.total_keywords == 20
        assert result.dataset.unique_keywords == 20

    def test_relevance_distribution(self) -> None:
        ctx = _make_context(20)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        assert result.relevance.relevant == 10
        assert result.relevance.irrelevant == 10

    def test_intent_distribution(self) -> None:
        ctx = _make_context(20)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        assert result.intent.informational == 10
        assert result.intent.commercial == 10

    def test_category_distribution(self) -> None:
        ctx = _make_context(21)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        assert "Laptop" in result.categories.counts
        assert "Gaming" in result.categories.counts

    def test_quality_distribution(self) -> None:
        ctx = _make_context(20)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        assert result.quality.good == 10
        assert result.quality.weak == 10

    def test_search_volume_stats(self) -> None:
        ctx = _make_context(20)
        engine = AnalyticsEngine()
        result = engine.compute(ctx)

        sv = result.search_volume
        assert sv.total_with_volume == 20
        assert sv.total_without_volume == 0
        assert sv.average_volume > 0
        assert sv.median_volume > 0
        assert len(sv.top_keywords) <= 10

    def test_empty_dataframe(self) -> None:
        s = Settings()
        ctx = PipelineContext(s)
        ctx.data = pd.DataFrame({"keyword": []})
        engine = AnalyticsEngine()
        result = engine.compute(ctx)
        assert result.dataset.total_keywords == 0


# ------------------------------------------------------------------
# Report Generation
# ------------------------------------------------------------------


class TestReportGeneration:
    """Tests for the ReportEngine."""

    def test_generate_produces_report_result(
        self,
        tmp_path: Path,
    ) -> None:
        ctx = _make_context(50)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )

        assert isinstance(report, ReportResult)
        assert report.executive.total_keywords_analysed == 50
        assert len(report.exported_files) == 1

    def test_multiple_formats(self, tmp_path: Path) -> None:
        ctx = _make_context(10)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["csv", "json"],
            output_dir=str(tmp_path),
        )
        assert len(report.exported_files) == 2

    def test_executive_summary_fields(
        self,
        tmp_path: Path,
    ) -> None:
        ctx = _make_context(30)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )
        assert report.executive.pipeline_health == "HEALTHY"
        assert report.executive.average_confidence > 0


# ------------------------------------------------------------------
# Template Rendering
# ------------------------------------------------------------------


class TestTemplates:
    """Tests for report templates."""

    def test_summary_template(self, tmp_path: Path) -> None:
        ctx = _make_context(10)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )
        rendered = SummaryTemplate.render(report)
        assert "title" in rendered
        assert "total_keywords" in rendered

    def test_executive_template(self, tmp_path: Path) -> None:
        ctx = _make_context(10)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )
        rendered = ExecutiveTemplate.render(report)
        assert "search_volume" in rendered
        assert "quality" in rendered

    def test_technical_template(self, tmp_path: Path) -> None:
        ctx = _make_context(10)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )
        rendered = TechnicalTemplate.render(report)
        assert "execution_id" in rendered
        assert "dataset" in rendered


# ------------------------------------------------------------------
# CSV Exporter
# ------------------------------------------------------------------


class TestCSVExporter:
    """Tests for CSV export."""

    def test_csv_export(self, tmp_path: Path) -> None:
        ctx = _make_context(100)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["csv"],
            output_dir=str(tmp_path),
        )
        csv_path = Path(report.exported_files[0])
        assert csv_path.exists()
        loaded = pd.read_csv(csv_path)
        assert len(loaded) == 100
        assert "keyword" in loaded.columns


# ------------------------------------------------------------------
# Excel Exporter
# ------------------------------------------------------------------


class TestExcelExporter:
    """Tests for Excel export."""

    def test_excel_export(self, tmp_path: Path) -> None:
        ctx = _make_context(50)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["excel"],
            output_dir=str(tmp_path),
        )
        xlsx_path = Path(report.exported_files[0])
        assert xlsx_path.exists()
        assert xlsx_path.suffix == ".xlsx"

        xls = pd.ExcelFile(xlsx_path)
        assert "Summary" in xls.sheet_names
        assert "Keywords" in xls.sheet_names
        assert "Statistics" in xls.sheet_names
        assert "Pipeline Metrics" in xls.sheet_names

        kw_df = pd.read_excel(xlsx_path, sheet_name="Keywords")
        assert len(kw_df) == 50


# ------------------------------------------------------------------
# JSON Exporter
# ------------------------------------------------------------------


class TestJSONExporter:
    """Tests for JSON export."""

    def test_json_export(self, tmp_path: Path) -> None:
        ctx = _make_context(20)
        engine = ReportEngine(ctx.settings)
        report = engine.generate(
            ctx,
            export_formats=["json"],
            output_dir=str(tmp_path),
        )
        json_path = Path(report.exported_files[0])
        assert json_path.exists()

        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert "executive" in data
        assert "analytics" in data
        assert "pipeline" in data
        assert data["executive"]["total_keywords_analysed"] == 20


# ------------------------------------------------------------------
# Stage Integration
# ------------------------------------------------------------------


class TestReportingStage:
    """Tests for ReportingStage."""

    def test_stage_executes(self, tmp_path: Path) -> None:
        from keyword_intelligence.pipeline.stages.reporting import (
            ReportingStage,
        )

        ctx = _make_context(10)
        engine = ReportEngine(ctx.settings)
        # Override output dir via engine config
        engine.config.output_dir = str(tmp_path)
        stage = ReportingStage(engine)

        result_ctx = stage.execute(ctx)
        assert result_ctx is ctx

        # At least one file should have been exported
        exported = list(tmp_path.glob("*"))
        assert len(exported) >= 1


# ------------------------------------------------------------------
# Benchmark
# ------------------------------------------------------------------


class TestBenchmark:
    """Performance benchmarks."""

    def test_50k_export_benchmark(
        self,
        tmp_path: Path,
    ) -> None:
        """Export 50,000 rows and verify it completes quickly."""
        ctx = _make_context(50_000)
        engine = ReportEngine(ctx.settings)

        start = time.perf_counter()
        report = engine.generate(
            ctx,
            export_formats=["csv", "json"],
            output_dir=str(tmp_path),
        )
        duration = time.perf_counter() - start

        assert duration < 15.0, f"50k export took {duration:.2f}s"
        assert len(report.exported_files) == 2
        assert report.executive.total_keywords_analysed == 50_000
