"""Configurable expansion dictionary for abbreviation normalization."""

import json
from pathlib import Path

from loguru import logger


class NormalizationDictionary:
    """Manages abbreviation mappings for the DictionaryNormalizer.

    This class is designed to be easily extendable with additional
    terms as needed by the application and supports loading from JSON files.
    """

    def __init__(
        self,
        initial_mapping: dict[str, str] | None = None,
        dictionary_path: str | None = None,
        company_dictionary_path: str | None = None,
    ) -> None:
        """Initialize the dictionary with default or provided mappings."""
        # Standard dictionary
        self._mapping: dict[str, str] = {
            "ergo": "ergonomic",
            "tv": "television",
            "pc": "personal computer",
            "ssd drive": "ssd",
            "usb stick": "usb flash drive",
        }

        # Company specific dictionary
        self._company_mapping: dict[str, str] = {}

        if initial_mapping:
            self._mapping.update(initial_mapping)

        # Load from external files if provided
        if dictionary_path:
            self._load_from_file(dictionary_path, self._mapping)

        if company_dictionary_path:
            self._load_from_file(company_dictionary_path, self._company_mapping)

    def _load_from_file(self, path_str: str, target_dict: dict[str, str]) -> None:
        """Load key-value mappings from a JSON file into the target dictionary."""
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Normalization dictionary file not found: {path}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Ensure all keys and values are lowercase
                    for k, v in data.items():
                        target_dict[str(k).lower()] = str(v).lower()
                else:
                    logger.error(
                        f"Normalization dictionary must be a JSON object: {path}"
                    )
        except Exception as e:
            logger.error(f"Failed to load normalization dictionary {path}: {e}")

    def get_mapping(self) -> dict[str, str]:
        """Return the current abbreviation mapping."""
        return self._mapping.copy()

    def get_company_mapping(self) -> dict[str, str]:
        """Return the current company specific mapping."""
        return self._company_mapping.copy()

    def add_term(self, abbreviation: str, expansion: str) -> None:
        """Add a new abbreviation to the standard dictionary."""
        self._mapping[abbreviation.lower()] = expansion.lower()
