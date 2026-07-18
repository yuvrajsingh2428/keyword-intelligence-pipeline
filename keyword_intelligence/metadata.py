"""Application metadata for the Keyword Intelligence Pipeline.

Centralizes application identity information used across the project:
UI headers, logging context, package metadata, and API responses.

All values here are the single source of truth — do not duplicate
these strings elsewhere in the codebase.
"""

from __future__ import annotations

APP_NAME: str = "Keyword Intelligence Pipeline"
"""The official display name of the application."""

VERSION: str = "0.1.0"
"""Semantic version string (MAJOR.MINOR.PATCH)."""

DESCRIPTION: str = (
    "An AI-powered keyword intelligence pipeline for automated keyword "
    "analysis, clustering, and strategic content recommendations."
)
"""Brief description used in package metadata and the UI footer."""

AUTHOR: str = "Keyword Intelligence Team"
"""The team or individual responsible for the application."""

REPOSITORY_URL: str = "https://github.com/your-org/keyword-intelligence-pipeline"
"""Link to the project source code repository."""

LICENSE: str = "MIT"
"""The project's license identifier."""
