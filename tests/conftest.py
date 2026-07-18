"""Shared pytest fixtures for the Keyword Intelligence Pipeline test suite.

Provides reusable fixtures for isolated settings instances, environment
variable manipulation, and temporary directories. All fixtures are
function-scoped by default to ensure test isolation.
"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from keyword_intelligence.config.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    """Create a fresh Settings instance with default values.

    Returns a new Settings instance that is not cached, ensuring
    each test gets an isolated configuration. Does not read from
    .env files to avoid environment contamination.
    """
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
    )


@pytest.fixture()
def production_settings() -> Settings:
    """Create a Settings instance configured for production.

    Useful for testing production-specific behavior like JSON
    logging and debug mode disabled.
    """
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="production",
        debug=False,
        log_format="json",
        log_level="WARNING",
    )


@pytest.fixture()
def env_override() -> Generator[dict[str, str], None, None]:
    """Provide a context for overriding environment variables in tests.

    Yields a dictionary that is patched into os.environ. Modifications
    to the dictionary are reflected in the environment for the duration
    of the test.

    Usage:
        def test_something(env_override):
            env_override["APP_ENV"] = "production"
            settings = Settings()
            assert settings.app_env == "production"
    """
    overrides: dict[str, str] = {}
    with patch.dict("os.environ", overrides):
        yield overrides
