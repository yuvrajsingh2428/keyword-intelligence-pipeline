"""Integration test for Business Context pipeline."""

import pytest

from keyword_intelligence.business_context.engine import BusinessContextEngine
from keyword_intelligence.business_context.filter import DeterministicFilter
from keyword_intelligence.business_context.models import CollectedContent
from keyword_intelligence.config.settings import get_settings
from keyword_intelligence.core.bootstrap import bootstrap
from keyword_intelligence.core.container import container


@pytest.fixture(scope="module")
def setup_container():
    bootstrap()
    yield container


def test_business_context_pipeline(setup_container):
    """
    Input: Lenovo, https://www.lenovo.com/in/en
    Dataset: ThinkPad, Running Shoes, Diamond Rings, Gaming Laptop, Yoga 9i
    """
    settings = get_settings()
    engine = setup_container.resolve(BusinessContextEngine)

    # 1. Generate BusinessProfile
    company = "Lenovo"
    website = "https://www.lenovo.com/in/en"

    # Mock collector to avoid flaky live website dependencies
    from unittest.mock import patch

    mock_html = """
    <html>
        <head><title>Lenovo Official Site</title></head>
        <body>
            <nav>
                <ul>
                    <li><a href="/thinkpad-x1">ThinkPad Laptops</a></li>
                    <li><a href="/thinkpad-t">ThinkPad T Series</a></li>
                    <li><a href="/yoga-9i">Yoga 9i</a></li>
                    <li><a href="/yoga-7i">Yoga 7i</a></li>
                    <li><a href="/gaming">Gaming Laptop</a></li>
                </ul>
            </nav>
        </body>
    </html>
    """
    with patch(
        "keyword_intelligence.business_context.collectors.website.WebsiteCollector.collect"
    ) as mock_collect:
        mock_collect.return_value = [
            CollectedContent(
                source_url=website,
                html=mock_html,
                title="Lenovo Official Site",
                clean_text="ThinkPad Laptops Yoga 9i Gaming Laptop",
            )
        ]
        profile = engine.process(company, website, force_refresh=True)

    # Assertions for generation
    assert profile is not None
    assert profile.company_name == "Lenovo"
    assert profile.website == website

    # Verify we extracted key products/brands
    brand_names = [b.entity.lower() for b in profile.business_facts.brands]
    product_names = [p.entity.lower() for p in profile.business_facts.products]
    family_names = [f.entity.lower() for f in profile.business_facts.product_families]
    category_names = [c.entity.lower() for c in profile.business_facts.categories]

    # LLM might classify them in different taxonomy buckets, so we check union
    all_names = set(brand_names + product_names + family_names + category_names)

    # We can't guarantee exact casing or exact LLM extraction, but we expect these to be found on Lenovo's site.
    # Note: If this fails, the LLM or collector failed to grab the homepage properly.
    assert len(all_names) > 0, "No entities were extracted from the business profile."

    # 2. Run Deterministic Filter
    det_filter = DeterministicFilter(profile)

    keywords = [
        "ThinkPad",
        "Running Shoes",
        "Diamond Rings",
        "Gaming Laptop",
        "Yoga 9i",
    ]

    results = {}
    for kw in keywords:
        rel, conf, reason = det_filter.classify(kw)
        results[kw] = rel.value if rel else "UNCERTAIN"

    # Assertions
    assert results["ThinkPad"] == "RELEVANT"
    assert results["Yoga 9i"] == "RELEVANT"

    # Running shoes and Diamond rings might not be known negatives,
    # but they MUST NOT be classified as RELEVANT deterministically.
    assert results["Running Shoes"] != "RELEVANT"
    assert results["Diamond Rings"] != "RELEVANT"
