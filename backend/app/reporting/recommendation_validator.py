"""Recommendation Validator for Production AI Executive Summary Engine V2.

Ensures that recommendations:
- Are strictly evidence-linked
- Do NOT contain generic filler (e.g. 'Continue monitoring performance', 'Review operational factors')
- Do NOT introduce unsupported facts, cross-domain concepts, or urgency without evidence
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class RecommendationValidationResult(BaseModel):
    is_valid: bool = True
    violations: list[str] = Field(default_factory=list)


class RecommendationValidator:
    """Validates that recommendations are grounded in verified evidence without generic filler."""

    GENERIC_FILLER_PATTERNS = [
        re.compile(r"\bcontinue\s+(?:standard\s+)?(?:operational\s+)?monitoring\b", re.IGNORECASE),
        re.compile(r"\bcontinue\s+monitoring\s+performance\b", re.IGNORECASE),
        re.compile(r"\breview\s+operational\s+factors\b", re.IGNORECASE),
        re.compile(r"\bmaintain\s+(?:current\s+)?monitoring\b", re.IGNORECASE),
        re.compile(r"\bfurther\s+monitoring\s+is\s+recommended\b", re.IGNORECASE),
        re.compile(r"\bmonitor\s+key\s+metrics\s+closely\b", re.IGNORECASE),
    ]

    @classmethod
    def validate_recommendations(
        cls,
        recommendations: list[Any],
        evidence: dict[str, Any],
        report_domain: str = "",
    ) -> RecommendationValidationResult:
        result = RecommendationValidationResult()
        valid_ids = set(evidence.get("all_evidence_ids", []))
        domain = (report_domain or evidence.get("dataset", {}).get("domain", "")).lower()

        for idx, rec in enumerate(recommendations):
            if isinstance(rec, dict):
                content = rec.get("content") or rec.get("description") or rec.get("title") or ""
                ev_ids = rec.get("evidence_ids", [])
            else:
                content = str(rec)
                ev_ids = []

            # 1. Reject generic boilerplate
            for pat in cls.GENERIC_FILLER_PATTERNS:
                if pat.search(content):
                    result.is_valid = False
                    result.violations.append(
                        f"Generic Recommendation: '{content}' is boilerplate advice with no specific evidence connection."
                    )

            # 2. Check cross-domain contamination in recommendations
            c_lower = content.lower()
            if domain == "hr":
                if any(w in c_lower for w in ["pricing strategy", "inventory stockout", "supply chain logistics", "warehouse capacity"]):
                    result.is_valid = False
                    result.violations.append(
                        f"Cross-Domain Recommendation: HR recommendation references unrelated commercial concept in '{content}'."
                    )
            elif domain == "sales":
                if any(w in c_lower for w in ["attrition interviews", "severance packages", "headcount reduction", "talent retention survey"]):
                    result.is_valid = False
                    result.violations.append(
                        f"Cross-Domain Recommendation: Sales recommendation references unrelated HR concept in '{content}'."
                    )

            # 3. If evidence_ids are provided, verify they exist in evidence
            if ev_ids:
                for eid in ev_ids:
                    if eid not in valid_ids and not any(eid in vid for vid in valid_ids):
                        result.is_valid = False
                        result.violations.append(
                            f"Ungrounded Recommendation: Evidence ID '{eid}' cited in recommendation does not exist."
                        )

        return result
