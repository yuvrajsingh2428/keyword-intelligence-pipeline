"""Base extractor interfaces."""

from __future__ import annotations

from typing import Literal

from keyword_intelligence.models.base import AppBaseModel


class ExtractedEntity(AppBaseModel):
    """Raw entity extracted by a single extractor."""

    entity: str
    entity_type: Literal["Brand", "ProductFamily", "Category", "Product", "Service"]
    source: str


class ExtractedRelation(AppBaseModel):
    """Raw relationship extracted by a single extractor."""

    source_entity: str
    relation_type: str
    target_entity: str


class BaseExtractor:
    """Base class for all modular extractors."""

    def extract(
        self, html: str, url: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        """Extract entities and relations from the given HTML and URL.

        Args:
            html: Raw HTML content.
            url: The source URL.

        Returns:
            Tuple of (entities, relations).
        """
        raise NotImplementedError
