from __future__ import annotations

import re
from typing import Any
import pandas as pd

from app.reporting.models import SemanticField


# Comprehensive dictionary of canonical field definitions, aliases, and semantic roles
SEMANTIC_KNOWLEDGE_BASE: dict[str, dict[str, Any]] = {
    # HR Fields
    "employee_id": {
        "aliases": {"employee_id", "emp_id", "staff_id", "id", "employeeid", "empid", "worker_id"},
        "role": "id",
        "type": "string",
    },
    "employee_name": {
        "aliases": {"employee_name", "employee", "name", "staff_name", "full_name", "employeename"},
        "role": "person",
        "type": "string",
    },
    "education": {
        "aliases": {"education", "education_level", "degree", "qualification", "educationlevel"},
        "role": "category",
        "type": "category",
    },
    "joining_year": {
        "aliases": {"joining_year", "joiningyear", "joined_year", "year_joined", "join_date", "hired_year", "year_of_joining"},
        "role": "date",
        "type": "numeric",
    },
    "city": {
        "aliases": {"city", "location", "office_location", "work_city", "employee_city", "branch_city"},
        "role": "category",
        "type": "category",
    },
    "payment_tier": {
        "aliases": {"payment_tier", "paymenttier", "pay_tier", "salary_tier", "tier", "grade", "compensation_tier"},
        "role": "score",
        "type": "category",
    },
    "age": {
        "aliases": {"age", "employee_age", "years_old"},
        "role": "metric",
        "type": "numeric",
    },
    "gender": {
        "aliases": {"gender", "sex"},
        "role": "category",
        "type": "category",
    },
    "ever_benched": {
        "aliases": {"ever_benched", "everbenched", "benched", "bench_status", "was_benched", "on_bench"},
        "role": "boolean",
        "type": "boolean",
    },
    "experience_in_current_domain": {
        "aliases": {
            "experience_in_current_domain",
            "experienceincurrentdomain",
            "domain_experience",
            "years_experience",
            "experience",
            "work_experience",
            "exp_in_domain",
        },
        "role": "metric",
        "type": "numeric",
    },
    "leave_or_not": {
        "aliases": {
            "leave_or_not",
            "leaveornot",
            "left_company",
            "attrition",
            "attrition_flag",
            "resigned",
            "churn",
            "terminated",
            "employment_status",
        },
        "role": "boolean",
        "type": "boolean",
    },
    "department": {
        "aliases": {"department", "dept", "division", "team", "business_unit"},
        "role": "category",
        "type": "category",
    },
    "salary": {
        "aliases": {"salary", "annual_salary", "monthly_salary", "base_pay", "compensation", "wages"},
        "role": "monetary",
        "type": "numeric",
    },

    # Sales Fields
    "revenue": {
        "aliases": {"revenue", "sales", "sales_amount", "total_sales", "turnover", "gross_sales", "net_sales", "amount"},
        "role": "monetary",
        "type": "numeric",
    },
    "profit": {
        "aliases": {"profit", "gross_profit", "net_profit", "margin_amount", "earnings"},
        "role": "monetary",
        "type": "numeric",
    },
    "quantity": {
        "aliases": {"quantity", "qty", "units_sold", "units", "items_sold", "volume"},
        "role": "quantity",
        "type": "numeric",
    },
    "price": {
        "aliases": {"price", "unit_price", "selling_price", "rate", "cost_price"},
        "role": "monetary",
        "type": "numeric",
    },
    "discount": {
        "aliases": {"discount", "discount_pct", "discount_rate", "discount_amount"},
        "role": "percentage",
        "type": "numeric",
    },
    "order_id": {
        "aliases": {"order_id", "order_number", "transaction_id", "invoice_no", "invoice_id", "sale_id"},
        "role": "id",
        "type": "string",
    },
    "order_date": {
        "aliases": {"order_date", "transaction_date", "date", "sale_date", "invoice_date", "timestamp"},
        "role": "date",
        "type": "date",
    },
    "product": {
        "aliases": {"product", "product_name", "item_name", "sku_name", "article", "good"},
        "role": "category",
        "type": "category",
    },
    "category": {
        "aliases": {"category", "product_category", "product_line", "segment", "class"},
        "role": "category",
        "type": "category",
    },
    "region": {
        "aliases": {"region", "territory", "zone", "market", "area", "country", "state"},
        "role": "category",
        "type": "category",
    },

    # Customer Fields
    "customer_id": {
        "aliases": {"customer_id", "client_id", "account_id", "user_id"},
        "role": "id",
        "type": "string",
    },
    "customer_name": {
        "aliases": {"customer_name", "client_name", "customer", "account_name"},
        "role": "person",
        "type": "string",
    },
    "customer_type": {
        "aliases": {"customer_type", "segment", "tier", "account_tier", "client_type"},
        "role": "category",
        "type": "category",
    },

    # Inventory Fields
    "stock_quantity": {
        "aliases": {"stock", "inventory", "stock_qty", "closing_stock", "on_hand", "available_stock"},
        "role": "quantity",
        "type": "numeric",
    },
    "reorder_level": {
        "aliases": {"reorder_level", "min_stock", "safety_stock", "reorder_point"},
        "role": "quantity",
        "type": "numeric",
    },

    # Finance Fields
    "expense": {
        "aliases": {"expense", "cost", "total_expense", "operating_cost", "spend"},
        "role": "monetary",
        "type": "numeric",
    },
    "budget": {
        "aliases": {"budget", "allocated_budget", "target_budget"},
        "role": "monetary",
        "type": "numeric",
    },
}


