"""Smoke tests for the Keyword Intelligence Pipeline.

Verifies that core infrastructure components are importable, correctly
configured, and functional. These tests should always pass as a basic
health check of the project foundation.
"""

from __future__ import annotations

import pytest


class TestPackageImports:
    """Verify that the main package and subpackages are importable."""

    @pytest.mark.smoke
    def test_package_is_importable(self) -> None:
        import keyword_intelligence

        assert keyword_intelligence is not None

    @pytest.mark.smoke
    def test_version_is_exported(self) -> None:
        from keyword_intelligence import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    @pytest.mark.smoke
    def test_version_is_valid_semver(self) -> None:
        from keyword_intelligence import __version__
        from keyword_intelligence.utils.helpers import is_valid_semver

        assert is_valid_semver(__version__)

    @pytest.mark.smoke
    def test_app_name_is_exported(self) -> None:
        from keyword_intelligence import __app_name__

        assert isinstance(__app_name__, str)
        assert len(__app_name__) > 0

    @pytest.mark.smoke
    def test_subpackages_are_importable(self) -> None:
        import importlib

        subpackages = [
            "keyword_intelligence.config",
            "keyword_intelligence.core",
            "keyword_intelligence.models",
            "keyword_intelligence.services",
            "keyword_intelligence.pipeline",
            "keyword_intelligence.utils",
            "keyword_intelligence.ui",
        ]
        for pkg in subpackages:
            module = importlib.import_module(pkg)
            assert module is not None


class TestMetadata:
    """Verify that application metadata is correctly defined."""

    @pytest.mark.smoke
    def test_metadata_fields_exist(self) -> None:
        from keyword_intelligence.metadata import (
            APP_NAME,
            AUTHOR,
            DESCRIPTION,
            LICENSE,
            REPOSITORY_URL,
            VERSION,
        )

        assert isinstance(APP_NAME, str) and len(APP_NAME) > 0
        assert isinstance(VERSION, str) and len(VERSION) > 0
        assert isinstance(DESCRIPTION, str) and len(DESCRIPTION) > 0
        assert isinstance(AUTHOR, str) and len(AUTHOR) > 0
        assert isinstance(REPOSITORY_URL, str) and len(REPOSITORY_URL) > 0
        assert isinstance(LICENSE, str) and len(LICENSE) > 0

    @pytest.mark.smoke
    def test_version_matches_init(self) -> None:
        from keyword_intelligence import __version__
        from keyword_intelligence.metadata import VERSION

        assert __version__ == VERSION


class TestConstants:
    """Verify that constants are correctly defined."""

    @pytest.mark.smoke
    def test_environment_enum_values(self) -> None:
        from keyword_intelligence.constants import Environment

        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

    @pytest.mark.smoke
    def test_log_format_enum_values(self) -> None:
        from keyword_intelligence.constants import LogFormat

        assert LogFormat.CONSOLE == "console"
        assert LogFormat.JSON == "json"

    @pytest.mark.smoke
    def test_log_level_enum_values(self) -> None:
        from keyword_intelligence.constants import LogLevel

        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestExceptions:
    """Verify the exception hierarchy."""

    @pytest.mark.smoke
    def test_base_exception_exists(self) -> None:
        from keyword_intelligence.core.exceptions import KeywordIntelligenceError

        assert issubclass(KeywordIntelligenceError, Exception)

    @pytest.mark.smoke
    def test_configuration_error_hierarchy(self) -> None:
        from keyword_intelligence.core.exceptions import (
            ConfigurationError,
            KeywordIntelligenceError,
        )

        assert issubclass(ConfigurationError, KeywordIntelligenceError)

    @pytest.mark.smoke
    def test_initialization_error_hierarchy(self) -> None:
        from keyword_intelligence.core.exceptions import (
            InitializationError,
            KeywordIntelligenceError,
        )

        assert issubclass(InitializationError, KeywordIntelligenceError)

    @pytest.mark.smoke
    def test_exception_message_and_detail(self) -> None:
        from keyword_intelligence.core.exceptions import ConfigurationError

        error = ConfigurationError("Missing API key", detail="Set AI_API_KEY env var")
        assert str(error) == "Missing API key — Set AI_API_KEY env var"
        assert error.message == "Missing API key"
        assert error.detail == "Set AI_API_KEY env var"

    @pytest.mark.smoke
    def test_exception_without_detail(self) -> None:
        from keyword_intelligence.core.exceptions import ConfigurationError

        error = ConfigurationError("Something failed")
        assert str(error) == "Something failed"
        assert error.detail is None


class TestLogger:
    """Verify the logger factory."""

    @pytest.mark.smoke
    def test_get_logger_returns_logger(self) -> None:
        from keyword_intelligence.core.logger import get_logger

        logger = get_logger("test_module")
        assert logger is not None

    @pytest.mark.smoke
    def test_logger_can_log_without_error(self) -> None:
        from keyword_intelligence.core.logger import get_logger

        logger = get_logger("test_module")
        # Should not raise any exception
        logger.info("Smoke test log message")


class TestBaseModel:
    """Verify the base Pydantic model configuration."""

    @pytest.mark.smoke
    def test_app_base_model_importable(self) -> None:
        from keyword_intelligence.models.base import AppBaseModel

        assert AppBaseModel is not None

    @pytest.mark.smoke
    def test_app_base_model_strips_whitespace(self) -> None:
        from keyword_intelligence.models.base import AppBaseModel

        class TestModel(AppBaseModel):
            name: str

        instance = TestModel(name="  hello  ")
        assert instance.name == "hello"

    @pytest.mark.smoke
    def test_app_base_model_forbids_extra(self) -> None:
        from pydantic import ValidationError

        from keyword_intelligence.models.base import AppBaseModel

        class TestModel(AppBaseModel):
            name: str

        with pytest.raises(ValidationError):
            TestModel(name="hello", unknown_field="value")  # type: ignore[call-arg]
