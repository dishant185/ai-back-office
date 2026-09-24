"""Result & Evidence Validator for Novera AI Business Analyst.

Compares EXPECTED QUERY PLAN against ACTUAL EXECUTION RESULT.
Validates:
  - Intent alignment
  - Dimension alignment
  - Measure alignment
  - Aggregation alignment
  - Filter and entity preservation
  - Mathematical integrity

Rejects results and revokes VERIFIED status when a mismatch occurs
(e.g. expected product revenue, but received category record count).
"""
from __future__ import annotations

import logging
from typing import Any
from app.analytics.models import QueryPlan, VerifiedResult

logger = logging.getLogger(__name__)


class ResultValidator:
    """Enforces strict query-evidence-result verification."""

    @classmethod
    def validate(cls, plan: QueryPlan, verified: VerifiedResult) -> bool:
        """Validate that verified execution strictly matches the requested query plan.

        Returns True if verified, False if rejected.
        """
        # Pass through expected unavailable or clarification states
        if verified.verification_status in ("unavailable", "clarification") or verified.is_unavailable:
            return True

        if plan.status in ("UNAVAILABLE", "CLARIFICATION", "REJECTED"):
            return True

        res = verified.result or {}

        # 1. Intent Validation
        plan_intent = plan.intent.upper()
        res_intent = verified.intent.upper()

        intent_equivalencies = {
            "COUNT": {"COUNT", "TOTAL"},
            "COUNT_UNIQUE": {"COUNT_UNIQUE", "DISTINCT_COUNT"},
            "SUM": {"SUM", "TOTAL", "FILTERED_METRIC"},
            "AVERAGE": {"AVERAGE", "AVG"},
            "MEDIAN": {"MEDIAN"},
            "MINIMUM": {"MINIMUM", "MIN"},
            "MAXIMUM": {"MAXIMUM", "MAX"},
            "TOP_ENTITY": {"TOP_ENTITY", "RANK", "TOP_N"},
            "BOTTOM_ENTITY": {"BOTTOM_ENTITY", "BOTTOM_N"},
            "COMPARISON": {"COMPARISON", "DIFFERENCE"},
            "SHARE": {"SHARE", "PERCENTAGE_SHARE", "CONTRIBUTION"},
            "ANOMALY": {"ANOMALY", "OUTLIER"},
            "MISSING_DATA_AUDIT": {"MISSING_DATA_AUDIT", "MISSING_VALUE_CHECK", "QUALITY"},
            "DERIVED_METRIC": {"DERIVED_METRIC"},
            "LIST_UNIQUE": {"LIST_UNIQUE"},
            "TREND": {"TREND", "GROWTH"},
        }

        allowed_intents = intent_equivalencies.get(plan_intent, {plan_intent})
        if res_intent not in allowed_intents and plan_intent != "SEMANTIC_ANALYTICS":
            logger.warning(
                "ResultValidator REJECT: Intent mismatch. Expected %s, got %s",
                plan_intent,
                res_intent,
            )
            verified.verification_status = "rejected"
            verified.error_message = f"Query intent mismatch: expected {plan_intent}, execution produced {res_intent}."
            return False

        # 2. Dimension Validation
        # If query expected a specific dimension (e.g. Product_ID), execution must not return another dimension (e.g. Category)
        if plan.dimension:
            plan_dim = plan.dimension.lower().replace(" ", "_")
            res_dim = str(res.get("dimension") or (verified.query_plan or {}).get("dimension") or "").lower().replace(" ", "_")
            if res_dim and res_dim != plan_dim and plan_dim not in res_dim and res_dim not in plan_dim:
                # Disallow dimension substitution (e.g. category for product)
                if any(k in plan_dim for k in ["product", "item", "sku"]) and "category" in res_dim:
                    logger.warning("ResultValidator REJECT: Dimension substituted. Expected %s, got %s", plan.dimension, res_dim)
                    verified.verification_status = "rejected"
                    verified.error_message = f"Dimension mismatch: requested '{plan.dimension}' but got '{res_dim}'."
                    return False

        # 3. Measure Validation
        # If query asked for revenue, execution must not substitute count or quantity
        if plan.measure:
            plan_m = plan.measure.lower().replace(" ", "_")
            res_m = str(res.get("measure") or (verified.query_plan or {}).get("measure") or "").lower().replace(" ", "_")
            if res_m and res_m != plan_m and plan_m not in res_m and res_m not in plan_m:
                # Explicitly disallow revenue <-> quantity or revenue <-> count substitution
                if any(r in plan_m for r in ["revenue", "sales", "amount"]) and any(q in res_m for q in ["quantity", "count", "units"]):
                    logger.warning("ResultValidator REJECT: Measure substituted. Expected %s, got %s", plan.measure, res_m)
                    verified.verification_status = "rejected"
                    verified.error_message = f"Measure mismatch: requested '{plan.measure}' but got '{res_m}'."
                    return False
                if any(q in plan_m for q in ["quantity", "units"]) and any(r in res_m for r in ["revenue", "sales", "amount"]):
                    logger.warning("ResultValidator REJECT: Measure substituted. Expected %s, got %s", plan.measure, res_m)
                    verified.verification_status = "rejected"
                    verified.error_message = f"Measure mismatch: requested '{plan.measure}' but got '{res_m}'."
                    return False

        # 4. Filter Validation
        if plan.filter_val:
            val_str = str(plan.filter_val).lower()
            res_entity = str(res.get("entity") or res.get("filter_value") or "").lower()
            if res_entity and val_str not in res_entity and res_entity not in val_str:
                logger.warning("ResultValidator REJECT: Entity filter mismatch. Expected %s, got %s", plan.filter_val, res_entity)
                verified.verification_status = "rejected"
                verified.error_message = f"Filter entity mismatch: expected '{plan.filter_val}', got '{res_entity}'."
                return False

        # 5. Entity Alignment in Comparisons
        if plan_intent in ("COMPARISON", "DIFFERENCE") and plan.entities:
            res_entities = [str(e).lower() for e in (res.get("entities") or [])]
            expected_entities = [str(e).lower() for e in plan.entities]
            if res_entities and not any(exp in res_entities for exp in expected_entities):
                logger.warning("ResultValidator REJECT: Comparison entities mismatch. Expected %s, got %s", plan.entities, res_entities)
                verified.verification_status = "rejected"
                verified.error_message = f"Comparison entities mismatch: expected {plan.entities}, got {res_entities}."
                return False

        # 6. Intent-specific mathematical / result checks
        if plan_intent in ("COUNT", "COUNT_UNIQUE"):
            val = res.get("value")
            if val is None or not isinstance(val, (int, float)) or val < 0:
                logger.warning("ResultValidator REJECT: Invalid count value: %s", val)
                verified.verification_status = "rejected"
                return False

        if plan_intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            # Check for entity presence
            if not res.get("entity") and not res.get("ranking"):
                logger.warning("ResultValidator REJECT: Missing entity in ranking result: %s", res)
                verified.verification_status = "rejected"
                return False

        if plan_intent in ("SUM", "AVERAGE", "AVG", "MINIMUM", "MAXIMUM", "MEDIAN"):
            val = res.get("value")
            if val is None or not isinstance(val, (int, float)):
                logger.warning("ResultValidator REJECT: Missing numeric value in aggregation result: %s", res)
                verified.verification_status = "rejected"
                return False

        return True
