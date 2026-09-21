"""Query Router — Classifies incoming user questions into analytical categories.

Determines whether a question can be answered deterministically from
verified metrics or requires reasoning/LLM synthesis.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any


class QueryType(str, Enum):
    DIRECT_METRIC = "DIRECT_METRIC"
    DIMENSION_LOOKUP = "DIMENSION_LOOKUP"
    COMPARISON = "COMPARISON"
    SUMMARY = "SUMMARY"
    EXPLANATION = "EXPLANATION"
    RECOMMENDATION = "RECOMMENDATION"
    TREND = "TREND"
    UNAVAILABLE = "UNAVAILABLE"
    COMPLEX = "COMPLEX"


# Known metric aliases mapped to canonical metric keys
METRIC_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Generic row/record counts
    (re.compile(r"how\s+many\s+(records?|rows?|entries|items?\s+in\s+total)", re.I), "row_count"),
    (re.compile(r"(total|number\s+of)\s+(records?|rows?|entries)", re.I), "row_count"),
    (re.compile(r"row\s*count|record\s*count", re.I), "row_count"),

    # HR metrics
    (re.compile(r"how\s+many\s+(employees?|people|staff|workers)", re.I), "employee_count"),
    (re.compile(r"(total|number\s+of)\s+(employees?|people|staff|workers)", re.I), "employee_count"),
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?(total\s+)?(employee|headcount|staff)\s*(count)?", re.I), "employee_count"),
    (re.compile(r"headcount", re.I), "employee_count"),

    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?average\s+age", re.I), "average_age"),
    (re.compile(r"avg\s+age", re.I), "average_age"),

    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?(attrition|turnover)\s*(rate)?", re.I), "attrition_rate"),
    (re.compile(r"how\s+many\s+(employees?\s+)?(left|quit|resigned|departed)", re.I), "employees_left"),
    (re.compile(r"employees?\s+(that\s+)?left", re.I), "employees_left"),
    (re.compile(r"how\s+many\s+(employees?\s+)?(stayed|retained)", re.I), "employees_retained"),
    (re.compile(r"average\s+joining\s+year", re.I), "avg_joining_year"),

    # Sales metrics
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?total\s+revenue", re.I), "total_revenue"),
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?(total\s+)?sales(\s+amount)?", re.I), "total_revenue"),
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?total\s+profit", re.I), "total_profit"),
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?total\s+quantity", re.I), "total_quantity"),
    (re.compile(r"average\s+(order\s+value|aov)", re.I), "average_order_value"),

    # Inventory / Customer metrics
    (re.compile(r"(what|what\'s)\s+(is\s+)?(the\s+)?(total|number\s+of)\s+products?", re.I), "total_products"),
    (re.compile(r"how\s+many\s+(unique\s+)?products?", re.I), "total_products"),
    (re.compile(r"(total|number\s+of)\s+(low\s+stock|out\s+of\s+stock)", re.I), "low_stock_count"),
    (re.compile(r"how\s+many\s+customers?", re.I), "customer_count"),
    (re.compile(r"(total|number\s+of)\s+customers?", re.I), "customer_count"),
]

# Metrics known to frequently trigger hallucination requests when not present
UNAVAILABLE_METRICS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bebitda\b", re.I), "EBITDA"),
    (re.compile(r"profit\s*margin", re.I), "Profit Margin"),
    (re.compile(r"net\s*income", re.I), "Net Income"),
    (re.compile(r"cash\s*flow", re.I), "Cash Flow"),
    (re.compile(r"customer\s*acquisition\s*cost|cac\b", re.I), "Customer Acquisition Cost (CAC)"),
    (re.compile(r"churn\s*rate", re.I), "Churn Rate"),
    (re.compile(r"lifetime\s*value|ltv\b", re.I), "Customer Lifetime Value (LTV)"),
    (re.compile(r"gross\s*margin", re.I), "Gross Margin"),
    (re.compile(r"return\s*on\s*investment|roi\b", re.I), "Return on Investment (ROI)"),
]

DIMENSION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"which\s+(city|region|location|department|education|product|category|item)\s+(has|had|generat\w+)\s+(the\s+)?(most|highest|top|least|lowest)", re.I), "top_dimension"),
    (re.compile(r"(top|leading|best|strongest|weakest|popular)\s+(city|cities|region|regions|location|locations|department|departments|education|product|products|category|categories|item|items)", re.I), "top_dimension"),
    (re.compile(r"what\s+(are|is)\s+(the\s+)?(strongest|top|leading|best|highest|main|weakest)\s+(products?|categories|items?|cities|departments?|regions?)", re.I), "top_dimension"),
    (re.compile(r"breakdown\s+by\s+(city|region|location|department|education|product|category|gender)", re.I), "dimension_breakdown"),
    (re.compile(r"(city|department|education|region|product|category)\s+distribution", re.I), "dimension_distribution"),
]

COMPARISON_PATTERNS = [
    re.compile(r"compare\s+([A-Za-z0-9\s]+)\s+(and|to|versus|vs\.?)\s+([A-Za-z0-9\s]+)", re.I),
    re.compile(r"difference\s+between\s+([A-Za-z0-9\s]+)\s+and\s+([A-Za-z0-9\s]+)", re.I),
]

EXPLANATION_PATTERNS = [
    re.compile(r"why\s+(is|did|are|was)", re.I),
    re.compile(r"what\s+caused", re.I),
    re.compile(r"reason\s+for", re.I),
    re.compile(r"explain\s+(why|the\s+change|the\s+drop|the\s+increase)", re.I),
]

RECOMMENDATION_PATTERNS = [
    re.compile(r"what\s+should\s+(we|management|the\s+team|company)\s+(do|investigate|focus\s+on)", re.I),
    re.compile(r"(give|provide|show)\s+(me\s+)?(some\s+)?recommendations?", re.I),
    re.compile(r"how\s+can\s+(we|management)\s+(improve|reduce|increase|optimize)", re.I),
    re.compile(r"next\s+steps?", re.I),
    re.compile(r"actionable\s+insights?", re.I),
]

SUMMARY_PATTERNS = [
    re.compile(r"summarize\s+(this\s+)?(dataset|data|report|file)?", re.I),
    re.compile(r"(give|provide)\s+(me\s+)?an?\s+overview", re.I),
    re.compile(r"executive\s+summary", re.I),
    re.compile(r"key\s+takeaways?", re.I),
]

TREND_PATTERNS = [
    re.compile(r"trend\s+(over\s+time|by\s+year|by\s+month)?", re.I),
    re.compile(r"how\s+has\s+([A-Za-z\s]+)\s+changed", re.I),
    re.compile(r"joining\s+trend", re.I),
    re.compile(r"growth\s+rate", re.I),
]


class QueryClassification:
    def __init__(
        self,
        query_type: QueryType,
        target_metric: str | None = None,
        target_dimension: str | None = None,
        unavailable_metric_name: str | None = None,
        comparison_entities: tuple[str, str] | None = None,
    ):
        self.query_type = query_type
        self.target_metric = target_metric
        self.target_dimension = target_dimension
        self.unavailable_metric_name = unavailable_metric_name
        self.comparison_entities = comparison_entities

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type.value,
            "target_metric": self.target_metric,
            "target_dimension": self.target_dimension,
            "unavailable_metric_name": self.unavailable_metric_name,
            "comparison_entities": list(self.comparison_entities) if self.comparison_entities else None,
        }


def classify_query(question: str, context: dict[str, Any] | None = None) -> QueryClassification:
    """Classify a user question into one of 9 analytical query types.
    
    Parameters
    ----------
    question:
        The natural language user query.
    context:
        Optional verified analytics context containing metrics, dimensions, capabilities.
    """
    cleaned = question.strip().lower()
    metrics = context.get("metrics", {}) if context else {}

    # 1. Check for unavailable metrics first
    for pattern, name in UNAVAILABLE_METRICS:
        if pattern.search(cleaned):
            # If the metric is not present in verified context
            metric_key = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            if metric_key not in metrics and name not in metrics:
                return QueryClassification(
                    query_type=QueryType.UNAVAILABLE,
                    unavailable_metric_name=name,
                )

    # 2. Check for explanation queries ("Why is attrition high?", "What caused...")
    for pattern in EXPLANATION_PATTERNS:
        if pattern.search(cleaned):
            return QueryClassification(query_type=QueryType.EXPLANATION)

    # 3. Check for recommendation queries
    for pattern in RECOMMENDATION_PATTERNS:
        if pattern.search(cleaned):
            return QueryClassification(query_type=QueryType.RECOMMENDATION)

    # 4. Check for comparison queries ("Compare Bangalore and Pune")
    for pattern in COMPARISON_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            groups = match.groups()
            ent1 = groups[0].strip()
            ent2 = groups[-1].strip()
            return QueryClassification(
                query_type=QueryType.COMPARISON,
                comparison_entities=(ent1, ent2),
            )

    # 5. Check for summary queries
    for pattern in SUMMARY_PATTERNS:
        if pattern.search(cleaned):
            return QueryClassification(query_type=QueryType.SUMMARY)

    # 6. Check for trend queries
    for pattern in TREND_PATTERNS:
        if pattern.search(cleaned):
            return QueryClassification(query_type=QueryType.TREND)

    # 7. Check for dimension lookups ("Which city has the most employees?", "Top department...")
    for pattern, dim_type in DIMENSION_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            target_dim = "city"
            for candidate in ["product", "category", "item", "department", "education", "region", "location", "city", "gender"]:
                if candidate in cleaned or (candidate + "s") in cleaned or (candidate == "category" and "categories" in cleaned):
                    target_dim = candidate
                    break
            return QueryClassification(
                query_type=QueryType.DIMENSION_LOOKUP,
                target_dimension=target_dim,
            )

    # 8. Check for direct metric lookups
    for pattern, metric_key in METRIC_PATTERNS:
        if pattern.search(cleaned):
            return QueryClassification(
                query_type=QueryType.DIRECT_METRIC,
                target_metric=metric_key,
            )

    # 9. Fallback to complex
    return QueryClassification(query_type=QueryType.COMPLEX)
