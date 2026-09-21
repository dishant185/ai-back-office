"""Pre/post-processing guardrails.

Sanitizes context data and prevents prompt injection from
dataset cell values.
"""
from __future__ import annotations

import re
from typing import Any


# Patterns that look like prompt injection attempts
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"execute\s+(this\s+)?command", re.IGNORECASE),
    re.compile(r"run\s+(this\s+)?(code|script|command|sql)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?your\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?(rules|instructions|constraints)", re.IGNORECASE),
    re.compile(r"system\s*override", re.IGNORECASE),
    re.compile(r"dump\s+(admin|database|credentials|passwords)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
]


def sanitize_context_value(value: Any) -> str:
    """Convert a value to string and neutralize injection attempts.

    Dataset cell values are DATA, not instructions. If a cell contains
    something that looks like an injection attempt, we escape it so
    the model treats it as a literal string.
    """
    text = str(value).strip()

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            # Wrap in quotes and prepend DATA marker
            return f'[DATA] "{text}"'

    return text


def sanitize_dimension_values(dimensions: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Sanitize all dimension label strings."""
    sanitized: dict[str, dict[str, int]] = {}
    for dim_name, values in dimensions.items():
        safe_name = sanitize_context_value(dim_name)
        safe_values = {}
        for label, count in values.items():
            safe_label = sanitize_context_value(label)
            safe_values[safe_label] = count
        sanitized[safe_name] = safe_values
    return sanitized


def sanitize_analytics_context(context: dict[str, Any]) -> dict[str, Any]:
    """Full pass over the analytics context to neutralize injections."""
    safe = dict(context)

    # Sanitize dimension labels
    if "dimensions" in safe:
        safe["dimensions"] = sanitize_dimension_values(safe["dimensions"])

    # Sanitize column names
    if "columns" in safe:
        safe["columns"] = [
            {**col, "name": sanitize_context_value(col.get("name", ""))}
            for col in safe["columns"]
        ]

    return safe


def detect_injection_in_question(question: str) -> bool:
    """Check if the user question itself contains injection attempts.

    Returns True if suspicious patterns are found. The caller can
    decide whether to warn or block.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(question):
            return True
    return False
