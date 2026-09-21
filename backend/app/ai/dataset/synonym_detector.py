"""Synonym Detector for AI Back-Office Copilot.

Builds vocabulary dictionaries and natural-language synonyms for columns,
enabling flexible query planning and conversational resolution.
"""
from __future__ import annotations

from app.ai.dataset.semantic_mapper import SemanticColumnMapping


class SynonymDetector:
    """Detects and maps natural-language query synonyms for dataset columns."""

    SYNONYM_CATALOG: dict[str, list[str]] = {
        "sales_amount": ["sales", "revenue", "gross revenue", "sales dollars", "turnover", "total sales"],
        "revenue": ["gross revenue", "total revenue", "earnings", "top line", "sales"],
        "net_profit": ["profit", "net earnings", "bottom line", "net income"],
        "operating_margin": ["margin", "profit margin", "operating margin percentage"],
        "quantity_ordered": ["quantity", "qty", "volume", "units sold", "units", "items ordered"],
        "region": ["sales region", "territory", "zone", "area"],
        "city": ["location", "town", "metro", "branch location"],
        "product_category": ["category", "item category", "product line", "family"],
        "product_name": ["product", "item", "sku name", "description"],
        "salesperson": ["sales rep", "rep", "representative", "agent", "account executive"],
        "sales_channel": ["channel", "order channel", "sales path"],
        "employee_age": ["age", "staff age", "worker age"],
        "education_level": ["education", "degree", "qualification", "highest degree"],
        "joining_year": ["year joined", "hire year", "start year"],
        "experience_years": ["experience", "tenure", "years of experience", "domain experience"],
        "payment_tier": ["tier", "pay grade", "salary band", "compensation tier"],
        "employee_gender": ["gender", "sex"],
        "leave_indicator": ["attrition", "left", "turnover", "resigned", "departed", "churn"],
        "stock_quantity": ["stock", "inventory level", "pallets", "units in stock"],
        "warehouse": ["depot", "distribution center", "fulfillment center", "plant"],
    }

    @classmethod
    def detect_synonyms(cls, columns: list[SemanticColumnMapping]) -> dict[str, list[str]]:
        synonyms: dict[str, list[str]] = {}

        for c in columns:
            orig = c.original_name
            orig_lower = orig.lower()
            sem = c.semantic_name

            syn_list = set()
            syn_list.add(orig_lower)
            syn_list.add(orig_lower.replace("_", " "))
            syn_list.add(orig_lower.replace("-", " "))

            # Match from catalog
            if sem in cls.SYNONYM_CATALOG:
                for item in cls.SYNONYM_CATALOG[sem]:
                    syn_list.add(item)

            synonyms[orig] = sorted(list(syn_list))

        return synonyms
