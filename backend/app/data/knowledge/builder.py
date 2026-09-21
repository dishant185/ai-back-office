"""Dataset Knowledge package builder.

Extracts semantic schema, capabilities, cardinalities, and statistics
to create the dataset's operational memory.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

from app.data.semantic.schema_builder import build_semantic_schema, SemanticSchema
from app.data.semantic.capability_detector import detect_capabilities
from app.data.knowledge.models import DatasetKnowledgePackage


def build_dataset_knowledge(
    frame: pd.DataFrame,
    dataset_id: str,
    account_id: str,
    file_name: str,
    file_type: str = "csv",
) -> DatasetKnowledgePackage:
    """Build full knowledge package from a DataFrame."""
    schema = build_semantic_schema(frame)
    capabilities = detect_capabilities(schema)

    column_mappings: dict[str, str] = {}
    dimension_cardinalities: dict[str, int] = {}
    measure_stats: dict[str, dict[str, Any]] = {}

    for col in schema.columns:
        column_mappings[col.semantic_name] = col.original_name
        orig = col.original_name

        if col.role in ("dimension", "geographic_dimension"):
            dimension_cardinalities[orig] = int(frame[orig].nunique(dropna=True))

        elif col.role == "measure" and col.data_type == "numeric":
            series = pd.to_numeric(frame[orig], errors="coerce").dropna()
            if not series.empty:
                measure_stats[orig] = {
                    "sum": float(series.sum()),
                    "avg": float(series.mean()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                }

    return DatasetKnowledgePackage(
        dataset_id=dataset_id,
        account_id=account_id,
        file_name=file_name,
        file_type=file_type,
        row_count=len(frame),
        column_count=len(frame.columns),
        profile=schema.profile,
        dimensions=schema.dimensions,
        measures=schema.measures,
        date_fields=schema.date_fields,
        capabilities=capabilities,
        quality_issues=schema.quality_issues,
        column_mappings=column_mappings,
        dimension_cardinalities=dimension_cardinalities,
        measure_stats=measure_stats,
    )
