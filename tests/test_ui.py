"""Unit tests for the UI layer."""

from __future__ import annotations

from collections.abc import Generator

import pytest
import streamlit as st

from keyword_intelligence.ui.services.pipeline_runner import PipelineRunner
from keyword_intelligence.ui.services.session import SessionManager


@pytest.fixture(autouse=True)
def mock_streamlit_session() -> Generator[None, None, None]:
    """Mock the Streamlit session state for testing."""
    # Reset session state before each test
    st.session_state.clear()
    SessionManager.init_defaults()
    yield
    st.session_state.clear()


class TestSessionManager:
    """Test the session manager wrapper."""

    def test_init_defaults(self) -> None:
        """Test defaults are set properly."""
        assert SessionManager.get_current_page() == "upload"
        assert SessionManager.get("running") is False
        assert SessionManager.get_filters() == {}

    def test_set_get_values(self) -> None:
        """Test setting and getting arbitrary typed values."""
        SessionManager.set("test_key", "value")
        assert SessionManager.get("test_key") == "value"

        SessionManager.set("test_key", 123)
        assert SessionManager.get("test_key") == 123

    def test_page_routing(self) -> None:
        """Test page state transitions."""
        assert SessionManager.get_current_page() == "upload"
        SessionManager.set_current_page("results")
        assert SessionManager.get_current_page() == "results"


class TestPipelineRunner:
    """Test the pipeline runner service."""

    def test_runner_initialization(self) -> None:
        """Test runner inits with correct state."""
        runner = PipelineRunner()
        assert runner.context is None
        assert runner.result is None
        assert runner.report is None
        assert len(runner.logs) == 0

    def test_log_recording(self) -> None:
        """Test logs are collected properly."""
        runner = PipelineRunner()
        runner._log("Test message")
        assert len(runner.logs) == 1
        assert "Test message" in runner.logs[0]
