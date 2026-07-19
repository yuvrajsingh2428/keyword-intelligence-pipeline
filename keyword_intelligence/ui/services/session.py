"""Session state wrapper — avoids direct st.session_state usage."""

from __future__ import annotations

from typing import Any

import streamlit as st

_PREFIX = "kip_"


def _key(name: str) -> str:
    return f"{_PREFIX}{name}"


class SessionManager:
    """Typed façade over Streamlit's session_state.

    All UI code should read/write session state through this class
    so that keys are centralized and strongly typed.
    """

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get(name: str, default: Any = None) -> Any:
        """Get a session value."""
        return st.session_state.get(_key(name), default)

    @staticmethod
    def set(name: str, value: Any) -> None:
        """Set a session value."""
        st.session_state[_key(name)] = value

    @staticmethod
    def has(name: str) -> bool:
        """Check if a session key exists."""
        return _key(name) in st.session_state

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------

    @staticmethod
    def get_current_page() -> str:
        """Return the active page name."""
        return str(st.session_state.get(_key("page"), "upload"))

    @staticmethod
    def set_current_page(page: str) -> None:
        """Set the active page."""
        st.session_state[_key("page")] = page

    @staticmethod
    def get_filters() -> dict[str, Any]:
        """Return active keyword table filters."""
        return dict(st.session_state.get(_key("filters"), {}))

    @staticmethod
    def set_filters(filters: dict[str, Any]) -> None:
        """Update active filters."""
        st.session_state[_key("filters")] = filters

    @staticmethod
    def init_defaults() -> None:
        """Ensure all required keys exist with sensible defaults."""
        defaults: dict[str, Any] = {
            "page": "upload",
            "context": None,
            "report": None,
            "pipeline_result": None,
            "uploaded_file": None,
            "filters": {},
            "logs": [],
            "running": False,
        }
        for k, v in defaults.items():
            if _key(k) not in st.session_state:
                st.session_state[_key(k)] = v

    @staticmethod
    def reset_pipeline_state() -> None:
        """Clear all pipeline execution state while preserving settings/preferences."""
        from loguru import logger

        PIPELINE_KEYS = [
            "context",
            "pipeline_result",
            "processed_dataframe",
            "business_profile",
            "business_facts",
            "stage_outputs",
            "report",
            "logs",
            "ai_results",
            "search_volume_results",
            "uploaded_file",
        ]

        # Clear Streamlit data cache
        st.cache_data.clear()

        # Pop all pipeline keys
        for key in PIPELINE_KEYS:
            if _key(key) in st.session_state:
                st.session_state.pop(_key(key))

        # Re-initialize required default keys
        SessionManager.init_defaults()

        logger.info("Caches cleared.")
        logger.info("Session state reset.")
        logger.info("Fresh pipeline execution started.")
