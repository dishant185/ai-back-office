"""Validate AI responses against supplied analytics.

Ensures every number the model outputs is grounded in the verified
context. Catches hallucinated metrics.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class AnalystResponse(BaseModel):
    """Structured AI analyst response."""
    answer: str
    sources: list[Any] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    entity: str | None = None
    dimension: str | None = None
    measure: str | None = None
    ai_status: str = "VERIFIED_ANALYTICS_ONLY"


def parse_ai_response(raw_text: str) -> AnalystResponse:
    """Parse raw LLM text into a structured AnalystResponse.

    Attempts to extract insights, recommendations, and limitations
    from the text based on common patterns.
    """
    answer = raw_text.strip()
    insights: list[str] = []
    recommendations: list[str] = []
    limitations: list[str] = []

    lines = answer.split("\n")
    current_section = "answer"

    for line in lines:
        stripped = line.strip().lower()
        if any(kw in stripped for kw in ["insight", "key finding"]):
            current_section = "insights"
            continue
        elif any(kw in stripped for kw in ["recommendation", "suggestion", "action"]):
            current_section = "recommendations"
            continue
        elif any(kw in stripped for kw in ["limitation", "not available", "missing", "caveat"]):
            current_section = "limitations"
            continue

        clean_line = line.strip().lstrip("•-*·→ ")
        if not clean_line:
            continue

        if current_section == "insights" and clean_line:
            insights.append(clean_line)
        elif current_section == "recommendations" and clean_line:
            recommendations.append(clean_line)
        elif current_section == "limitations" and clean_line:
            limitations.append(clean_line)

    return AnalystResponse(
        answer=answer,
        insights=insights,
        recommendations=recommendations,
        limitations=limitations,
    )


def extract_numbers_from_text(text: str) -> list[float]:
    """Extract all numeric values from text."""
    # Match complete formatted numbers (4,653 or 1,234.56), decimals (34.39), or integers (4653)
    # Prevents matching sub-parts like .39 from 29.39 or 653 from 4,653, while allowing sentence punctuation.
    pattern = r"(?<![\w,])(?<!\d\.)(?:(\d{1,3}(?:,\d{3})+(?:\.\d+)?)|(\d+\.\d+)%?|(\d+)(?:\s*%)?)(?!\w)(?!\.\d)"
    numbers: list[float] = []
    for match in re.finditer(pattern, text):
        raw = match.group(1) or match.group(2) or match.group(3)
        if raw:
            try:
                num_str = raw.replace(",", "")
                numbers.append(float(num_str))
            except ValueError:
                continue
    return list(set(numbers))


def validate_grounding(
    response: AnalystResponse,
    context: dict[str, Any],
    *,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    """Verify that numbers in the response are grounded in context.

    Parameters
    ----------
    response:
        The parsed AI response.
    context:
        The analytics context that was supplied to the LLM.
    strict:
        If True, reject any response with ungrounded numbers.
        If False, flag but don't reject.

    Returns
    -------
    (is_valid, list_of_warnings)
    """
    metrics = context.get("metrics", {})
    dimensions = context.get("dimensions", {})
    row_count = context.get("row_count", 0)

    # Collect all known numeric values
    known_numbers: set[float] = set()
    known_numbers.add(float(row_count))

    for value in metrics.values():
        if isinstance(value, (int, float)):
            known_numbers.add(float(value))
            # Also allow rounded versions
            known_numbers.add(round(float(value), 2))
            known_numbers.add(round(float(value), 1))
            known_numbers.add(round(float(value), 0))

    for dim_values in dimensions.values():
        for count in dim_values.values():
            if isinstance(count, (int, float)):
                known_numbers.add(float(count))

    # Also allow common derived values (percentages of row_count)
    if row_count > 0:
        for val in metrics.values():
            if isinstance(val, (int, float)):
                pct = (val / row_count) * 100
                known_numbers.add(round(pct, 2))
                known_numbers.add(round(pct, 1))
                known_numbers.add(round(pct, 0))

    # Extract numbers from the AI response
    response_numbers = extract_numbers_from_text(response.answer)

    warnings: list[str] = []
    for num in response_numbers:
        # Skip very small numbers (1, 2, 3, etc.) — likely ordinals/counting
        if num < 10 and num == int(num):
            continue

        # Check if grounded
        is_grounded = False
        for known in known_numbers:
            if abs(num - known) < 0.5:  # Allow small rounding differences
                is_grounded = True
                break

        if not is_grounded:
            warnings.append(f"Ungrounded number in response: {num}")

    is_valid = len(warnings) == 0 if strict else True
    return is_valid, warnings
