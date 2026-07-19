"""Centralized theme configuration for the Streamlit dashboard."""

from __future__ import annotations

from typing import ClassVar

from keyword_intelligence.models.base import AppBaseModel


class ThemeColors(AppBaseModel):
    """Application colour palette — no hardcoded colours in components."""

    primary: str = "#6366F1"
    secondary: str = "#8B5CF6"
    accent: str = "#EC4899"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    info: str = "#3B82F6"

    bg_primary: str = "#0F172A"
    bg_secondary: str = "#1E293B"
    bg_card: str = "#1E293B"

    text_primary: str = "#F8FAFC"
    text_secondary: str = "#94A3B8"
    text_muted: str = "#64748B"

    border: str = "#334155"

    chart_palette: ClassVar[list[str]] = [
        "#6366F1",
        "#EC4899",
        "#10B981",
        "#F59E0B",
        "#3B82F6",
        "#8B5CF6",
        "#14B8A6",
        "#F97316",
    ]


THEME = ThemeColors()


def inject_css() -> str:
    """Return a CSS block that applies the theme globally."""
    return f"""
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    );
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    .stApp {{
        background: linear-gradient(
            135deg, {THEME.bg_primary} 0%, {THEME.bg_secondary} 100%
        );
    }}
    .metric-card {{
        background: {THEME.bg_card};
        border: 1px solid {THEME.border};
        border-radius: 12px;
        padding: 1.25rem;
    }}
    .metric-card h3 {{
        color: {THEME.text_secondary};
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0 0 0.4rem 0;
    }}
    .metric-card .value {{
        color: {THEME.text_primary};
        font-size: 1.75rem;
        font-weight: 700;
    }}
    .badge {{
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge-success {{
        background: {THEME.success}22;
        color: {THEME.success};
    }}
    .badge-warning {{
        background: {THEME.warning}22;
        color: {THEME.warning};
    }}
    .badge-error {{
        background: {THEME.error}22;
        color: {THEME.error};
    }}
    </style>
    """
