"""CLI interface for executing the Keyword Intelligence Pipeline."""

import argparse
import sys
from pathlib import Path

# Force utf-8 encoding for standard output to support checkmarks on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from loguru import logger

from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.core.constants import StageType
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.events import PipelineEventListener
from keyword_intelligence.pipeline.pipeline import Pipeline


class CliOutputListener(PipelineEventListener):
    """Custom listener to format output exactly as requested."""

    def __init__(self) -> None:
        self.stage_start_times: dict[str, float] = {}

    def before_pipeline(self, context: PipelineContext) -> None:
        pass

    def before_stage(self, stage_type: StageType, context: PipelineContext) -> None:
        pass

    def after_stage(self, stage_type: StageType, context: PipelineContext) -> None:
        pass

    def on_error(
        self, stage_type: StageType, error: Exception, context: PipelineContext
    ) -> None:
        print(f"✗ Failed at {stage_type.value}: {error}\n")


class CliRunner:
    """Command Line Interface runner for the pipeline."""

    def __init__(self) -> None:
        """Initialize the CLI Runner."""
        bootstrap()

        # Remove default loguru stderr handler to keep CLI output clean
        logger.remove()
        logger.add("logs/cli_pipeline.log", rotation="10 MB", level="DEBUG")
        logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")

    def execute(self, args: list[str]) -> None:
        """Parse arguments and execute the pipeline."""
        parser = argparse.ArgumentParser(
            description="Keyword Intelligence Pipeline CLI"
        )
        parser.add_argument(
            "--input", required=True, help="Path to the input CSV or Excel file"
        )
        parser.add_argument("--company", required=True, help="Company Name")
        parser.add_argument("--website", required=True, help="Company Website")
        parser.add_argument("--industry", default="", help="Company Industry")
        parser.add_argument("--sheet", default=None, help="Excel Sheet Name to load")
        parser.add_argument(
            "--column", default=None, help="Explicit Keyword Column to load"
        )
        parser.add_argument(
            "--output-dir", default="output", help="Directory to save outputs"
        )

        parsed_args = parser.parse_args(args)

        input_path = Path(parsed_args.input)
        if not input_path.exists():
            print(f"Error: File '{input_path}' not found.")
            sys.exit(1)

        ext = input_path.suffix.lower()
        file_type = "Excel" if ext in [".xlsx", ".xls"] else "CSV"
        print(f"Detected File Type: {file_type}")
        if file_type == "Excel" and parsed_args.sheet:
            print(f"Selected Sheet: {parsed_args.sheet}")
        if parsed_args.column:
            print(f"Explicit Column: {parsed_args.column}")

        output_dir = Path(parsed_args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pipeline = Pipeline(listeners=[CliOutputListener()])

        try:
            result, context = pipeline.run(
                input_file=input_path,
                file_name=input_path.name,
                company_name=parsed_args.company,
                website=parsed_args.website,
                industry=parsed_args.industry,
                sheet_name=parsed_args.sheet,
                keyword_column=parsed_args.column,
            )

            summary = result.execution_summary or {}
            print("\n====================================")
            print("Keyword Intelligence Pipeline")
            print("====================================")
            print(f"Rows Read: {summary.get('Rows Read', 0)}")
            print(f"Unique Keywords: {summary.get('Unique Keywords', 0)}")
            print(f"Duplicate Keywords: {summary.get('Duplicate Keywords', 0)}")
            print(f"Relevant: {summary.get('Relevant', 0)}")
            print(f"Irrelevant: {summary.get('Irrelevant', 0)}")
            print(f"Deterministic: {summary.get('Deterministic', 0)}")
            print(f"AI: {summary.get('AI', 0)}")
            print(f"AI Reduction %: {summary.get('AI Reduction %', '0.0%')}")
            print(f"Runtime: {summary.get('Runtime', '0 sec')}")

            output_dir_name = "output"
            if result.output_file_locations:
                first_file = Path(result.output_file_locations[0])
                output_dir_name = f"output/{first_file.parent.name}/"

            print(f"\nOutput Directory:\n{output_dir_name}\n")
            print("Generated Files")

            generated_names = [Path(f).name for f in result.output_file_locations]
            expected = [
                "filtered_keywords.csv",
                "filtered_keywords_debug.csv",
                "filtered_keywords.xlsx",
                "execution_summary.json",
                "pipeline_metrics.json",
                "stage_metrics.json",
            ]

            for f in expected:
                if f in generated_names:
                    print(f"✓ {f}")

            for f in generated_names:
                if f not in expected:
                    print(f"✓ {f}")
            print("====================================\n")

        except Exception as e:
            print(f"Pipeline execution failed critically: {e}")
            sys.exit(1)
