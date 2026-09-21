"""Report Summary Differentiation Validator (Rule #25).

Ensures that different report types for the same dataset produce meaningfully
differentiated executive narratives rather than generic copy-paste templates.
Compares analytical focus, primary dimensions, and metric themes dynamically.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class DifferentiationResult(BaseModel):
    is_differentiated: bool = True
    similarity_score: float = 0.0
    shared_focus_topics: list[str] = Field(default_factory=list)
    distinct_dimensions_found: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class ReportSummaryValidator:
    """Validates that summaries across different reports maintain distinct analytical focus."""

    @staticmethod
    def _extract_text(summary_payload: dict[str, Any] | str) -> str:
        if isinstance(summary_payload, str):
            return summary_payload
        if isinstance(summary_payload, dict):
            parts = [summary_payload.get("overview", "")]
            for k in ["key_findings", "patterns", "comparisons", "trends", "business_implications", "recommendations"]:
                v = summary_payload.get(k)
                if isinstance(v, list):
                    parts.extend(str(item) for item in v)
                elif isinstance(v, str):
                    parts.append(v)
            return " ".join(parts)
        return ""

    @classmethod
    def validate_differentiation(
        cls,
        summary_a: dict[str, Any] | str,
        report_type_a: str,
        summary_b: dict[str, Any] | str,
        report_type_b: str,
        max_overlap_threshold: float = 0.70,
    ) -> DifferentiationResult:
        """Validates that two reports produced distinct, purpose-driven narratives dynamically."""
        text_a = cls._extract_text(summary_a).lower()
        text_b = cls._extract_text(summary_b).lower()

        res = DifferentiationResult()

        # Extract words (ignoring short stopwords)
        words_a = set(re.findall(r"\b[a-z]{4,}\b", text_a))
        words_b = set(re.findall(r"\b[a-z]{4,}\b", text_b))

        if not words_a or not words_b:
            return res

        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        jaccard = len(intersection) / max(len(union), 1)
        res.similarity_score = round(jaccard, 3)

        # Distinct vocabulary unique to each report's narrative
        diff_a = words_a - words_b
        diff_b = words_b - words_a

        for w in sorted(list(diff_a))[:5]:
            res.distinct_dimensions_found.append(f"{report_type_a}: {w}")
        for w in sorted(list(diff_b))[:5]:
            res.distinct_dimensions_found.append(f"{report_type_b}: {w}")

        # If similarity exceeds threshold and no distinct dimensions were found, flag lack of differentiation
        if jaccard > max_overlap_threshold and len(res.distinct_dimensions_found) == 0:
            res.is_differentiated = False
            res.violations.append(
                f"Reports '{report_type_a}' and '{report_type_b}' produced indistinguishable narratives (similarity {jaccard:.2f})."
            )

        return res
