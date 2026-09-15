from __future__ import annotations

from typing import Any
import pandas as pd
from app.reporting.models import SemanticField


DOMAIN_KEYWORDS: dict[str, dict[str, float]] = {
    "hr": {
        "employee_id": 3.0,
        "employee_name": 3.0,
        "education": 2.5,
        "joining_year": 3.0,
        "city": 1.0,
        "payment_tier": 3.0,
        "age": 2.0,
        "gender": 2.0,
        "ever_benched": 3.5,
        "experience_in_current_domain": 3.5,
        "leave_or_not": 4.0,
        "department": 2.0,
        "salary": 2.0,
        "attrition": 3.0,
    },
    "sales": {
        "revenue": 3.5,
        "sales": 3.5,
        "sales_amount": 3.5,
        "profit": 3.0,
        "quantity": 2.5,
        "order_id": 3.0,
        "order_date": 2.5,
        "product": 2.5,
        "category": 2.0,
        "region": 1.5,
        "discount": 2.5,
        "price": 2.5,
    },
    "finance": {
        "expense": 3.5,
        "budget": 3.5,
        "revenue": 2.5,
        "profit": 2.5,
        "account_name": 3.0,
        "ledger": 3.5,
        "invoice_id": 2.5,
        "tax": 2.5,
        "cost": 2.5,
    },
    "inventory": {
        "stock_quantity": 4.0,
        "reorder_level": 4.0,
        "sku": 3.5,
        "warehouse": 3.0,
        "opening_stock": 4.0,
        "closing_stock": 4.0,
        "inventory": 3.5,
    },
    "customer": {
        "customer_id": 3.5,
        "customer_name": 3.5,
        "customer_type": 3.0,
        "churn": 3.0,
        "nps": 3.5,
        "retention": 3.0,
    },
    "marketing": {
        "leads": 3.5,
        "campaign": 3.5,
        "conversions": 3.5,
        "clicks": 3.0,
        "impressions": 3.0,
        "cpc": 3.5,
        "roi": 3.0,
    },
    "automobile": {
        "vehicle": 3.5,
        "model": 2.5,
        "brand": 2.5,
        "make": 2.5,
        "mileage": 3.5,
        "vin": 4.0,
        "fuel_type": 3.5,
    },
}


class DomainDetector:
    """Classifies dataset into business domains with confidence scoring."""

    @classmethod
    def detect(cls, fields: list[SemanticField]) -> tuple[str, float, list[str]]:
        scores: dict[str, float] = {d: 0.0 for d in DOMAIN_KEYWORDS}

        for field in fields:
            name = field.normalized_name
            for domain, weights in DOMAIN_KEYWORDS.items():
                if name in weights:
                    scores[domain] += weights[name]

        # Sort domains by score descending
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_domain, top_score = sorted_domains[0]

        # Minimum threshold of 4.0 to claim a specialized domain
        if top_score < 3.5:
            return "generic", 1.0, []

        # Calculate confidence
        confidence = min(1.0, top_score / 12.0)

        # Identify secondary domains if significant
        secondaries = [
            d for d, s in sorted_domains[1:]
            if s >= 3.0 and s >= top_score * 0.4
        ]

        return top_domain, round(confidence, 2), secondaries
