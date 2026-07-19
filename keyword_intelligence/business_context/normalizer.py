"""Normalizes extracted entities to canonical forms."""

from __future__ import annotations

import re


class EntityNormalizer:
    """Normalizes entities and resolves synonyms."""

    def __init__(self) -> None:
        # Map common variations to canonical categories/products
        self.mappings = {
            "usb c dock": "Docking Station",
            "usb-c dock": "Docking Station",
            "usb hub": "Docking Station",
            "usb-c hub": "Docking Station",
            "notebook": "Laptop",
            "notebook pc": "Laptop",
            "wireless mouse": "Mouse",
            "bluetooth mouse": "Mouse",
            "ergonomic mouse": "Mouse",
            "wireless keyboard": "Keyboard",
            "mechanical keyboard": "Keyboard",
            "desktop computer": "Desktop",
            "desktop pc": "Desktop",
        }

    def normalize_name(self, name: str) -> str:
        """Normalize the entity name to a canonical form."""
        if not name:
            return ""

        clean = re.sub(r"\s+", " ", name.strip())
        lower = clean.lower()

        # Exact match override
        if lower in self.mappings:
            return self.mappings[lower]

        # Optional: return exact original casing rather than Title Case for uniformity
        return clean

    def normalize_type(self, entity_type: str) -> str:
        """Ensure the entity type matches our canonical types."""
        valid_types = {"Brand", "ProductFamily", "Category", "Product", "Service"}
        if entity_type not in valid_types:
            return "Product"  # Default fallback
        return entity_type
