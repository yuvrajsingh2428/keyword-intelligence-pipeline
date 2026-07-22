"""Tests for the ColumnResolver module."""

import pytest
import yaml

from keyword_intelligence.column_resolver.exceptions import KeywordColumnNotFoundError
from keyword_intelligence.column_resolver.models import ResolutionMethod
from keyword_intelligence.column_resolver.resolver import ColumnResolver


@pytest.fixture
def mock_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    aliases_file = config_dir / "column_aliases.yaml"
    aliases_data = {
        "aliases": [
            "keyword",
            "keywords",
            "search query",
            "search queries",
            "query",
            "queries",
            "search term",
            "search terms",
            "term",
            "keyword text",
            "organic keyword",
            "top queries",
            "search keyword",
        ]
    }
    with open(aliases_file, "w") as f:
        yaml.dump(aliases_data, f)

    return config_dir


@pytest.fixture
def resolver(mock_config_dir):
    return ColumnResolver(config_dir=mock_config_dir)


def test_exact_match(resolver):
    columns = ["date", "keyword", "volume"]
    results = resolver.resolve(columns)

    assert len(results) >= 1
    best = results[0]
    assert best.original_column == "keyword"
    assert best.method == ResolutionMethod.EXACT
    assert best.confidence_score == 100.0


def test_alias_match(resolver):
    columns = ["date", "Search Query", "volume"]
    results = resolver.resolve(columns)

    assert len(results) >= 1
    best = results[0]
    assert best.original_column == "Search Query"
    assert best.method == ResolutionMethod.ALIAS
    assert best.confidence_score == 95.0


def test_fuzzy_match(resolver):
    columns = ["date", "keyword_text", "volume"]
    # keyword_text is close to "keyword text"
    results = resolver.resolve(columns)

    assert len(results) >= 1
    best = results[0]
    assert best.original_column == "keyword_text"
    assert best.method == ResolutionMethod.FUZZY
    assert best.confidence_score >= 90.0


def test_no_match_raises_error(resolver):
    columns = ["date", "clicks", "impressions"]

    with pytest.raises(KeywordColumnNotFoundError):
        resolver.resolve(columns)


def test_multiple_candidates(resolver):
    columns = ["search term", "keyword", "query"]
    results = resolver.resolve(columns)

    # Should resolve all 3
    assert len(results) == 3

    # "keyword" should be EXACT (100.0)
    assert results[0].original_column == "keyword"
    assert results[0].method == ResolutionMethod.EXACT

    # "search term" should be ALIAS (95.0)
    # "query" should be ALIAS (95.0)
    methods = [r.method for r in results]
    assert methods.count(ResolutionMethod.ALIAS) == 2


def test_missing_config_falls_back_to_keyword(tmp_path):
    # No yaml file
    res = ColumnResolver(config_dir=tmp_path)

    results = res.resolve(["Keyword", "volume"])
    assert results[0].method == ResolutionMethod.EXACT

    with pytest.raises(KeywordColumnNotFoundError):
        res.resolve(["search query"])
