"""Column Resolver core implementation."""

from pathlib import Path

import yaml
from loguru import logger
from rapidfuzz import fuzz

from keyword_intelligence.column_resolver.exceptions import KeywordColumnNotFoundError
from keyword_intelligence.column_resolver.models import (
    ColumnResolutionResult,
    ResolutionMethod,
)


class ColumnResolver:
    """Detects and resolves keyword columns intelligently."""

    def __init__(
        self, config_dir: str | Path | None = None, fuzzy_threshold: float = 90.0
    ) -> None:
        """Initialize the ColumnResolver.

        Args:
            config_dir: Path to the directory containing column_aliases.yaml.
            fuzzy_threshold: Minimum RapidFuzz match score to consider a fuzzy match (0-100).
        """
        self.fuzzy_threshold = fuzzy_threshold
        if config_dir is None:
            # Default to the config directory relative to this file
            config_dir = Path(__file__).parent.parent / "config"

        self.aliases_path = Path(config_dir) / "column_aliases.yaml"
        self.aliases: list[str] = self._load_aliases()

    def _load_aliases(self) -> list[str]:
        """Load configured aliases from YAML."""
        if not self.aliases_path.exists():
            logger.warning(
                f"Alias config not found at {self.aliases_path}. Proceeding with default 'keyword'."
            )
            return ["keyword"]

        try:
            with open(self.aliases_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return [str(a).lower() for a in config.get("aliases", [])]
        except Exception as e:
            logger.error(f"Failed to load column aliases: {e}")
            return ["keyword"]

    def resolve(self, columns: list[str]) -> list[ColumnResolutionResult]:
        """Resolve candidates for the keyword column.

        Returns:
            A list of valid ColumnResolutionResult candidates, sorted by confidence descending.

        Raises:
            KeywordColumnNotFoundError: If no column matches exactly, by alias, or fuzzily above threshold.
        """
        candidates: list[ColumnResolutionResult] = []

        for col in columns:
            normalized_col = str(col).lower().strip()

            # 1. Exact Match
            if normalized_col == "keyword":
                candidates.append(
                    ColumnResolutionResult(
                        original_column=col,
                        method=ResolutionMethod.EXACT,
                        confidence_score=100.0,
                    )
                )
                continue

            # 2. Alias Match
            if normalized_col in self.aliases:
                candidates.append(
                    ColumnResolutionResult(
                        original_column=col,
                        method=ResolutionMethod.ALIAS,
                        confidence_score=95.0,  # High confidence for explicit alias
                    )
                )
                continue

            # 3. Fuzzy Match
            # Compare against all aliases and take the best score
            best_score = 0.0
            for alias in self.aliases:
                score = fuzz.ratio(normalized_col, alias)
                if score > best_score:
                    best_score = score

            if best_score >= self.fuzzy_threshold:
                candidates.append(
                    ColumnResolutionResult(
                        original_column=col,
                        method=ResolutionMethod.FUZZY,
                        confidence_score=round(best_score, 2),
                    )
                )

        if not candidates:
            raise KeywordColumnNotFoundError(
                f"Could not automatically identify a keyword column among: {columns}"
            )

        # Sort candidates by confidence descending
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        return candidates
