"""Relationship Detector for AI Back-Office Copilot.

Discovers empirical correlations and structural relationships between columns
without asserting causal conclusions.
"""
from __future__ import annotations

from typing import Any
import pandas as pd
from pydantic import BaseModel, Field

from app.ai.dataset.semantic_mapper import SemanticColumnMapping


class DetectedRelationship(BaseModel):
    source_column: str
    target_column: str
    relationship_type: str  # correlation, functional_dependency, hierarchy
    metric_value: float | None = None
    description: str


class RelationshipDetector:
    """Discovers relationships, correlations, and hierarchies between columns."""

    @classmethod
    def detect_relationships(
        cls,
        df: pd.DataFrame,
        columns: list[SemanticColumnMapping],
    ) -> list[DetectedRelationship]:
        relationships: list[DetectedRelationship] = []
        numeric_cols = [c.original_name for c in columns if c.role == "measure" and c.original_name in df.columns]

        # 1. Pearson correlations between numeric measures
        if len(numeric_cols) >= 2 and len(df) > 10:
            try:
                corr_matrix = df[numeric_cols].corr(numeric_only=True)
                for i in range(len(numeric_cols)):
                    for j in range(i + 1, len(numeric_cols)):
                        col_a = numeric_cols[i]
                        col_b = numeric_cols[j]
                        r_val = corr_matrix.loc[col_a, col_b]
                        if pd.notna(r_val) and abs(r_val) >= 0.35:
                            strength = "strong" if abs(r_val) >= 0.70 else "moderate"
                            direction = "positive" if r_val > 0 else "negative"
                            relationships.append(DetectedRelationship(
                                source_column=col_a,
                                target_column=col_b,
                                relationship_type="correlation",
                                metric_value=round(float(r_val), 3),
                                description=f"{strength.title()} {direction} correlation (r={round(float(r_val), 2)}) observed between {col_a} and {col_b}.",
                            ))
            except Exception:
                pass

        # 2. Hierarchical / Geographic groupings
        dim_cols = [c.original_name for c in columns if c.role in ("dimension", "geographic_dimension") and c.original_name in df.columns]
        if "Region" in df.columns and "City" in df.columns:
            relationships.append(DetectedRelationship(
                source_column="Region",
                target_column="City",
                relationship_type="hierarchy",
                description="Geographic hierarchy: Region contains City groupings.",
            ))

        return relationships
