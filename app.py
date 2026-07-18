"""Keyword Intelligence Pipeline — Streamlit Application Entrypoint.

This is the thin entrypoint script for the Streamlit application.
It initializes logging and delegates rendering to the dashboard module.

Run with:
    streamlit run app.py
"""

from keyword_intelligence.config import get_settings
from keyword_intelligence.config.logging_config import setup_logging
from keyword_intelligence.core.logger import get_logger
from keyword_intelligence.ui.dashboard import render

# Initialize configuration and logging
settings = get_settings()
setup_logging(settings)

logger = get_logger(__name__)
logger.info("Starting Keyword Intelligence Pipeline", version=settings.app_title)

# Render the Streamlit dashboard
render()
