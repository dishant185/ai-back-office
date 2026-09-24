"""Universal Semantic Mapping Engine.

Maps source dataset columns to canonical semantic definitions with confidence scores,
business roles, units, and clear explanations across ANY business domain:
- HR / Workforce
- Sales / Commercial
- Finance / Accounting
- Inventory / Supply Chain
- Operations / Logistics
- Retail / E-Commerce
- Automobile / Manufacturing
- SaaS / Technology
- Customer / CRM
- Healthcare / Operations
- Generic / Unknown Datasets

Preserves:
source_column, semantic_name, role, unit, definition, confidence, status
"""
from __future__ import annotations

import re
from typing import Any
import pandas as pd
from pydantic import BaseModel, Field


class SemanticFieldMapping(BaseModel):
    source_column: str
    detected_type: str  # numeric, categorical, date, id, boolean
    semantic_name: str
    suggested_label: str
    role: str  # dimension, measure, time_dimension, identifier, outcome, status
    unit: str  # currency, count, percentage, years, units, text, flag
    definition: str
    confidence: float  # 0.0 to 1.0
    status: str = "suggested"  # suggested, confirmed, edited, ignored
    transformation: str | None = None
    is_confirmed: bool = False


class SemanticMappingCatalog(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    domain_hint: str
    mappings: list[SemanticFieldMapping] = Field(default_factory=list)
    confidence_summary: dict[str, Any] = Field(default_factory=dict)


class UniversalSemanticMappingEngine:
    """Universal engine inferring business semantics from raw column names and content."""

    # Explicit semantic match rules ordered by specificity
    RULES: list[dict[str, Any]] = [
        # Domain Experience vs Company Tenure (CRITICAL RULE)
        {
            "match": lambda c, s: any(x in c for x in ["experience_in_current_domain", "experienceincurrentdomain", "domain_experience", "domainexperience"]),
            "semantic_name": "current_domain_experience",
            "label": "Domain Experience",
            "role": "measure",
            "unit": "years",
            "definition": "Recorded years of professional experience in employee's current domain",
            "confidence": 0.98,
        },
        {
            "match": lambda c, s: any(x in c for x in ["years_at_company", "yearsatcompany", "company_tenure", "companytenure", "tenure"]),
            "semantic_name": "company_tenure",
            "label": "Company Tenure",
            "role": "measure",
            "unit": "years",
            "definition": "Total length of continuous service at the current company",
            "confidence": 0.95,
        },
        # Separation / Attrition / Churn
        {
            "match": lambda c, s: any(x in c for x in ["leave_or_not", "leaveornot", "attrition", "left", "resigned", "churn", "churned", "is_churn"]),
            "semantic_name": "separation_indicator",
            "label": "Separation / Attrition Flag",
            "role": "outcome",
            "unit": "flag",
            "definition": "Binary indicator marking departure, resignation, attrition, or customer churn",
            "confidence": 0.96,
        },
        # Revenue & Sales Value
        {
            "match": lambda c, s: any(x in c for x in ["sales_amount", "salesamount", "sales_value", "salesvalue", "booking_value", "order_value", "total_sales"]),
            "semantic_name": "sales_value",
            "label": "Sales Value",
            "role": "measure",
            "unit": "currency",
            "definition": "Gross monetary transaction value generated from sales",
            "confidence": 0.96,
        },
        {
            "match": lambda c, s: any(x in c for x in ["mrr", "monthly_recurring_revenue", "arr", "annual_recurring_revenue"]),
            "semantic_name": "recurring_revenue",
            "label": "Recurring Revenue",
            "role": "measure",
            "unit": "currency",
            "definition": "Predictable subscription or recurring contracted revenue",
            "confidence": 0.98,
        },
        {
            "match": lambda c, s: any(x in c for x in ["revenue", "turnover", "gross_revenue", "top_line"]),
            "semantic_name": "revenue",
            "label": "Revenue",
            "role": "measure",
            "unit": "currency",
            "definition": "Commercial gross operating revenue recognized",
            "confidence": 0.96,
        },
        # Profit / Margins
        {
            "match": lambda c, s: "net_profit" in c or "netprofit" in c or "net_income" in c,
            "semantic_name": "net_profit",
            "label": "Net Profit",
            "role": "measure",
            "unit": "currency",
            "definition": "Net earnings after accounting for direct expenses, overhead, and taxes",
            "confidence": 0.97,
        },
        {
            "match": lambda c, s: "profit" in c and "margin" not in c and "rate" not in c,
            "semantic_name": "profit",
            "label": "Operating Profit",
            "role": "measure",
            "unit": "currency",
            "definition": "Operating profit or contribution margin",
            "confidence": 0.92,
        },
        {
            "match": lambda c, s: "profit_margin" in c or "margin_pct" in c or "margin" in c,
            "semantic_name": "profit_margin",
            "label": "Profit Margin",
            "role": "measure",
            "unit": "percentage",
            "definition": "Percentage share of revenue retained as profit",
            "confidence": 0.94,
        },
        # Volume & Quantity
        {
            "match": lambda c, s: any(x in c for x in ["quantity", "qty", "units_sold", "units_produced", "units", "volume", "order_quantity"]),
            "semantic_name": "order_volume",
            "label": "Unit Volume",
            "role": "measure",
            "unit": "count",
            "definition": "Physical units or transaction quantity fulfilled",
            "confidence": 0.95,
        },
        # Discounts & Pricing
        {
            "match": lambda c, s: any(x in c for x in ["discount_pct", "discount_rate", "discount_percentage"]),
            "semantic_name": "discount_percentage",
            "label": "Discount Rate",
            "role": "measure",
            "unit": "percentage",
            "definition": "Concession or promotional markdown percentage applied",
            "confidence": 0.95,
        },
        {
            "match": lambda c, s: any(x in c for x in ["discount", "discount_amount"]),
            "semantic_name": "discount_amount",
            "label": "Discount Amount",
            "role": "measure",
            "unit": "currency",
            "definition": "Monetary discount or promotional rebate deduction",
            "confidence": 0.92,
        },
        # Temporal Fields
        {
            "match": lambda c, s: any(x in c for x in ["order_date", "orderdate", "transaction_date", "invoice_date", "sale_date"]),
            "semantic_name": "transaction_date",
            "label": "Transaction Date",
            "role": "time_dimension",
            "unit": "date",
            "definition": "Timestamp when transaction or business event occurred",
            "confidence": 0.98,
        },
        {
            "match": lambda c, s: any(x in c for x in ["hire_date", "joining_date", "start_date", "created_at", "signup_date"]),
            "semantic_name": "effective_start_date",
            "label": "Start / Registration Date",
            "role": "time_dimension",
            "unit": "date",
            "definition": "Recorded date of entity onboarding, hiring, or account creation",
            "confidence": 0.96,
        },
        # Geographic Dimensions
        {
            "match": lambda c, s: any(x in c for x in ["region", "territory", "market_area", "geography"]),
            "semantic_name": "geography",
            "label": "Geographic Region",
            "role": "dimension",
            "unit": "text",
            "definition": "Geographic operational territory or regional market segment",
            "confidence": 0.97,
        },
        {
            "match": lambda c, s: any(x in c for x in ["city", "town", "metro", "municipality"]),
            "semantic_name": "city",
            "label": "City / Location",
            "role": "dimension",
            "unit": "text",
            "definition": "Metropolitan center or municipal branch location",
            "confidence": 0.96,
        },
        {
            "match": lambda c, s: any(x in c for x in ["country", "nation", "state", "province"]),
            "semantic_name": "country_state",
            "label": "Country / State",
            "role": "dimension",
            "unit": "text",
            "definition": "Sovereign nation, state, or provincial jurisdiction",
            "confidence": 0.96,
        },
        # Organizational & Product Entities
        {
            "match": lambda c, s: any(x in c for x in ["department", "dept", "business_unit", "division", "practice"]),
            "semantic_name": "department",
            "label": "Department / Division",
            "role": "dimension",
            "unit": "text",
            "definition": "Functional organizational business department or corporate unit",
            "confidence": 0.97,
        },
        {
            "match": lambda c, s: any(x in c for x in ["category", "product_category", "item_category", "segment"]),
            "semantic_name": "category",
            "label": "Product Category",
            "role": "dimension",
            "unit": "text",
            "definition": "High-level classification or line of business taxonomy",
            "confidence": 0.94,
        },
        {
            "match": lambda c, s: any(x in c for x in ["product", "sku", "item", "product_name", "part_number", "model"]),
            "semantic_name": "product_item",
            "label": "Product / Item",
            "role": "dimension",
            "unit": "text",
            "definition": "Specific commercial product, SKU, vehicle model, or catalog item",
            "confidence": 0.94,
        },
        # Automobile / Manufacturing specific
        {
            "match": lambda c, s: any(x in c for x in ["vin", "vehicle_id", "chassis_number"]),
            "semantic_name": "vehicle_identifier",
            "label": "Vehicle Identification Number (VIN)",
            "role": "identifier",
            "unit": "text",
            "definition": "Unique serialized automobile or asset identifier",
            "confidence": 0.99,
        },
        {
            "match": lambda c, s: any(x in c for x in ["defect", "defects", "scrap", "rework_count", "failure_rate"]),
            "semantic_name": "defect_metric",
            "label": "Defect / Quality Incident",
            "role": "measure",
            "unit": "count",
            "definition": "Recorded manufacturing defect or operational failure count",
            "confidence": 0.95,
        },
        # Customer / Client
        {
            "match": lambda c, s: any(x in c for x in ["customer_name", "client_name", "account_name", "customer_id", "client_id"]),
            "semantic_name": "customer_account",
            "label": "Customer / Client Account",
            "role": "dimension",
            "unit": "text",
            "definition": "Purchasing commercial client or consumer entity",
            "confidence": 0.96,
        },
        # Identifiers (General)
        {
            "match": lambda c, s: c.endswith("_id") or c.endswith("id") or c.startswith("id_") or "uuid" in c,
            "semantic_name": "record_identifier",
            "label": "Record Identifier",
            "role": "identifier",
            "unit": "text",
            "definition": "Unique key or database primary/foreign identifier",
            "confidence": 0.92,
        },
    ]

    @classmethod
    def analyze(cls, frame: pd.DataFrame, dataset_id: str = "dataset") -> SemanticMappingCatalog:
        row_count = int(len(frame))
        col_count = int(len(frame.columns))
        mappings: list[SemanticFieldMapping] = []
        domain_votes: dict[str, int] = {"generic": 1}

        for col in frame.columns:
            s = frame[col]
            c_low = str(col).lower().replace("-", "_").replace(" ", "_").strip()
            detected_type = cls._detect_data_type(s, str(col))

            matched_rule = None
            for rule in cls.RULES:
                try:
                    if rule["match"](c_low, s):
                        matched_rule = rule
                        break
                except Exception:
                    continue

            if matched_rule:
                sem_name = matched_rule["semantic_name"]
                label = matched_rule["label"]
                role = matched_rule["role"]
                unit = matched_rule["unit"]
                definition = matched_rule["definition"]
                conf = matched_rule["confidence"]

                # Track domain hints
                if sem_name in ("current_domain_experience", "company_tenure", "separation_indicator", "department"):
                    domain_votes["hr"] = domain_votes.get("hr", 0) + 2
                elif sem_name in ("sales_value", "recurring_revenue", "discount_percentage", "revenue"):
                    domain_votes["sales"] = domain_votes.get("sales", 0) + 2
                elif sem_name in ("net_profit", "profit", "profit_margin"):
                    domain_votes["finance"] = domain_votes.get("finance", 0) + 2
                elif sem_name in ("vehicle_identifier", "defect_metric"):
                    domain_votes["automobile"] = domain_votes.get("automobile", 0) + 3
                elif sem_name in ("customer_account",):
                    domain_votes["crm"] = domain_votes.get("crm", 0) + 2
            else:
                # Generic fallback inference
                clean_title = str(col).replace("_", " ").title()
                if detected_type == "numeric":
                    sem_name = c_low
                    label = clean_title
                    role = "measure"
                    unit = "units"
                    definition = f"Numerical metric representing {clean_title}"
                    conf = 0.80
                elif detected_type == "date":
                    sem_name = f"{c_low}_date"
                    label = f"{clean_title} Date"
                    role = "time_dimension"
                    unit = "date"
                    definition = f"Timestamp observation for {clean_title}"
                    conf = 0.85
                elif detected_type == "boolean":
                    sem_name = f"is_{c_low}"
                    label = f"{clean_title} Status"
                    role = "status"
                    unit = "flag"
                    definition = f"Binary indicator for {clean_title}"
                    conf = 0.85
                elif detected_type == "id":
                    sem_name = f"{c_low}_key"
                    label = f"{clean_title} Key"
                    role = "identifier"
                    unit = "text"
                    definition = f"Unique identifier for {clean_title}"
                    conf = 0.88
                else:
                    sem_name = c_low
                    label = clean_title
                    role = "dimension"
                    unit = "text"
                    definition = f"Categorical classification by {clean_title}"
                    conf = 0.80

            mappings.append(SemanticFieldMapping(
                source_column=str(col),
                detected_type=detected_type,
                semantic_name=sem_name,
                suggested_label=label,
                role=role,
                unit=unit,
                definition=definition,
                confidence=round(conf, 2),
                status="suggested",
            ))

        primary_domain = max(domain_votes.items(), key=lambda x: x[1])[0]
        avg_conf = sum(m.confidence for m in mappings) / max(len(mappings), 1)

        return SemanticMappingCatalog(
            dataset_id=dataset_id,
            row_count=row_count,
            column_count=col_count,
            domain_hint=primary_domain,
            mappings=mappings,
            confidence_summary={
                "average_confidence": round(avg_conf, 2),
                "high_confidence_fields": len([m for m in mappings if m.confidence >= 0.90]),
                "needs_review_fields": len([m for m in mappings if m.confidence < 0.85]),
            },
        )

    @classmethod
    def _detect_data_type(cls, series: pd.Series, col_name: str) -> str:
        c_low = col_name.lower()
        if pd.api.types.is_datetime64_any_dtype(series):
            return "date"
        if any(d in c_low for d in ["date", "timestamp", "created_at", "order_date"]):
            try:
                valid = pd.to_datetime(series.dropna().head(10), errors="coerce")
                if valid.notna().sum() > 0:
                    return "date"
            except Exception:
                pass

        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        non_null = series.dropna()
        if non_null.empty:
            return "categorical"

        unique_c = int(non_null.nunique())
        row_c = len(series)

        if unique_c == 2 and set(non_null.astype(str).str.lower().unique()).issubset({"0", "1", "true", "false", "yes", "no"}):
            return "boolean"

        if (c_low.endswith("_id") or c_low.endswith("id") or "code" in c_low or "vin" in c_low) and unique_c > 0.7 * row_c:
            return "id"

        return "categorical"
