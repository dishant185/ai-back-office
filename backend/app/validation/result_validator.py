"""Result Validator.

Ensures that the output of the deterministic analytics engine conforms to expectations
and maintains mathematical consistency.
"""
from __future__ import annotations

import logging
from typing import Any
from app.analytics.models import QueryPlan, VerifiedResult

logger = logging.getLogger(__name__)


class ResultValidator:
    """Validates VerifiedResult before returning to response layer."""

    @classmethod
    def validate(cls, plan: QueryPlan, verified: VerifiedResult) -> bool:
        if verified.verification_status in ("unavailable", "clarification"):
            return True

        res = verified.result

        # Intent-specific verification
        if plan.intent in ("COUNT", "COUNT_UNIQUE"):
            val = res.get("value")
            if val is None or not isinstance(val, (int, float)) or val < 0:
                logger.error("Invalid count value in verified result: %s", val)
                return False

        if plan.intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            if not res.get("entity"):
                logger.error("Missing entity in top/bottom result: %s", res)
                return False

        if plan.intent in ("SUM", "AVERAGE", "AVG", "MINIMUM", "MAXIMUM", "MEDIAN"):
            val = res.get("value")
            if val is None or not isinstance(val, (int, float)):
                logger.error("Missing numeric value in aggregation result: %s", res)
                return False

        return True
