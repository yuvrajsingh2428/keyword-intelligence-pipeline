"""Base data model for the Keyword Intelligence Pipeline.

Provides a shared Pydantic BaseModel subclass with project-wide
configuration. All domain data models should inherit from
AppBaseModel to ensure consistent serialization, validation,
and behavior across the application.

Usage:
    from keyword_intelligence.models.base import AppBaseModel

    class Keyword(AppBaseModel):
        term: str
        search_volume: int
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """Base model with shared Pydantic configuration.

    All application data models should inherit from this class to
    ensure consistent behavior:
    - Attribute access via .field_name (not just dict-style)
    - Whitespace stripped from string fields
    - ORM/dataclass compatibility via from_attributes
    - Strict validation that rejects unexpected fields

    Attributes are configured via model_config rather than
    individual Field() calls for DRY consistency.
    """

    model_config = ConfigDict(
        # Allow constructing models from ORM objects / dataclasses
        from_attributes=True,
        # Strip leading/trailing whitespace from string fields
        str_strip_whitespace=True,
        # Validate field values on assignment, not just construction
        validate_assignment=True,
        # Use enum values (not enum members) in serialization
        use_enum_values=True,
        # Forbid extra fields to catch typos and schema drift
        extra="forbid",
    )
