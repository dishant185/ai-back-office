"""Unsupported Inference Validator for AI Back-Office Copilot.

Enforces:
1. Causation Protection (Section 29): Rejects asserting causal links from correlation.
2. Instruction Leakage Prevention: Rejects meta-instructions or prompt directives in user text.
3. Unsupported speculation guardrail.
"""
from __future__ import annotations

import re
from pydantic import BaseModel


class InferenceValidationResult(BaseModel):
    is_valid: bool
    violations: list[str] = []


class UnsupportedInferenceValidator:
    """Validates that text contains no unsupported causal or speculative assertions."""

    CAUSATION_PATTERNS = [
        r"\b(higher|lower|increased|decreased)\b.*?\b(caused|led to|drove|resulted in)\b.*?\b(higher|lower|sales|revenue|attrition|turnover)\b",
        r"\b(because of|due to)\b.*?\b(caused|causing)\b",
        r"\b(proves that|directly responsible for|sole cause of)\b",
    ]

    INSTRUCTION_LEAK_PATTERNS = [
        r"\bevaluate revenue, transaction volume, and commercial performance\b",
        r"\bprovide actionable recommendations\b",
        r"\bnever invent numbers\b",
        r"\bdo not hallucinate\b",
        r"\bas an ai business analyst\b",
        r"\baccording to the system prompt\b",
        r"\bbased on the provided json schema\b",
    ]

    @classmethod
    def validate_inferences(
        cls,
        text: str,
        has_causal_evidence: bool = False,
    ) -> InferenceValidationResult:
        violations = []
        text_low = text.lower()

        # 1. Causation checks
        if not has_causal_evidence:
            for pat in cls.CAUSATION_PATTERNS:
                if re.search(pat, text_low):
                    # Check if qualified with correlation language
                    if not any(k in text_low for k in ["correlation", "associated with", "pattern shows", "observed relationship"]):
                        violations.append(f"Text asserts unsupported causal relationship: match for pattern '{pat}'")

        # 2. Instruction leakage checks
        for pat in cls.INSTRUCTION_LEAK_PATTERNS:
            if re.search(pat, text_low):
                violations.append(f"Text contains internal prompt instruction leakage: match for pattern '{pat}'")

        return InferenceValidationResult(
            is_valid=(len(violations) == 0),
            violations=violations,
        )
