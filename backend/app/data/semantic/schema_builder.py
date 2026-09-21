"""Universal Semantic Schema Builder.

Infers semantic roles, standardized names, and domain profiles without
forcing sales requirements on HR, Inventory, or Generic datasets.
"""
from __future__ import annotations

import re
from typing import Any
import pandas as pd
from pydantic import BaseModel

from app.data.semantic.aliases import DOMAIN_ALIASES
from app.data.semantic.type_detector import detect_column_data_type, detect_column_role


class ColumnSemantic(BaseModel):
    original_name: str
    semantic_name: str
    data_type: str  # numeric, categorical, date, datetime, text, boolean
    role: str       # measure, dimension, time_dimension, geographic_dimension, identifier
    confidence: float
    mapping_source: str  # exact, alias, pattern, inferred


class SemanticSchema(BaseModel):
    profile: str  # sales, hr, inventory, customer, finance, generic
    domain_profile: str | None = None
    columns: list[ColumnSemantic]
    dimensions: list[str]
    measures: list[str]
    date_fields: list[str]
    identifiers: list[str]
    quality_issues: list[str] = []

    def get_column(self, name: str) -> ColumnSemantic | None:
        clean = name.strip().lower().replace(" ", "_").replace("-", "_")
        for col in self.columns:
            c_clean = col.original_name.strip().lower().replace(" ", "_").replace("-", "_")
            if c_clean == clean or col.semantic_name == clean:
                return col
        return None


def _normalize_token(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")


def build_semantic_schema(frame: pd.DataFrame) -> SemanticSchema:
    """Analyze a DataFrame and produce a standardized, validated semantic schema."""
    column_semantics: list[ColumnSemantic] = []
    dimensions: list[str] = []
    measures: list[str] = []
    date_fields: list[str] = []
    identifiers: list[str] = []
    quality_issues: list[str] = []

    # Count potential domain matches
    domain_scores: dict[str, int] = {"sales": 0, "hr": 0, "inventory": 0, "customer": 0, "finance": 0}

    for col in frame.columns:
        col_str = str(col)
        norm_name = _normalize_token(col_str)
        series = frame[col]

        data_type = detect_column_data_type(series)
        role = detect_column_role(col_str, data_type, series)

        # Match against domain aliases
        matched_semantic: str | None = None
        matched_domain: str | None = None
        confidence = 0.5
        mapping_source = "inferred"

        for dom, aliases_map in DOMAIN_ALIASES.items():
            for canonical, aliases in aliases_map.items():
                if norm_name == canonical or norm_name in aliases:
                    matched_semantic = canonical
                    matched_domain = dom
                    confidence = 0.95
                    mapping_source = "exact_alias"
                    domain_scores[dom] += 2
                    break
                # Partial token match
                if any(alias in norm_name for alias in aliases if len(alias) >= 4):
                    if not matched_semantic:
                        matched_semantic = canonical
                        matched_domain = dom
                        confidence = 0.8
                        mapping_source = "partial_alias"
                    domain_scores[dom] += 1

        semantic_name = matched_semantic or norm_name

        # Refine role based on semantic name
        if semantic_name in ("transaction_date", "joining_year", "hire_date", "date"):
            role = "time_dimension"
        elif semantic_name in ("region", "city", "state", "location"):
            role = "geographic_dimension"
        elif semantic_name in ("sales_amount", "quantity", "unit_price", "unit_cost", "discount", "stock_quantity", "age", "experience"):
            if data_type == "numeric":
                role = "measure"

        # Check quality issues for this column
        missing_count = int(series.isna().sum())
        if missing_count > 0 and missing_count == len(series):
            quality_issues.append(f"Column '{col_str}' is completely empty.")
        elif series.nunique(dropna=True) == 1 and len(series) > 1:
            quality_issues.append(f"Column '{col_str}' has a constant single value.")

        col_obj = ColumnSemantic(
            original_name=col_str,
            semantic_name=semantic_name,
            data_type=data_type,
            role=role,
            confidence=confidence,
            mapping_source=mapping_source,
        )
        column_semantics.append(col_obj)

        if role in ("dimension", "geographic_dimension"):
            dimensions.append(col_str)
        elif role == "measure":
            measures.append(col_str)
        elif role == "time_dimension":
            date_fields.append(col_str)
        elif role == "identifier":
            identifiers.append(col_str)

    # Determine highest scoring profile
    top_domain = max(domain_scores, key=domain_scores.get)
    profile = top_domain if domain_scores[top_domain] >= 2 else "generic"

    return SemanticSchema(
        profile=profile,
        domain_profile=profile,
        columns=column_semantics,
        dimensions=dimensions,
        measures=measures,
        date_fields=date_fields,
        identifiers=identifiers,
        quality_issues=quality_issues,
    )


class SemanticSchemaBuilder:
    @classmethod
    def build(cls, frame: pd.DataFrame) -> SemanticSchema:
        return build_semantic_schema(frame)

