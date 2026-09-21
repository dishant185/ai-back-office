"""Risk Claim Validator for Production AI Executive Summary Engine V2.

Ensures that numerical values alone are not arbitrarily transformed into risk/danger claims
without authoritative anomaly or risk evidence.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class RiskValidationResult(BaseModel):
    is_valid: bool = True
    violations: list[str] = Field(default_factory=list)


class RiskClaimValidator:
    """Validates that risk, warning, and danger claims are grounded in verified anomaly evidence."""

    UNSUPPORTED_RISK_PATTERNS = [
        re.compile(r"\b(?:talent\s+loss\s+risk|talent\s+drain|flight\s+risk)\b", re.IGNORECASE),
        re.compile(r"\b(?:severe\s+risk|critical\s+danger|operational\s+crisis)\b", re.IGNORECASE),
        re.compile(r"\b(?:margin\s+compression\s+risk|catastrophic\s+risk)\b", re.IGNORECASE),
        re.compile(r"\bhigh\s+talent\s+loss\s+risk\b", re.IGNORECASE),
    ]

    @classmethod
    def validate_risks(
        cls,
        summary_text: str,
        evidence: dict[str, Any],
    ) -> RiskValidationResult:
        result = RiskValidationResult()
        anomalies = evidence.get("anomalies", evidence.get("verified_anomalies", []))
        has_high_severity_anomaly = any(a.get("severity") in ("high", "critical") for a in anomalies)

        for pat in cls.UNSUPPORTED_RISK_PATTERNS:
            match = pat.search(summary_text)
            if match:
                # If there is no high/critical severity anomaly supporting this claim, fail
                if not has_high_severity_anomaly:
                    result.is_valid = False
                    result.violations.append(
                        f"Unsupported Risk Claim: '{match.group(0)}' asserted without verified anomaly evidence in the current report."
                    )

        return result

    @classmethod
    def validate_text(cls, text: str, has_risk_model: bool = False) -> RiskValidationResult:
        ev = {"anomalies": [{"severity": "high"}]} if has_risk_model else {}
        return cls.validate_risks(text, ev)

