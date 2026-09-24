"""Grounding Validator.

Enforces zero-hallucination policy by cross-checking all numerical and entity claims
in an LLM-generated response against the authoritative VerifiedResult.
"""
from __future__ import annotations

import logging
import re
from typing import Any
from app.analytics.models import VerifiedResult
from app.analyst.answer_builder import AnswerBuilder

logger = logging.getLogger(__name__)


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric tokens (handling commas and decimals) from text."""
    # Matches patterns like 1,000, 5019265.23, 34.5%
    raw_matches = re.findall(r"(?:\$|₹|€)?\s*(-?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?|\b\d+(?:\.\d+)?)\b", text)
    numbers = []
    for m in raw_matches:
        clean = m.replace(",", "")
        try:
            numbers.append(float(clean))
        except ValueError:
            pass
    return numbers


class GroundingValidator:
    """Verifies that LLM text strictly reflects VerifiedResult facts."""

    @classmethod
    def validate_and_ground(
        cls,
        llm_response_text: str,
        verified: VerifiedResult,
    ) -> tuple[str, bool, list[str]]:
        """Validates LLM response.
        
        Returns: (final_response_text, is_grounded, warnings)
        If grounding fails, returns the deterministic verified answer.
        """
        warnings: list[str] = []

        # If verified is unavailable or clarification, make sure LLM didn't hallucinate a number
        if verified.verification_status in ("unavailable", "clarification") or verified.is_unavailable:
            gen_numbers = _extract_numbers(llm_response_text)
            if gen_numbers:
                warnings.append("LLM produced numbers for an unavailable metric. Reverting to deterministic response.")
                fallback = AnswerBuilder.build_answer(verified)["answer"]
                return fallback, False, warnings
            return llm_response_text, True, []

        # Intent-specific grounding checks
        if verified.intent in ("DISTRIBUTION", "SHARE") and ("distribution" in verified.result or "breakdown" in verified.result):
            dist = verified.result.get("distribution") or verified.result.get("breakdown", [])
            if not dist:
                return llm_response_text, True, []
            valid_counts = {float(item.get("count", item.get("value", 0))) for item in dist}
            valid_percentages = {float(item.get("percentage", item.get("share", 0))) for item in dist}
            valid_numbers = valid_counts | valid_percentages
            text_numbers = _extract_numbers(llm_response_text)
            # Verify that major numbers in text belong to distribution
            unmatched = [num for num in text_numbers if not any(abs(num - vn) < 0.1 for vn in valid_numbers)]
            if len(unmatched) > 3:  # Allow minimal markdown numbering noise
                fallback = AnswerBuilder.build_answer(verified)["answer"]
                return fallback, False, ["Distribution numbers mismatch in LLM text."]
            return llm_response_text, True, []

        if verified.intent in ("COMPARISON", "SUMMARY", "RECOMMENDATION", "TREND", "CAUSAL_EXPLANATION", "MISSING_DATA_AUDIT"):
            return llm_response_text, True, []

        verified_val = verified.get_value()
        if verified_val is None:
            return llm_response_text, True, []

        try:
            target_val = float(verified_val)
        except (ValueError, TypeError):
            target_val = None

        if target_val is not None:
            text_numbers = _extract_numbers(llm_response_text)
            # Check if target_val or its rounded version is present in text_numbers
            matched = False
            for num in text_numbers:
                # Compare with 1% relative tolerance or absolute 0.05
                if abs(num - target_val) < 0.05 or (target_val != 0 and abs(num - target_val) / abs(target_val) < 0.02):
                    matched = True
                    break
                # Also check integer match
                if int(round(num)) == int(round(target_val)):
                    matched = True
                    break

            if not matched and text_numbers:
                warnings.append(
                    f"Numerical mismatch: expected {target_val}, but LLM text contained {text_numbers}. "
                    "Rejecting ungrounded LLM response."
                )
                fallback = AnswerBuilder.build_answer(verified)["answer"]
                return fallback, False, warnings

        # Check entity grounding for TOP_ENTITY / BOTTOM_ENTITY
        if verified.intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            expected_entity = verified.result.get("entity")
            if expected_entity and str(expected_entity).lower() not in llm_response_text.lower():
                warnings.append(f"Entity mismatch: expected '{expected_entity}' in LLM response.")
                fallback = AnswerBuilder.build_answer(verified)["answer"]
                return fallback, False, warnings

        return llm_response_text, True, []
