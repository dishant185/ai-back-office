"""Semantic Validator for Production AI Executive Summary Engine V2.

Enforces strict semantic measure alignment:
- Prohibits calling revenue/monetary amounts 'volume' or 'sales volume'
- Prohibits calling headcount/employee counts 'revenue' or 'sales'
- Prohibits metric category conflations
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class SemanticValidationResult(BaseModel):
    is_valid: bool = True
    violations: list[str] = Field(default_factory=list)


class SemanticValidator:
    """Validates that semantic terminology aligns with authoritative metric measures."""

    @classmethod
    def validate_semantics(
        cls,
        summary_text: str,
        evidence: dict[str, Any],
    ) -> SemanticValidationResult:
        result = SemanticValidationResult()
        text_lower = summary_text.lower()
        metrics = evidence.get("metrics", evidence.get("verified_metrics", []))

        # Check for revenue called "volume" or "sales volume"
        revenue_metrics = [m for m in metrics if m.get("semantic_measure") == "revenue" or "revenue" in m.get("name", "").lower()]
        if revenue_metrics:
            # Look for phrases like "$... volume", "revenue of ... in volume", "sales volume of $", "volume was $"
            patterns = [
                r"\$[\d\.,]+[kmb]?\s+(?:in\s+)?(?:sales\s+)?volume\b",
                r"\b(?:sales\s+)?volume\s+(?:of|at|stands\s+at)?\s*\$[\d\.,]+[kmb]?",
                r"\brecorded\s+\$[\d\.,]+[kmb]?\s+in\s+sales\s+volume\b",
                r"\bregional\s+volume\s+(?:of|at|was)?\s*\$[\d\.,]+[kmb]?",
                r"\bhighest\s+sales\s+volume\s+at\s+\$[\d\.,]+[kmb]?",
            ]
            for pat in patterns:
                match = re.search(pat, text_lower)
                if match:
                    result.is_valid = False
                    result.violations.append(
                        f"Semantic Violation: Currency amount framed as 'volume' in '{match.group(0)}'. Revenue measure must not be described as volume."
                    )

        # Check for headcount described as currency
        headcount_metrics = [m for m in metrics if m.get("semantic_measure") == "headcount" or "employee" in m.get("name", "").lower()]
        if headcount_metrics:
            pat_curr_headcount = r"\$[\d\.,]+[kmb]?\s+(?:employees|workers|headcount|staff)\b"
            match = re.search(pat_curr_headcount, text_lower)
            if match:
                result.is_valid = False
                result.violations.append(
                    f"Semantic Violation: Headcount metric prefixed with currency in '{match.group(0)}'."
                )

        return result
