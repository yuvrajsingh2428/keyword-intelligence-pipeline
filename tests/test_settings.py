"""Settings configuration tests for the Keyword Intelligence Pipeline.

Validates that the Settings class correctly loads defaults, accepts
environment variable overrides, enforces type constraints, and
rejects invalid values.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from keyword_intelligence.config.settings import Settings


class TestSettingsDefaults:
    """Verify default values when no environment variables are set."""

    @pytest.mark.settings
    def test_default_app_env(self, settings: Settings) -> None:
        assert settings.app_env == "development"

    @pytest.mark.settings
    def test_default_debug(self, settings: Settings) -> None:
        assert settings.debug is False

    @pytest.mark.settings
    def test_default_log_level(self, settings: Settings) -> None:
        assert settings.log_level == "INFO"

    @pytest.mark.settings
    def test_default_log_format(self, settings: Settings) -> None:
        assert settings.log_format == "console"

    @pytest.mark.settings
    def test_default_log_file_enabled(self, settings: Settings) -> None:
        assert settings.log_file_enabled is False

    @pytest.mark.settings
    def test_default_log_rotation(self, settings: Settings) -> None:
        assert settings.log_rotation == "10 MB"

    @pytest.mark.settings
    def test_default_log_retention(self, settings: Settings) -> None:
        assert settings.log_retention == "7 days"

    @pytest.mark.settings
    def test_default_app_title(self, settings: Settings) -> None:
        assert settings.app_title == "Keyword Intelligence Pipeline"


class TestSettingsOverrides:
    """Verify that environment variable overrides are applied."""

    @pytest.mark.settings
    def test_env_var_override_app_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.app_env == "production"

    @pytest.mark.settings
    def test_env_var_override_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.log_level == "DEBUG"

    @pytest.mark.settings
    def test_env_var_override_log_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_FORMAT", "json")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.log_format == "json"

    @pytest.mark.settings
    def test_env_var_override_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEBUG", "true")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.debug is True

    @pytest.mark.settings
    def test_debug_flag_accepts_numeric(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEBUG", "1")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.debug is True


class TestSettingsValidation:
    """Verify that invalid values are rejected with ValidationError."""

    @pytest.mark.settings
    def test_invalid_app_env_raises(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,  # type: ignore[call-arg]
                app_env="invalid_env",  # type: ignore[arg-type]
            )

    @pytest.mark.settings
    def test_invalid_log_level_raises(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,  # type: ignore[call-arg]
                log_level="TRACE",  # type: ignore[arg-type]
            )

    @pytest.mark.settings
    def test_invalid_log_format_raises(self) -> None:
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,  # type: ignore[call-arg]
                log_format="xml",  # type: ignore[arg-type]
            )


class TestSettingsProperties:
    """Verify computed properties."""

    @pytest.mark.settings
    def test_is_production_true(self, production_settings: Settings) -> None:
        assert production_settings.is_production is True

    @pytest.mark.settings
    def test_is_production_false(self, settings: Settings) -> None:
        assert settings.is_production is False

    @pytest.mark.settings
    def test_is_development_true(self, settings: Settings) -> None:
        assert settings.is_development is True

    @pytest.mark.settings
    def test_is_development_false(self, production_settings: Settings) -> None:
        assert production_settings.is_development is False

    @pytest.mark.settings
    def test_logs_dir_is_path(self, settings: Settings) -> None:
        from pathlib import Path

        assert isinstance(settings.logs_dir, Path)
        assert settings.logs_dir.name == "logs"
