"""CSV exporter for the final dataset."""

from pathlib import Path

from loguru import logger

from keyword_intelligence.exporters.base import BaseExporter
from keyword_intelligence.models import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext


class CSVExporter(BaseExporter):
    """Generates the filtered_keywords.csv artifact."""

    def export(
        self, result: PipelineResult, context: PipelineContext, output_dir: Path
    ) -> list[str]:
        if not context.has_data:
            return []

        df = context.data
        exported_files = []

        try:


            # 2. Business Output (Clean Columns)
            df_business = df.rename(
                columns={
                    "classification_stage": "classification",
                    "relevance_score": "confidence",
                    "company_name": "company",
                    "company_website": "website",
                }
            ).copy()

            # Map booleans to strings, round confidence
            if "relevant" in df_business.columns:
                df_business["relevant"] = df_business["relevant"].map(
                    {
                        True: "Relevant",
                        False: "Irrelevant",
                        "True": "Relevant",
                        "False": "Irrelevant",
                    }
                )

            if "confidence" in df_business.columns:
                df_business["confidence"] = (
                    df_business["confidence"].astype(float).round(2)
                )

            # Sort by relevant DESC and search_volume DESC
            sort_cols = []
            sort_asc = []
            if "relevant" in df_business.columns:
                sort_cols.append("relevant")
                sort_asc.append(False)  # 'Relevant' > 'Irrelevant'
            if "search_volume" in df_business.columns:
                sort_cols.append("search_volume")
                sort_asc.append(False)

            if sort_cols:
                df_business = df_business.sort_values(by=sort_cols, ascending=sort_asc)

            # We want specific columns if they exist
            target_cols = [
                "keyword",
                "search_volume",
                "relevant",
                "confidence",
                "brand",
                "category",
                "search_intent",
                "classification",
                "recommended_action",
                "reason",
                "company",
                "website",
            ]

            available_cols = [c for c in target_cols if c in df_business.columns]

            csv_path = output_dir / "filtered_keywords.csv"
            df_business[available_cols].to_csv(csv_path, index=False)
            exported_files.append(str(csv_path.absolute()))

            # 3. Duplicate Keywords
            if "status" in df.columns:
                duplicates = df[df["status"] == "DUPLICATE"]
                if not duplicates.empty:
                    dup_path = output_dir / "duplicate_keywords.csv"
                    duplicates.to_csv(dup_path, index=False)
                    exported_files.append(str(dup_path.absolute()))

            return exported_files

        except Exception as e:
            logger.error(f"Failed to generate CSV output: {e}")
            return []
