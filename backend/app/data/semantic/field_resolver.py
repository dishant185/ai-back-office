"""Universal semantic field resolver.

Maps natural language query tokens (e.g. 'rep', 'turnover', 'margin')
to the actual physical column in the active dataset schema.
"""
from __future__ import annotations

from typing import Any
from rapidfuzz import process, fuzz

from app.data.semantic.schema_builder import SemanticSchema


class FieldResolver:
    """Resolves natural language tokens to physical columns in a dataset."""

    def __init__(self, schema: SemanticSchema) -> None:
        self.schema = schema
        self._col_lookup: dict[str, str] = {}

        for col in schema.columns:
            orig = col.original_name
            self._col_lookup[orig.lower()] = orig
            self._col_lookup[col.semantic_name.lower()] = orig
            self._col_lookup[orig.lower().replace(" ", "_").replace("-", "_")] = orig
            self._col_lookup[col.semantic_name.lower().replace("_", " ")] = orig

    def resolve_field(self, token: str) -> str | None:
        """Find the physical column name matching a natural query token."""
        clean = token.strip().lower()

        # 1. Exact match
        if clean in self._col_lookup:
            return self._col_lookup[clean]

        clean_norm = clean.replace(" ", "_").replace("-", "_")
        if clean_norm in self._col_lookup:
            return self._col_lookup[clean_norm]

        # 2. Fuzzy match against all known candidates
        candidates = list(self._col_lookup.keys())
        match = process.extractOne(clean, candidates, scorer=fuzz.token_sort_ratio, score_cutoff=75)
        if match:
            return self._col_lookup[match[0]]

        return None

    def resolve_measure(self, token: str) -> str | None:
        """Resolve specifically to a measure column."""
        field = self.resolve_field(token)
        if field and field in self.schema.measures:
            return field
        # Check if matched field has numeric data type
        col = self.schema.get_column(field) if field else None
        if col and col.data_type == "numeric":
            return col.original_name
        return None

    def resolve_dimension(self, token: str) -> str | None:
        """Resolve specifically to a dimension column."""
        field = self.resolve_field(token)
        if field and (field in self.schema.dimensions or field in self.schema.date_fields):
            return field
        col = self.schema.get_column(field) if field else None
        if col and col.role in ("dimension", "geographic_dimension", "time_dimension"):
            return col.original_name
        return None
