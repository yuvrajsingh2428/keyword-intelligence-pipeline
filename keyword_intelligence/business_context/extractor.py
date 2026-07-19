"""Structured deterministic extractor."""

from __future__ import annotations

from loguru import logger

from keyword_intelligence.business_context.extractors import (
    HeadingExtractor,
    NavigationExtractor,
    SchemaOrgExtractor,
    URLExtractor,
)
from keyword_intelligence.business_context.models import (
    BusinessFacts,
    BusinessProfile,
    CollectedContent,
    EntityEvidence,
    Relationship,
)
from keyword_intelligence.business_context.normalizer import EntityNormalizer


class StructuredExtractor:
    """Orchestrates modular extractors and populates BusinessFacts."""

    def __init__(self) -> None:
        self.extractors = [
            NavigationExtractor(),
            HeadingExtractor(),
            URLExtractor(),
            SchemaOrgExtractor(),
        ]
        self.normalizer = EntityNormalizer()

    def extract(
        self,
        company_name: str,
        website_url: str,
        industry: str,
        contents: list[CollectedContent],
    ) -> BusinessProfile:
        """Create a draft BusinessProfile containing deterministically extracted facts."""
        logger.info("Orchestrating modular extractors to build BusinessFacts.")

        draft = BusinessProfile(
            company_name=company_name,
            website=website_url,
            industry=industry,
        )
        facts = BusinessFacts()

        raw_entities = []
        raw_relations = []

        # 1. Run all modular extractors
        for content in contents:
            if not content.html:
                continue

            for extractor in self.extractors:
                try:
                    ents, rels = extractor.extract(content.html, content.source_url)
                    raw_entities.extend(ents)
                    raw_relations.extend(rels)
                except Exception as e:
                    logger.warning(
                        f"{extractor.__class__.__name__} failed on {content.source_url}: {e}"
                    )

        # 2. Normalize and group entities to build evidence
        grouped_entities = {}
        for ent in raw_entities:
            norm_name = self.normalizer.normalize_name(ent.entity)
            if not norm_name:
                continue

            norm_type = self.normalizer.normalize_type(ent.entity_type)

            if norm_name not in grouped_entities:
                grouped_entities[norm_name] = {"type": norm_type, "sources": set()}
            grouped_entities[norm_name]["sources"].add(ent.source)

        # 3. Populate facts lists
        for name, data in grouped_entities.items():
            sources = list(data["sources"])
            evidence = EntityEvidence(
                entity=name,
                entity_type=data["type"],
                evidence_sources=sources,
                confidence_score=float(
                    len(sources)
                ),  # Score based on evidence strength
            )

            if data["type"] == "Brand":
                facts.brands.append(evidence)
            elif data["type"] == "ProductFamily":
                facts.product_families.append(evidence)
            elif data["type"] == "Category":
                facts.categories.append(evidence)
            elif data["type"] == "Service":
                facts.services.append(evidence)
            else:
                facts.products.append(evidence)

        # 4. Normalize and build relationships & taxonomy
        added_rels = set()
        for rel in raw_relations:
            norm_src = self.normalizer.normalize_name(rel.source_entity)
            norm_tgt = self.normalizer.normalize_name(rel.target_entity)

            if not norm_src or not norm_tgt or norm_src == norm_tgt:
                continue

            rel_key = f"{norm_src}:{rel.relation_type}:{norm_tgt}"
            if rel_key not in added_rels:
                facts.relationships.append(
                    Relationship(
                        source=norm_src,
                        relation_type=rel.relation_type,
                        target=norm_tgt,
                    )
                )
                added_rels.add(rel_key)

                if rel.relation_type == "belongs_to":
                    if norm_tgt not in facts.taxonomy:
                        facts.taxonomy[norm_tgt] = []
                    if norm_src not in facts.taxonomy[norm_tgt]:
                        facts.taxonomy[norm_tgt].append(norm_src)

        draft.business_facts = facts
        return draft
