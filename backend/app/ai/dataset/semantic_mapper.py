"""Semantic Mapper for AI Back-Office Copilot.

Maps raw column names and profile heuristics to standardized business concepts.
Assigns confidence ratings and identifies columns requiring user confirmation.
NEVER makes unsafe assumptions (e.g., Sales_Amount is mapped to sales_amount,
not automatically claimed to be Net Revenue).
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from app.ai.dataset.profiler import ColumnProfile


class SemanticColumnMapping(BaseModel):
    original_name: str
    semantic_name: str
    data_type: str
    role: str  # dimension, measure, target, identifier, temporal_dimension, geographic_dimension
    confidence: float
    requires_confirmation: bool = False
    unit: str | None = None
    currency: str | None = None
    aggregation_default: str = "sum"  # sum, avg, count, rate


class SemanticMapper:
    """Infers semantic meaning and business roles without unsafe domain conflation."""

    # Semantic alias dictionary: canonical_name -> (patterns, role, default_unit, default_curr, default_agg)
    SEMANTIC_PATTERNS = [
        # Financial / Commercial
        ("sales_amount", [r"\bsales(_amount)?\b", r"\bgross_sales\b", r"\btransaction_amount\b", r"\border_amount\b"], "measure", "currency", "USD", "sum"),
        ("revenue", [r"\b(gross_)?revenue\b", r"\btotal_rev\b"], "measure", "currency", "USD", "sum"),
        ("net_profit", [r"\b(net_)?profit\b", r"\bearnings\b", r"\bnet_income\b"], "measure", "currency", "USD", "sum"),
        ("operating_margin", [r"\b(operating_)?margin(_pct)?\b", r"\bprofit_margin\b"], "measure", "percentage", None, "avg"),
        ("unit_price", [r"\b(unit_)?price\b", r"\brate\b", r"\bmsrp\b"], "measure", "currency", "USD", "avg"),
        ("unit_cost", [r"\b(unit_)?cost\b", r"\bcogs\b"], "measure", "currency", "USD", "avg"),
        ("discount", [r"\bdiscount(_amount|_pct)?\b"], "measure", "percentage", None, "avg"),
        ("quantity_ordered", [r"\b(qty|quantity|units(_sold)?)\b"], "measure", "count", None, "sum"),
        ("order_id", [r"\border(_)?id\b", r"\binvoice(_)?(no|num|id)\b"], "identifier", None, None, "count"),
        
        # Geographic
        ("region", [r"\b(sales_)?region\b", r"\bterritory\b", r"\bzone\b"], "geographic_dimension", None, None, "count"),
        ("city", [r"\bcity\b", r"\btown\b", r"\bmetro\b"], "geographic_dimension", None, None, "count"),
        ("state", [r"\bstate\b", r"\bprovince\b"], "geographic_dimension", None, None, "count"),
        ("country", [r"\bcountry\b", r"\bnation\b"], "geographic_dimension", None, None, "count"),
        
        # Products / Operations
        ("product_category", [r"\b(product_)?category\b", r"\bitem_group\b"], "dimension", None, None, "count"),
        ("product_name", [r"\b(product|item)(_name|_desc)?\b"], "dimension", None, None, "count"),
        ("salesperson", [r"\b(sales_?rep|salesperson|representative|agent)\b"], "dimension", None, None, "count"),
        ("sales_channel", [r"\b(sales_)?channel\b"], "dimension", None, None, "count"),
        
        # HR / Workforce
        ("employee_age", [r"\b(employee_)?age\b"], "measure", "years", None, "avg"),
        ("education_level", [r"\beducation(_level)?\b", r"\bdegree\b", r"\bqualification\b"], "dimension", None, None, "count"),
        ("joining_year", [r"\bjoining(_)?year\b", r"\bhired?(_)?year\b", r"\bstart(_)?year\b"], "temporal_dimension", "year", None, "count"),
        ("experience_years", [r"\b(experience|tenure)(_years|_in_current_domain)?\b"], "measure", "years", None, "avg"),
        ("payment_tier", [r"\bpayment(_)?tier\b", r"\bsalary(_)?band\b", r"\bgrade\b"], "dimension", None, None, "count"),
        ("employee_gender", [r"\b(employee_)?gender\b", r"\bsex\b"], "dimension", None, None, "count"),
        ("leave_indicator", [r"\bleaveornot\b", r"\b(attrition|left|resigned|churn)\b"], "target", "binary", None, "rate"),
        ("employee_id", [r"\b(emp|employee)(_)?id\b"], "identifier", None, None, "count"),
        ("department", [r"\b(dept|department|division)\b"], "dimension", None, None, "count"),
        
        # Logistics / Inventory
        ("stock_quantity", [r"\b(stock|inventory)(_level|_qty|_count)?\b", r"\bpallets?\b"], "measure", "count", None, "sum"),
        ("warehouse", [r"\bwarehouse\b", r"\bfulfillment_center\b"], "dimension", None, None, "count"),
    ]

    @classmethod
    def map_columns(cls, col_profiles: list[ColumnProfile]) -> list[SemanticColumnMapping]:
        mappings: list[SemanticColumnMapping] = []

        for cp in col_profiles:
            col_raw = cp.name
            col_norm = col_raw.strip().lower().replace(" ", "_").replace("-", "_")

            matched_semantic = None
            matched_role = None
            matched_unit = None
            matched_curr = None
            matched_agg = "sum"
            confidence = 0.50

            # 1. Check exact pattern catalog
            for sem_name, patterns, role, unit, curr, agg in cls.SEMANTIC_PATTERNS:
                for pat in patterns:
                    if re.search(pat, col_norm):
                        matched_semantic = sem_name
                        matched_role = role
                        matched_unit = unit
                        matched_curr = curr
                        matched_agg = agg
                        confidence = 0.95
                        break
                if matched_semantic:
                    break

            # 2. Heuristic fallback based on profiling
            if not matched_semantic:
                if cp.is_identifier:
                    matched_semantic = f"{col_norm}_id" if not col_norm.endswith("id") else col_norm
                    matched_role = "identifier"
                    confidence = 0.85
                elif cp.is_datetime:
                    matched_semantic = col_norm
                    matched_role = "temporal_dimension"
                    confidence = 0.85
                elif cp.is_target_candidate:
                    matched_semantic = col_norm
                    matched_role = "target"
                    confidence = 0.80
                elif cp.is_numeric:
                    matched_semantic = col_norm
                    matched_role = "measure"
                    matched_unit = "%" if cp.is_percentage else ("USD" if cp.is_currency else "count")
                    matched_curr = "USD" if cp.is_currency else None
                    matched_agg = "avg" if cp.is_percentage else "sum"
                    confidence = 0.70
                elif cp.inferred_type == "categorical":
                    matched_semantic = col_norm
                    matched_role = "dimension"
                    confidence = 0.75
                else:
                    matched_semantic = col_norm
                    matched_role = "dimension"
                    confidence = 0.60

            # 3. Confirmation requirement threshold
            requires_confirmation = (confidence < 0.75)

            mappings.append(SemanticColumnMapping(
                original_name=col_raw,
                semantic_name=matched_semantic,
                data_type=cp.data_type,
                role=matched_role,
                confidence=confidence,
                requires_confirmation=requires_confirmation,
                unit=matched_unit,
                currency=matched_curr,
                aggregation_default=matched_agg,
            ))

        return mappings
