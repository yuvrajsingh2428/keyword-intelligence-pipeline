"""Keyword Intelligence Pipeline.

An AI-powered keyword intelligence pipeline for automated keyword analysis,
clustering, and strategic content recommendations.
"""

from keyword_intelligence.metadata import APP_NAME, VERSION

__version__: str = VERSION
__app_name__: str = APP_NAME

__all__: list[str] = ["__app_name__", "__version__"]
