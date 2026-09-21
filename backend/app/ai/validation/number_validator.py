"""Number and Percentage Validator for AI Back-Office Copilot.

Validates that every numerical value, currency amount, and percentage in AI claims
strictly matches verified deterministic evidence within defined tolerance.
Enforces the Zero != Unavailable invariant.
"""
from __future__ import annotations

import math
from typing import Any
from pydantic import BaseModel


class NumberValidationResult(BaseModel):
    is_valid: bool
    unverified_numbers: list[float] = []
    unverified_percentages: list[float] = []
    errors: list[str] = []


class NumberValidator:
    """Validates numbers, percentages, and zero vs unavailable invariants."""

    @classmethod
    def validate_numbers(
        cls,
        claimed_numbers: list[float],
        verified_numbers: set[float] | list[float],
        tolerance_pct: float = 0.005,  # 0.5% tolerance
        min_abs_tolerance: float = 1.0,
    ) -> NumberValidationResult:
        v_pool = [float(x) for x in verified_numbers if x is not None]
        unverified: list[float] = []
        errors: list[str] = []

        # Benign numbers (e.g. 1, 2, 3 in bullet points, rank indices)
        benign_integers = {0, 1, 2, 3, 4, 5, 10}

        for num in claimed_numbers:
            if num in benign_integers:
                continue

            matched = False
            for v in v_pool:
                abs_diff = abs(num - v)
                allowed_tol = max(tolerance_pct * abs(v), min_abs_tolerance)
                if abs_diff <= allowed_tol:
                    matched = True
                    break

            if not matched:
                unverified.append(num)
                errors.append(f"Number {num} does not match any verified metric in evidence.")

        return NumberValidationResult(
            is_valid=(len(unverified) == 0),
            unverified_numbers=unverified,
            errors=errors,
        )

    @classmethod
    def validate_percentages(
        cls,
        claimed_pcts: list[float],
        verified_pcts: set[float] | list[float],
        abs_tolerance: float = 0.25,  # 0.25% absolute difference
    ) -> NumberValidationResult:
        v_pool = [float(x) for x in verified_pcts if x is not None]
        unverified: list[float] = []
        errors: list[str] = []

        for p in claimed_pcts:
            matched = False
            for v in v_pool:
                if abs(p - v) <= abs_tolerance:
                    matched = True
                    break
            if not matched:
                unverified.append(p)
                errors.append(f"Percentage {p}% does not match any verified rate in evidence.")

        return NumberValidationResult(
            is_valid=(len(unverified) == 0),
            unverified_percentages=unverified,
            errors=errors,
        )

    @classmethod
    def check_zero_vs_unavailable(
        cls,
        text: str,
        unavailable_metrics: list[str],
    ) -> tuple[bool, str | None]:
        """Ensures unavailable metrics are never reported as zero (Rule #26)."""
        text_low = text.lower()
        for u in unavailable_metrics:
            u_low = u.lower()
            if u_low in text_low:
                # Check if claimed as zero
                if f"{u_low} = $0" in text_low or f"{u_low} of $0" in text_low or f"{u_low} is 0" in text_low or f"{u_low}: 0" in text_low:
                    return False, f"Metric '{u}' is unavailable and cannot be claimed as zero."
        return True, None
