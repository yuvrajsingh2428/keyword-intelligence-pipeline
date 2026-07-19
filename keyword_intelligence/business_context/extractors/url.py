"""Extracts entities and hierarchy from URL paths."""

from __future__ import annotations

from urllib.parse import unquote, urlparse

from keyword_intelligence.business_context.extractors.base import (
    BaseExtractor,
    ExtractedEntity,
    ExtractedRelation,
)


class URLExtractor(BaseExtractor):
    """Infers categories and products from URL paths."""

    def extract(
        self, html: str, url: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        if not url:
            return entities, relations

        parsed = urlparse(url)
        path = unquote(parsed.path).strip("/")

        if not path:
            return entities, relations

        segments = [
            s.replace("-", " ").replace("_", " ").title() for s in path.split("/") if s
        ]

        # e.g. /laptops/gaming/legion-5
        # laptops (Category) -> gaming (Category) -> legion 5 (Product)

        for i, segment in enumerate(segments):
            if len(segment) < 3:
                continue

            entity_type = "Category" if i < len(segments) - 1 else "Product"
            entities.append(
                ExtractedEntity(entity=segment, entity_type=entity_type, source="URL")
            )

            if i > 0:
                parent = segments[i - 1]
                if len(parent) >= 3:
                    relations.append(
                        ExtractedRelation(
                            source_entity=segment,
                            relation_type="belongs_to",
                            target_entity=parent,
                        )
                    )

        return entities, relations
