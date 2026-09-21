"""Clarification message builder."""
from __future__ import annotations

from typing import Any


class ClarificationBuilder:
    """Constructs structured clarification requests when inquiries are ambiguous."""

    @classmethod
    def dataset_ambiguity(cls, matching_filenames: list[str]) -> dict[str, Any]:
        options_text = " or ".join(matching_filenames)
        return {
            "status": "clarification",
            "question": f"Which dataset would you like me to use: {options_text}?",
            "options": matching_filenames,
        }

    @classmethod
    def metric_ambiguity(cls, dimension: str, candidates: list[str]) -> dict[str, Any]:
        return {
            "status": "clarification",
            "question": f"Which metric would you like to analyze for {dimension}: {' or '.join(candidates)}?",
            "options": candidates,
        }