def normalize_col_name(col: str) -> str:
    """Standardizes any string: CamelCase, snake_case, spaces, hyphens into clean snake_case."""
    text = str(col).strip()
    # Handle CamelCase: split between lowercase/digit and uppercase
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    # Replace non-alphanumeric chars with underscore
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    return text.strip("_").lower()


class SemanticDetector:
    """Infers semantic roles, data types, and confidence for dataset columns."""

    @classmethod
    def detect_field(cls, series: pd.Series, col_name: str) -> SemanticField:
        clean_name = normalize_col_name(col_name)
        sample_vals = [x for x in series.dropna().head(5).tolist() if pd.notna(x)]

        # 1. Match against Semantic Knowledge Base
        for canonical, info in SEMANTIC_KNOWLEDGE_BASE.items():
            if clean_name == canonical or clean_name in info["aliases"]:
                # Check for boolean flag values like 0/1 or Yes/No
                detected_type = info["type"]
                detected_role = info["role"]

                # If it's a known boolean like leave_or_not or ever_benched, verify
                if detected_role == "boolean":
                    return SemanticField(
                        source_column=col_name,
                        normalized_name=canonical,
                        semantic_role="boolean",
                        data_type="boolean",
                        confidence=0.98,
                        sample_values=sample_vals,
                    )

                return SemanticField(
                    source_column=col_name,
                    normalized_name=canonical,
                    semantic_role=detected_role,
                    data_type=detected_type,
                    confidence=0.95,
                    sample_values=sample_vals,
                )

        # 2. Heuristic analysis if not directly recognized in knowledge base
        dtype = series.dtype
        is_numeric = pd.api.types.is_numeric_dtype(dtype)
        unique_count = series.nunique(dropna=True)
        total_count = len(series.dropna())

        # Check for boolean-like column
        if unique_count <= 2 and total_count > 0:
            unique_vals = set(series.dropna().astype(str).str.lower().unique())
            if unique_vals.issubset({"0", "1", "0.0", "1.0", "true", "false", "yes", "no", "y", "n"}):
                return SemanticField(
                    source_column=col_name,
                    normalized_name=clean_name,
                    semantic_role="boolean",
                    data_type="boolean",
                    confidence=0.90,
                    sample_values=sample_vals,
                )

        # Check for ID columns
        if "id" in clean_name or "code" in clean_name or "key" in clean_name or "num" in clean_name:
            if unique_count > total_count * 0.7:  # High cardinality
                return SemanticField(
                    source_column=col_name,
                    normalized_name=clean_name,
                    semantic_role="id",
                    data_type="string",
                    confidence=0.88,
                    sample_values=sample_vals,
                )

        # Check for Date columns
        if any(d in clean_name for d in ["date", "time", "day", "month", "year"]):
            return SemanticField(
                source_column=col_name,
                normalized_name=clean_name,
                semantic_role="date",
                data_type="date",
                confidence=0.85,
                sample_values=sample_vals,
            )

        # Check for Monetary/Metric columns
        if is_numeric:
            if any(m in clean_name for m in ["amount", "revenue", "sales", "cost", "price", "profit", "salary", "spend", "fee"]):
                return SemanticField(
                    source_column=col_name,
                    normalized_name=clean_name,
                    semantic_role="monetary",
                    data_type="numeric",
                    confidence=0.85,
                    sample_values=sample_vals,
                )
            if any(q in clean_name for q in ["qty", "quantity", "count", "units", "items", "volume"]):
                return SemanticField(
                    source_column=col_name,
                    normalized_name=clean_name,
                    semantic_role="quantity",
                    data_type="numeric",
                    confidence=0.85,
                    sample_values=sample_vals,
                )
            if any(p in clean_name for p in ["pct", "percent", "ratio", "rate", "share"]):
                return SemanticField(
                    source_column=col_name,
                    normalized_name=clean_name,
                    semantic_role="percentage",
                    data_type="numeric",
                    confidence=0.85,
                    sample_values=sample_vals,
                )

            return SemanticField(
                source_column=col_name,
                normalized_name=clean_name,
                semantic_role="metric",
                data_type="numeric",
                confidence=0.75,
                sample_values=sample_vals,
            )

        # Low cardinality categorical
        if unique_count <= 25 or unique_count < total_count * 0.2:
            return SemanticField(
                source_column=col_name,
                normalized_name=clean_name,
                semantic_role="category",
                data_type="category",
                confidence=0.70,
                sample_values=sample_vals,
            )

        # Fallback string / dimension
        return SemanticField(
            source_column=col_name,
            normalized_name=clean_name,
            semantic_role="dimension",
            data_type="string",
            confidence=0.60,
            sample_values=sample_vals,
        )

    @classmethod
    def detect_all(cls, frame: pd.DataFrame) -> list[SemanticField]:
        return [cls.detect_field(frame[col], str(col)) for col in frame.columns]
