"""Capability Detector for AI Back-Office Copilot.

Discovers dataset analytics capabilities dynamically based strictly on available columns.
NEVER requires irrelevant fields across domains (e.g. Employee.csv never requires revenue or transaction_date).
"""
from __future__ import annotations

from app.ai.dataset.semantic_mapper import SemanticColumnMapping


class CapabilityDetector:
    """Dynamically identifies analytics capabilities supported by the dataset."""

    @classmethod
    def detect_capabilities(
        cls,
        columns: list[SemanticColumnMapping],
        domain: str = "generic",
    ) -> list[str]:
        capabilities: list[str] = []
        sem_map = {c.semantic_name: c for c in columns}
        orig_map = {c.original_name.lower(): c for c in columns}

        # 1. Domain-specific primary capabilities
        if domain == "hr":
            capabilities.append("employee_analysis")
            if "leave_indicator" in sem_map or any("leave" in k or "attrition" in k for k in orig_map):
                capabilities.append("attrition_analysis")
            if "education_level" in sem_map or "education" in orig_map:
                capabilities.append("education_analysis")
            if "city" in sem_map or "city" in orig_map:
                capabilities.append("city_analysis")
            if "employee_age" in sem_map or "age" in orig_map:
                capabilities.append("age_analysis")
            if "employee_gender" in sem_map or "gender" in orig_map:
                capabilities.append("gender_analysis")
            if "experience_years" in sem_map or any("experience" in k for k in orig_map):
                capabilities.append("experience_analysis")
            if "payment_tier" in sem_map or any("payment" in k for k in orig_map):
                capabilities.append("compensation_tier_analysis")

        elif domain == "sales":
            capabilities.append("sales_analysis")
            if "region" in sem_map or "region" in orig_map:
                capabilities.append("regional_analysis")
            if "product_category" in sem_map or "product_name" in sem_map or any("product" in k for k in orig_map):
                capabilities.append("product_analysis")
            if "salesperson" in sem_map or any("sales_rep" in k or "salesperson" in k for k in orig_map):
                capabilities.append("salesperson_analysis")
            if "sales_channel" in sem_map or any("channel" in k for k in orig_map):
                capabilities.append("channel_analysis")
            if "discount" in sem_map or "discount" in orig_map:
                capabilities.append("discount_analysis")
            if any(k in sem_map for k in ("net_profit", "operating_margin", "unit_cost")) or "profit" in orig_map:
                capabilities.append("profit_analysis")

        elif domain == "inventory":
            capabilities.append("stock_analysis")
            if "stock_quantity" in sem_map or any("stock" in k or "pallet" in k for k in orig_map):
                capabilities.append("inventory_level_analysis")
            if "warehouse" in sem_map or "warehouse" in orig_map:
                capabilities.append("warehouse_analysis")
            if "product_name" in sem_map or "sku" in orig_map:
                capabilities.append("sku_analysis")

        # 2. Universal capabilities based on column attributes
        has_temporal = any(c.role == "temporal_dimension" or "date" in c.original_name.lower() for c in columns)
        if has_temporal:
            capabilities.append("time_series_analysis")

        has_geo = any(c.role == "geographic_dimension" or c.semantic_name in ("city", "region", "state", "country") for c in columns)
        if has_geo and "regional_analysis" not in capabilities and "city_analysis" not in capabilities:
            capabilities.append("geographic_distribution_analysis")

        numeric_measures = [c for c in columns if c.role == "measure"]
        if len(numeric_measures) >= 2:
            capabilities.append("correlation_analysis")

        if not capabilities:
            capabilities.append("tabular_summary_analysis")

        return sorted(list(set(capabilities)))
