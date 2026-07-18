"""General-purpose utility functions for the Keyword Intelligence Pipeline.

Contains stateless, pure helper functions with no domain knowledge.
These utilities are safe to use from any module without introducing
circular dependencies.

Usage:
    from keyword_intelligence.utils.helpers import sanitize_string, ensure_directory
"""

from __future__ import annotations

import re
from pathlib import Path


def sanitize_string(value: str) -> str:
    """Normalize a string by stripping whitespace and collapsing internal spaces.

    Args:
        value: The input string to sanitize.

    Returns:
        The sanitized string with leading/trailing whitespace removed
        and consecutive internal whitespace collapsed to a single space.

    Examples:
        >>> sanitize_string("  hello   world  ")
        'hello world'
        >>> sanitize_string("")
        ''
    """
    return re.sub(r"\s+", " ", value.strip())


def ensure_directory(path: Path) -> Path:
    """Create a directory (and parents) if it does not exist.

    Args:
        path: The directory path to ensure exists.

    Returns:
        The same path, guaranteed to exist as a directory.

    Raises:
        OSError: If the path exists but is not a directory, or if
            directory creation fails due to permissions.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def truncate_string(value: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length with an ellipsis suffix.

    Args:
        value: The input string to truncate.
        max_length: Maximum allowed length (including suffix).
        suffix: The string to append when truncating.

    Returns:
        The original string if it fits within max_length,
        otherwise the truncated string with suffix appended.

    Examples:
        >>> truncate_string("hello", max_length=10)
        'hello'
        >>> truncate_string("hello world", max_length=8)
        'hello...'
    """
    if len(value) <= max_length:
        return value
    return value[: max_length - len(suffix)] + suffix


def is_valid_semver(version: str) -> bool:
    """Check whether a string is a valid semantic version (MAJOR.MINOR.PATCH).

    Args:
        version: The version string to validate.

    Returns:
        True if the string matches semver format, False otherwise.

    Examples:
        >>> is_valid_semver("1.0.0")
        True
        >>> is_valid_semver("1.0")
        False
    """
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version))
