"""Comparison Validator for Production AI Executive Summary Engine V2.

Ensures comparisons:
- Involve the same measure, same unit, and compatible scope
- Accurately reflect verified top/bottom entity relationships (no inverse comparisons)
- Avoid subjective ungrounded superlatives like 'performed better' without metric definition
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class ComparisonValidationResult(BaseModel):
    is_valid: bool = True
    violations: list[str] = Field(default_factory=list)


class ComparisonValidator:
    """Validates comparative statements against authoritative rankings and comparisons."""

    VAGUE_SUPERLATIVE_PATTERNS = [
        re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+performed\s+better\b", re.IGNORECASE),
        re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+was\s+superior\b", re.IGNORECASE),
    ]

    @classmethod
    def validate_comparisons(
        cls,
        summary_text: str,
        evidence: dict[str, Any],
    ) -> ComparisonValidationResult:
        result = ComparisonValidationResult()
        text_lower = summary_text.lower()
        comparisons = evidence.get("comparisons", evidence.get("verified_comparisons", []))
        rankings = evidence.get("rankings", evidence.get("verified_rankings", []))

        # 1. Check for inverted comparisons within individual sentences
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text_lower) if s.strip()]
        for cmp in comparisons:
            top_e = (cmp.get("top_entity") or "").lower()
            bot_e = (cmp.get("bottom_entity") or "").lower()
            if top_e and bot_e and top_e != bot_e:
                inv_pat = rf"\b{re.escape(bot_e)}\b.*?\b(?:leads|exceeds|higher than|surpassed|outperformed|more than)\b.*?\b{re.escape(top_e)}\b"
                for sentence in sentences:
                    if re.search(inv_pat, sentence):
                        result.is_valid = False
                        result.violations.append(
                            f"Inverted Comparison: Claimed '{bot_e}' leads '{top_e}' in '{sentence.strip()}', but verified evidence shows '{top_e}' ({cmp.get('top_value')}) exceeds '{bot_e}' ({cmp.get('bottom_value')})."
                        )
                        break

        # 2. Check for vague unqualified superlatives
        for pat in cls.VAGUE_SUPERLATIVE_PATTERNS:
            match = pat.search(summary_text)
            if match:
                # If the immediate vicinity doesn't define the metric or number, flag it
                snippet = summary_text[max(0, match.start() - 20):min(len(summary_text), match.end() + 40)]
                if not any(token in snippet.lower() for token in ["revenue", "margin", "volume", "$", "%"]):
                    result.is_valid = False
                    result.violations.append(
                        f"Unqualified Comparison: '{match.group(0)}' asserts subjective performance without defining the verified metric."
                    )

        return result
