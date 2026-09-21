"""Trend Validator for Production AI Executive Summary Engine V2.

Ensures that claims of temporal growth, decline, trajectory, or seasonality are backed by
verified deterministic time-series analytics with sufficient data points.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class TrendValidationResult(BaseModel):
    is_valid: bool = True
    violations: list[str] = Field(default_factory=list)


class TrendValidator:
    """Validates that trend assertions are supported by deterministic chronological calculations."""

    TREND_ASSERTION_PATTERNS = [
        re.compile(r"\b(?:revenue|profit|sales|headcount|attrition)\s+(?:increased|decreased|grew|declined|surged|dropped)\s+by\s+(\d+(?:\.\d+)?%?)", re.IGNORECASE),
        re.compile(r"\b(?:upward|downward|historical)\s+trend\b", re.IGNORECASE),
        re.compile(r"\btemporal\s+trajectory\b", re.IGNORECASE),
        re.compile(r"\baccelerat(?:ed|ing|ion)\b", re.IGNORECASE),
        re.compile(r"\bdecelerat(?:ed|ing|ion)\b", re.IGNORECASE),
        re.compile(r"\bseasonality\b", re.IGNORECASE),
        re.compile(r"\brevenue\s+over\s+time\b", re.IGNORECASE),
    ]

    @classmethod
    def validate_trends(
        cls,
        summary_text: str,
        evidence: dict[str, Any],
    ) -> TrendValidationResult:
        result = TrendValidationResult()
        trends = evidence.get("trends", evidence.get("verified_trends", []))
        has_meaningful_trend = any(t.get("data_points", 0) >= 2 or t.get("is_meaningful", False) for t in trends)

        for pat in cls.TREND_ASSERTION_PATTERNS:
            for match in pat.finditer(summary_text):
                claim = match.group(0)
                if not has_meaningful_trend:
                    result.is_valid = False
                    result.violations.append(
                        f"Unsupported Trend: Claim '{claim}' asserted without verified temporal analytics in current report."
                    )

        return result
