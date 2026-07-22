"""API interface adapter for the Keyword Intelligence Pipeline."""

from __future__ import annotations

from typing import Any


class ApiRunner:
    """Service that REST APIs use to execute the pipeline."""

    def __init__(self) -> None:
        """Initialize the API Runner."""
        pass

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute the pipeline based on API payload.

        This is a stub implementation meant to be expanded in the future.
        """
        # pipeline = Pipeline()
        # Extract file from payload (e.g. base64 or S3 URI)
        # result, context = pipeline.run(input_file=file_path_or_bytes)
        # return result.model_dump()

        return {"status": "Not Implemented"}
