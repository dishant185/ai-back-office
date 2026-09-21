"""Domain Detector for AI Back-Office Copilot.

Classifies tabular datasets into business domains:
HR, SALES, INVENTORY, FINANCE, CUSTOMER, MARKETING, AUTOMOTIVE, OPERATIONS, GENERIC, MIXED.
Strictly evidence-driven: if evidence is ambiguous or insufficient, safely defaults to 'generic'.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from app.ai.dataset.semantic_mapper import SemanticColumnMapping


class DomainDetectionResult(BaseModel):
    domain: str  # hr, sales, inventory, finance, customer, marketing, automotive, operations, generic, mixed
    confidence: float
    matched_signals: list[str] = Field(default_factory=list)
    secondary_domain: str | None = None


class DomainDetector:
    """Detects dataset business domain using semantic column mappings and vocabulary heuristics."""

    DOMAIN_RULES: dict[str, list[str]] = {
        "hr": [
            "employee", "attrition", "leaveornot", "education", "joining_year", "experience",
            "department", "salary", "payroll", "headcount", "gender", "tenure", "job_role"
        ],
        "sales": [
            "sales", "revenue", "order", "product", "discount", "quantity", "salesperson",
            "invoice", "retail", "wholesale", "deal", "channel", "margin", "customer"
        ],
        "inventory": [
            "stock", "inventory", "warehouse", "sku", "pallet", "reorder", "bin",
            "storage", "quantity_on_hand", "batch", "lot"
        ],
        "finance": [
            "ebitda", "profit", "cogs", "asset", "liability", "equity", "tax", "ledger",
            "depreciation", "cash_flow", "balance", "expense"
        ],
        "customer": [
            "customer_id", "churn", "lifetime_value", "clv", "nps", "csat", "segment",
            "satisfaction", "retention", "support_ticket"
        ],
        "automotive": [
            "dealer", "dealership", "vin", "make", "model", "trim", "mileage",
            "odometer", "showroom", "vehicle"
        ],
        "marketing": [
            "campaign", "impressions", "clicks", "ctr", "cpc", "roas", "ad_spend",
            "lead", "conversion_rate"
        ],
        "operations": [
            "sla", "throughput", "cycle_time", "lead_time", "downtime", "defect",
            "incident", "machine", "work_order"
        ],
    }

    @classmethod
    def detect_domain(
        cls,
        columns: list[SemanticColumnMapping],
        file_name: str = "",
    ) -> DomainDetectionResult:
        col_tokens = set()
        for col in columns:
            col_tokens.add(col.semantic_name.lower())
            for part in re.split(r"[_\s\-]+", col.original_name.lower()):
                if part:
                    col_tokens.add(part)

        file_low = file_name.lower()
        scores: dict[str, int] = {d: 0 for d in cls.DOMAIN_RULES}
        matched: dict[str, list[str]] = {d: [] for d in cls.DOMAIN_RULES}

        # Check filename bonus
        for d in cls.DOMAIN_RULES:
            if d in file_low or (d == "hr" and any(k in file_low for k in ["employee", "worker", "staff"])):
                scores[d] += 3
                matched[d].append(f"filename_matches_{d}")

        # Check column signals
        for d, keywords in cls.DOMAIN_RULES.items():
            for kw in keywords:
                for tok in col_tokens:
                    if kw in tok or tok in kw:
                        scores[d] += 1
                        matched[d].append(tok)
                        break

        # Sort candidate domains
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_d, top_score = ranked[0]
        second_d, second_score = ranked[1]

        # Domain classification logic
        if top_score < 2:
            return DomainDetectionResult(
                domain="generic",
                confidence=0.50,
                matched_signals=[],
            )

        # Check for mixed dataset
        if top_score >= 3 and second_score >= 3 and (top_score - second_score) <= 1:
            return DomainDetectionResult(
                domain="mixed",
                confidence=0.80,
                matched_signals=matched[top_d] + matched[second_d],
                secondary_domain=f"{top_d}_{second_d}",
            )

        conf = min(0.95, 0.60 + (top_score * 0.08))
        return DomainDetectionResult(
            domain=top_d,
            confidence=conf,
            matched_signals=matched[top_d],
            secondary_domain=second_d if second_score >= 2 else None,
        )
