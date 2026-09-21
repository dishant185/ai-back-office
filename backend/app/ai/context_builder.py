"""Build structured canonical analytics context for the LLM.

Transforms deterministic analytics output into a compact authoritative context
that the AI can reason about — without ever seeing raw CSV rows or full datasets.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.analytics.capabilities import detect_capabilities
from app.analytics.engine import AnalyticsEngine
from app.analytics.metrics import build_metrics
from app.data.loader import DataLoader


def build_analytics_context(
    frame: pd.DataFrame,
    *,
    dataset_id: str | None = None,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a canonical structured context dict from a DataFrame.

    Parameters
    ----------
    frame:
        The standardized DataFrame.
    dataset_id:
        Optional dataset identifier.
    report_context:
        Optional extra context from a specific report.

    Returns
    -------
    Canonical analytics object ready for routing, verified answers, or LLM prompting.
    """
    cap_info = detect_capabilities(frame)
    profile = cap_info["profile"]
    capabilities_raw = cap_info["capabilities"]

    # Only keep active capabilities
    active_capabilities = [k for k, v in capabilities_raw.items() if v]

    # Build deterministic metrics
    metrics_list = build_metrics(frame, profile)
    metrics_dict: dict[str, Any] = {}
    for m in metrics_list:
        if m.value is not None:
            metrics_dict[m.name] = m.value

    # Summarize dimensions
    engine = AnalyticsEngine()
    dimensions_list = engine.summarize_dimensions(frame, profile)
    dimensions_dict: dict[str, Any] = {}
    for dim in dimensions_list:
        name = dim["name"]
        col = frame[name] if name in frame.columns else None
        if col is not None:
            counts = col.value_counts().head(15).to_dict()
            dimensions_dict[name] = {str(k): int(v) for k, v in counts.items()}

    # Column inventory
    columns_info = []
    available_fields = [str(col) for col in frame.columns]
    for col in frame.columns:
        dtype = str(frame[col].dtype)
        col_type = "numeric" if pd.api.types.is_numeric_dtype(frame[col]) else "categorical"
        columns_info.append({"name": str(col), "type": col_type, "dtype": dtype})

    context: dict[str, Any] = {
        "dataset_id": dataset_id or "live-dataset",
        "profile": profile,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "capabilities": active_capabilities,
        "metrics": metrics_dict,
        "dimensions": dimensions_dict,
        "available_fields": available_fields,
        "columns": columns_info,
    }

    if report_context:
        context["report_context"] = report_context

    return context


def build_compact_context_text(context: dict[str, Any]) -> str:
    """Format the canonical analytics object into a compact, authoritative text prompt."""
    profile = context.get("profile", "business").upper()
    row_count = context.get("row_count", 0)
    capabilities = context.get("capabilities", [])
    metrics = context.get("metrics", {})
    dimensions = context.get("dimensions", {})
    available_fields = context.get("available_fields", [])

    lines = [
        f"DATASET PROFILE:\n{profile}",
        f"ROWS:\n{row_count}",
        f"AVAILABLE CAPABILITIES:\n" + "\n".join(capabilities),
        "VERIFIED METRICS:",
    ]

    for k, v in metrics.items():
        lines.append(f"{k} = {v}")

    for dim_name, counts in dimensions.items():
        lines.append(f"VERIFIED {dim_name.upper()} COUNTS:")
        for k, v in list(counts.items())[:10]:
            lines.append(f"{k} = {v}")

    lines.append("AVAILABLE FIELDS:\n" + "\n".join(available_fields))
    lines.append("IMPORTANT:\nThese values are authoritative. Never invent numbers.")

    return "\n\n".join(lines)


def build_context_from_dataset_id(
    dataset_id: str,
    *,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a dataset by ID and build analytics context."""
    from pathlib import Path
    from app.core.config import settings

    dataset_path = Path(settings.upload_dir) / dataset_id
    if not dataset_path.exists():
        candidates = list(Path(settings.upload_dir).glob(f"{dataset_id}*"))
        if candidates:
            dataset_path = candidates[0]
        else:
            raise FileNotFoundError(f"Dataset {dataset_id} not found.")

    frame = DataLoader().load_file(dataset_path)
    return build_analytics_context(frame, dataset_id=dataset_id, report_context=report_context)
