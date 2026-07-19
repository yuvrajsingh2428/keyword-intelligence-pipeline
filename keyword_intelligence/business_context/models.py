"""Business Context models."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from keyword_intelligence.models.base import AppBaseModel


class EntityEvidence(AppBaseModel):
    """Deterministically extracted entity with evidence-based confidence."""

    entity: str
    entity_type: str
    evidence_sources: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0


class Relationship(AppBaseModel):
    """A simple relationship between two entities."""

    source: str
    relation_type: str
    target: str


class BusinessFacts(AppBaseModel):
    """Deterministically extracted facts from the retailer website."""

    brands: list[EntityEvidence] = Field(default_factory=list)
    product_families: list[EntityEvidence] = Field(default_factory=list)
    categories: list[EntityEvidence] = Field(default_factory=list)
    products: list[EntityEvidence] = Field(default_factory=list)
    services: list[EntityEvidence] = Field(default_factory=list)

    # Simple in-memory relationships (e.g. ThinkPad belongs_to Laptop)
    relationships: list[Relationship] = Field(default_factory=list)

    # Hierarchical taxonomy: parent_category -> [child_categories]
    taxonomy: dict[str, list[str]] = Field(default_factory=dict)

    aliases: dict[str, str] = Field(default_factory=dict)
    synonyms: dict[str, list[str]] = Field(default_factory=dict)


class ProfileMetadata(AppBaseModel):
    """Metadata enabling cache invalidation and reproducibility."""

    profile_version: str = "2.0.0"
    generator_version: str = "2.0.0"
    collector_version: str = "2.0.0"
    llm_model: str = ""
    quality_score: float = 0.0
    source_pages: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class BusinessProfile(AppBaseModel):
    """The canonical representation of the business, split into deterministic and LLM layers."""

    company_name: str
    website: str

    # LLM Enriched Knowledge
    industry: str = ""
    business_description: str = ""
    customer_segments: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    important_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    business_concepts: list[str] = Field(default_factory=list)

    # Deterministic Business Facts
    business_facts: BusinessFacts = Field(default_factory=BusinessFacts)

    metadata: ProfileMetadata = Field(default_factory=ProfileMetadata)


class CollectedContent(AppBaseModel):
    """Raw data collected from a provider."""

    source_url: str
    title: str = ""
    clean_text: str = ""
    html: str = ""
