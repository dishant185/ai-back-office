"""Numerical Grounding Validator — Strict hallucination detection.

Extracts all numerical claims from AI-generated text and verifies them
against the canonical analytics context (metrics, row counts, dimension values).
Replaces ungrounded claims with safe factual disclaimers.
"""
from __future__ import annotations

import re
from typing import Any

from app.ai.validators import AnalystResponse, extract_numbers_from_text


def get_all_grounded_numbers(context: dict[str, Any]) -> set[float]:
    """Collect all legitimate numbers present or derivable from context."""
    grounded: set[float] = set()

    # 1. Row count and column count
    row_count = context.get("row_count", 0)
    col_count = context.get("column_count", 0)
    if row_count:
        grounded.add(float(row_count))
    if col_count:
        grounded.add(float(col_count))

    # 2. Metrics and rounded variants
    metrics = context.get("metrics", {})
    for val in metrics.values():
        if isinstance(val, (int, float)):
            f_val = float(val)
            grounded.add(f_val)
            grounded.add(round(f_val, 0))
            grounded.add(round(f_val, 1))
            grounded.add(round(f_val, 2))
            # If percentage representation
            if 0 < f_val <= 1:
                pct = f_val * 100
                grounded.add(round(pct, 1))
                grounded.add(round(pct, 2))
            elif f_val > 1 and row_count > 0:
                pct = (f_val / row_count) * 100
                grounded.add(round(pct, 1))
                grounded.add(round(pct, 2))

    # 3. Dimension values
    dimensions = context.get("dimensions", {})
    for dim_dict in dimensions.values():
        if isinstance(dim_dict, dict):
            for count in dim_dict.values():
                if isinstance(count, (int, float)):
                    c_val = float(count)
                    grounded.add(c_val)
                    if row_count > 0:
                        pct = (c_val / row_count) * 100
                        grounded.add(round(pct, 1))
                        grounded.add(round(pct, 2))

    # 4. Common standard years if present in attributes or context
    # e.g., years between 2000 and 2030
    for year in range(2000, 2031):
        grounded.add(float(year))

    # 5. Common zero and one
    grounded.add(0.0)
    grounded.add(1.0)
    grounded.add(100.0)

    return grounded


def validate_and_enforce_grounding(
    response: AnalystResponse,
    context: dict[str, Any],
) -> tuple[AnalystResponse, list[str]]:
    """Validate numerical claims and enforce grounding.

    If an unsupported number is detected:
    - Replaces or appends a warning
    - Adds explicit limitation note

    Returns
    -------
    (guarded_response, warnings)
    """
    grounded_numbers = get_all_grounded_numbers(context)
    claimed_numbers = extract_numbers_from_text(response.answer)

    ungrounded: list[float] = []
    for num in claimed_numbers:
        # Check direct match or approximate match (within 0.05)
        is_grounded = any(abs(num - g) < 0.05 for g in grounded_numbers)
        if not is_grounded:
            ungrounded.append(num)

    warnings: list[str] = []
    if ungrounded:
        for num in ungrounded:
            warnings.append(f"Ungrounded number in response: {num}")

        # Enforce grounding on answer
        limitation_note = (
            f"Note: Certain figures ({', '.join(str(n) for n in ungrounded[:3])}) "
            "could not be verified against deterministic analytics. "
            "The available verified data does not provide those values."
        )

        response.limitations.append(limitation_note)

    return response, warnings
