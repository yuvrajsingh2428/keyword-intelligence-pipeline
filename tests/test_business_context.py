"""Tests for Business Context Enrichment."""

import pytest

from keyword_intelligence.business_context.models import (
    BusinessFacts,
    BusinessProfile,
    EntityEvidence,
)
from keyword_intelligence.business_context.rule_engine import BusinessRuleEngine


@pytest.fixture
def test_profile():
    """Create a mock BusinessProfile for testing."""
    facts = BusinessFacts(
        brands=[
            EntityEvidence(entity="Lenovo", entity_type="Brand"),
            EntityEvidence(entity="Apple", entity_type="Brand"),
        ],
        categories=[
            EntityEvidence(entity="Laptop", entity_type="Category"),
        ],
        product_families=[
            EntityEvidence(entity="ThinkPad", entity_type="ProductFamily"),
        ],
        synonyms={
            "lenovo": [],
            "apple": ["mac"],
            "thinkpad": ["think pad", "think-pad"],
            "laptop": ["notebook"],
        },
        taxonomy={"Laptop": ["ThinkPad"]},
    )

    return BusinessProfile(
        company_name="Lenovo",
        website="lenovo.com",
        industry="Computers",
        business_facts=facts,
    )


@pytest.fixture
def engine(test_profile):
    """Provide a configured BusinessRuleEngine."""
    return BusinessRuleEngine(test_profile)


def test_product_family_match(engine):
    """Test deterministic match for a known product family."""
    ctx = engine.process("best thinkpad for business")

    assert ctx.product_family == "ThinkPad"
    assert ctx.brand == "Lenovo"
    assert ctx.category == "Laptop"
    assert ctx.retail_relevance is True
    assert ctx.requires_ai is False
    assert ctx.business_confidence == 1.0


def test_brand_and_category_match(engine):
    """Test deterministic match when both brand and category are present."""
    ctx = engine.process("cheap lenovo laptop")

    assert ctx.product_family is None
    assert ctx.brand == "Lenovo"
    assert ctx.category == "Laptop"
    assert ctx.retail_relevance is True
    assert ctx.requires_ai is False
    assert ctx.business_confidence > 0.8


def test_unknown_keyword(engine):
    """Test keyword that needs AI."""
    ctx = engine.process("cool tech gadget")

    assert ctx.brand is None
    assert ctx.category is None
    assert ctx.requires_ai is True
    assert ctx.retail_relevance is None
    assert ctx.business_confidence == 0.0
