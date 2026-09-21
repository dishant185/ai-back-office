"""Tests for Numerical Grounding Validator."""
from __future__ import annotations

import pytest
from app.ai.grounding_validator import get_all_grounded_numbers, validate_and_enforce_grounding
from app.ai.validators import AnalystResponse


def test_get_all_grounded_numbers():
    ctx = {
        "row_count": 4653,
        "column_count": 9,
        "metrics": {
            "employee_count": 4653,
            "average_age": 29.39,
            "attrition_rate": 34.39,
        },
        "dimensions": {
            "city": {"Bangalore": 2228, "Pune": 1268}
        },
    }

    nums = get_all_grounded_numbers(ctx)
    assert 4653.0 in nums
    assert 9.0 in nums
    assert 29.39 in nums
    assert 2228.0 in nums
    assert 1268.0 in nums


def test_validate_and_enforce_grounding_valid():
    ctx = {
        "row_count": 4653,
        "metrics": {"employee_count": 4653, "average_age": 29.39},
        "dimensions": {},
    }
    resp = AnalystResponse(
        answer="The dataset includes 4653 employees with an average age of 29.39.",
    )
    guarded, warnings = validate_and_enforce_grounding(resp, ctx)
    assert len(warnings) == 0
    assert len(guarded.limitations) == 0


def test_validate_and_enforce_grounding_hallucinated():
    ctx = {
        "row_count": 4653,
        "metrics": {"employee_count": 4653, "average_age": 29.39},
        "dimensions": {},
    }
    resp = AnalystResponse(
        answer="We found 4653 employees and exactly 98765 applicants last month.",
    )
    guarded, warnings = validate_and_enforce_grounding(resp, ctx)
    assert len(warnings) > 0
    assert any("98765" in w for w in warnings)
    assert any("98765" in lim for lim in guarded.limitations)
