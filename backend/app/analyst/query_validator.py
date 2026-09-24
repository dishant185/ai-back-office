"""Query Plan Validator.

Pre-execution quality controller. Validates the plan against the active dataset schema,
checks data types, rejects arbitrary code or SQL injection, and flags unsupported operations.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.analytics.models import QueryPlan
from app.data.semantic.schema_builder import SemanticSchema

logger = logging.getLogger(__name__)

# Dangerous patterns to prevent arbitrary code or injection attempts
DANGEROUS_PATTERNS = [
    r"__import__",
    r"exec\(",
    r"eval\(",
    r"os\.system",
    r"subprocess",
    r";\s*DROP\b",
    r";\s*DELETE\b",
    r";\s*INSERT\b",
    r";\s*UPDATE\b",
    r"<script",
]


class QueryValidator:
    """Validates analytical query plans before execution."""

    @classmethod
    def validate(cls, plan: QueryPlan, schema: SemanticSchema) -> QueryPlan:
        # Check for dangerous patterns in all string attributes
        plan_str = f"{plan.dimension or ''} {plan.measure or ''} {plan.filter_col or ''} {plan.filter_val or ''}"
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, plan_str, re.IGNORECASE):
                logger.warning("Dangerous pattern rejected in QueryPlan: %s", pat)
                plan.status = "REJECTED"
                plan.unavailable_reason = "Query rejected due to safety policy violations."
                return plan

        # If already marked unavailable or clarification, pass through safely
        if plan.status in ("UNAVAILABLE", "CLARIFICATION", "REJECTED"):
            return plan

        orig_col_names = [c.original_name.lower() for c in schema.columns]
        semantic_col_names = [c.semantic_name.lower() for c in schema.columns]
        valid_cols = set(orig_col_names + semantic_col_names)

        # Validate dimension if present
        if plan.dimension:
            if plan.dimension.lower() not in valid_cols:
                # Try relaxed partial match
                if not any(plan.dimension.lower() in c or c in plan.dimension.lower() for c in valid_cols):
                    plan.status = "UNAVAILABLE"
                    plan.unavailable_reason = f"Dimension '{plan.dimension}' was not found in dataset schema."
                    return plan

        # Validate measure if present
        if plan.measure and plan.measure not in ("estimated_profit", "attrition_rate"):
            if plan.measure.lower() not in valid_cols:
                if not any(plan.measure.lower() in c or c in plan.measure.lower() for c in valid_cols):
                    plan.status = "UNAVAILABLE"
                    plan.unavailable_reason = f"Measure '{plan.measure}' was not found in dataset schema."
                    return plan

            # Ensure identifier fields are never used as aggregated business measures
            if plan.aggregation and plan.aggregation.upper() not in ("COUNT", "COUNT_DISTINCT"):
                col_obj = schema.get_column(plan.measure)
                if col_obj and col_obj.role == "identifier":
                    plan.status = "REJECTED"
                    plan.unavailable_reason = f"Identifier '{plan.measure}' cannot be aggregated using {plan.aggregation}."
                    return plan

        # Validate aggregation function
        if plan.aggregation:
            valid_aggs = {"SUM", "AVG", "AVERAGE", "MIN", "MINIMUM", "MAX", "MAXIMUM", "MEDIAN", "COUNT"}
            if plan.aggregation.upper() not in valid_aggs:
                plan.aggregation = "SUM"

        # Validate limits
        if plan.limit <= 0 or plan.limit > 1000:
            plan.limit = 10

        return plan
