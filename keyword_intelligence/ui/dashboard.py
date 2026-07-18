"""Placeholder dashboard page for the Keyword Intelligence Pipeline.

Renders the main Streamlit dashboard with application status,
navigation sidebar, and project information. This is the Phase 1
placeholder UI — future phases will replace sections with
interactive pipeline controls and data visualizations.

Usage:
    This module is called by the app.py entrypoint:

        from keyword_intelligence.ui.dashboard import render
        render()
"""

from __future__ import annotations

import streamlit as st

from keyword_intelligence.constants import (
    PHASE_LABEL,
    SIDEBAR_TITLE,
)
from keyword_intelligence.metadata import (
    APP_NAME,
    AUTHOR,
    DESCRIPTION,
    REPOSITORY_URL,
    VERSION,
)


def _render_sidebar() -> None:
    """Render the sidebar with navigation and application information."""
    with st.sidebar:
        st.title(SIDEBAR_TITLE)
        st.divider()

        # Application info
        st.markdown("### 📋 App Info")
        st.markdown(f"**Version:** `{VERSION}`")
        st.markdown(f"**Phase:** {PHASE_LABEL}")
        st.markdown(f"**Author:** {AUTHOR}")

        st.divider()

        # Navigation placeholder
        st.markdown("### 🗂️ Modules")
        st.markdown(
            """
            - 🏠 Dashboard *(active)*
            - 🔍 Keyword Analysis *(Phase 2)*
            - 🧩 Clustering *(Phase 3)*
            - 📊 Reports *(Phase 4)*
            - ⚙️ Settings *(Phase 5)*
            """
        )

        st.divider()

        # Repository link
        st.markdown(f"[📦 GitHub Repository]({REPOSITORY_URL})")


def _render_header() -> None:
    """Render the main page header with title and description."""
    st.title(f"🚀 {APP_NAME}")
    st.caption(DESCRIPTION)
    st.divider()


def _render_status_cards() -> None:
    """Render Phase 1 status indicator cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Project Phase", value="1", delta="Foundation")
    with col2:
        st.metric(label="Version", value=VERSION)
    with col3:
        st.metric(label="Modules", value="7", delta="Ready")
    with col4:
        st.metric(label="Test Coverage", value="—", delta="Pending")


def _render_foundation_status() -> None:
    """Render the Phase 1 completion checklist."""
    st.markdown(f"### ✅ {PHASE_LABEL}")
    st.success("Project foundation has been successfully established.", icon="🎉")

    st.markdown("#### Completed Components")
    components = {
        "Project Structure": "Clean modular architecture with separation of concerns",
        "Configuration Management": "Typed settings with Pydantic BaseSettings",
        "Logging Infrastructure": "Loguru with console/JSON modes and file rotation",
        "Exception Hierarchy": "Structured application exceptions",
        "Data Models": "Base Pydantic model with shared configuration",
        "Service Layer": "Abstract base service with lifecycle management",
        "Pipeline Design": "PipelineContext architecture documented",
        "Code Quality": "Black, Ruff, MyPy, pre-commit configured",
        "CI/CD": "GitHub Actions workflow for lint, typecheck, and test",
        "Developer Tooling": "Cross-platform Makefile + PowerShell scripts",
    }

    for component, description in components.items():
        st.markdown(f"- ✅ **{component}** — {description}")


def _render_architecture_overview() -> None:
    """Render a high-level architecture overview."""
    st.markdown("### 🏗️ Architecture Overview")

    st.code(
        """
keyword_intelligence/
├── config/       → Settings, logging configuration
├── core/         → Logger factory, exception hierarchy
├── models/       → Pydantic data models
├── services/     → External service integrations
├── pipeline/     → Pipeline orchestration (Phase 2+)
├── utils/        → Stateless helper functions
└── ui/           → Streamlit presentation layer
        """,
        language="text",
    )


def render() -> None:
    """Render the complete dashboard page.

    This is the main entry point called by app.py. It assembles
    all dashboard sections in order.
    """
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _render_sidebar()
    _render_header()
    _render_status_cards()

    st.divider()

    # Two-column layout for content
    left_col, right_col = st.columns([3, 2])

    with left_col:
        _render_foundation_status()

    with right_col:
        _render_architecture_overview()

    # Footer
    st.divider()
    st.caption(f"{APP_NAME} v{VERSION} • {PHASE_LABEL} • " f"Built with ❤️ by {AUTHOR}")
