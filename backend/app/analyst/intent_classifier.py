"""Universal Intent Classifier for natural language business questions.

Maps user inquiries to 23 canonical analytical intents without hardcoded questions.
Strictly distinguishes COUNT_UNIQUE from TOP_ENTITY and handles extensive paraphrases.

Canonical Intents (23):
  TOTAL, COUNT, COUNT_UNIQUE, AVERAGE, MEDIAN, SUM, MIN, MAX,
  TOP_ENTITY, BOTTOM_ENTITY, RANK, SHARE, COMPARE/COMPARISON,
  FILTER, TREND, GROWTH, DISTRIBUTION, CORRELATION, ANOMALY,
  DATA_QUALITY, MISSING_VALUE_CHECK, SCHEMA, EXPLANATION,
  DUPLICATE_CHECK, DERIVED_METRIC, LIST_UNIQUE, RECOMMENDATION, SUMMARY,
  PERCENTILE
"""
from __future__ import annotations

import re
from typing import Any

from app.data.semantic.schema_builder import SemanticSchema


class IntentClassifier:
    """Classifies user natural-language questions into canonical analytics intents."""

    @classmethod
    def classify(cls, question: str, schema: SemanticSchema | None = None) -> str:
        q = question.strip().lower()

        # 1. Quality queries (Duplicates & Missing Values)
        if re.search(r"\b(duplicate|repeated|duplicates)\b", q):
            return "DUPLICATE_CHECK"
        if re.search(r"\b(missing|null|empty|blank|na)\b", q) and re.search(r"\b(values?|cells?|data|fields?|rows?|records?)\b", q):
            return "MISSING_VALUE_CHECK"

        # 1b. Data Quality (overall quality, completeness, data health)
        if re.search(r"\b(data quality|quality score|quality report|completeness|data health|data integrity)\b", q):
            return "DATA_QUALITY"

        # 1c. Schema queries (column names, field types, dataset structure)
        if re.search(r"\b(schema|columns?|fields?|structure|what data|describe.*dataset|metadata)\b", q) and re.search(r"\b(list|show|what|describe|tell|available)\b", q):
            return "SCHEMA"

        # 1d. Derived metrics (Profit, Attrition)
        if "profit" in q or "margin" in q:
            return "DERIVED_METRIC"
        if "attrition" in q or re.search(r"\b(left|leave|leaving|churn|churned|turnover|resigned)\b", q):
            return "DERIVED_METRIC"

        # 1e. Explanation queries (why, explain, how is it calculated)
        if re.search(r"\b(explain|why|how is|how are|what does|what is meant|reasoning|rationale|methodology)\b", q) and not re.search(r"\b(how many|how much)\b", q):
            return "EXPLANATION"

        # 3. Recommendations & Insights
        if re.search(r"\b(recommend|recommendation|suggestions?|actionable|what should)\b", q):
            return "RECOMMENDATION"
        if re.search(r"\b(insight|insights|overview|summary|summarize|key takeaway)\b", q):
            return "SUMMARY"

        # 3b. Anomaly / Outlier detection queries
        if re.search(r"\b(anomal\w*|outlier\w*|unusual|abnormal|extreme|exceptional|spike\w*|unexpected)\b", q):
            return "ANOMALY"

        # 3c. Correlation queries
        if re.search(r"\b(correlat\w*|relationship between|association|linked to|related to|depends on|influence)\b", q):
            return "CORRELATION"

        # 4. Comparison queries
        if re.search(r"\b(compare|comparison|versus|vs\.?|difference between)\b", q):
            return "COMPARISON"

        # 4b. Pure Numerical Min / Max Aggregations
        if re.search(r"^(what('s|\s+is)\s+(the\s+)?)?(minimum|min)\b", q) and not re.search(r"\b(which|who)\b", q):
            return "MINIMUM"
        if re.search(r"^(what('s|\s+is)\s+(the\s+)?)?(maximum|max)\b", q) and not re.search(r"\b(which|who)\b", q):
            return "MAXIMUM"

        # 5. Top / Bottom Entity queries (including Nth / second-highest / leading / ranks first)
        if re.search(r"\b(which|who|what|show me)\b.*\b(highest|top|most|best|maximum|greatest|largest|leading|leads|first|ranks first|second[\s-]highest|2nd[\s-]highest|third[\s-]highest|3rd[\s-]highest)\b", q):
            return "TOP_ENTITY"
        if re.search(r"\b(ranks first|leads in|first by|leads)\b", q):
            return "TOP_ENTITY"
        if re.search(r"\b(second[\s-]highest|2nd[\s-]highest|third[\s-]highest|3rd[\s-]highest)\b", q):
            return "TOP_ENTITY"
        if re.search(r"\b(highest|top|most|best|greatest|largest|leading|leads)\b.*\b(sales|revenue|amount|employees|transactions|orders|products?|items?|money|value)\b", q):
            return "TOP_ENTITY"
        if re.search(r"\b(which|who|what)\b.*\b(lowest|bottom|least|worst|minimum|smallest)\b", q):
            return "BOTTOM_ENTITY"
        if re.search(r"\b(lowest|bottom|least|worst|smallest)\b.*\b(sales|revenue|amount|employees|transactions|orders|products?|items?)\b", q):
            return "BOTTOM_ENTITY"

        # 5b. Rank queries (explicit ranking requests)
        if re.search(r"\b(rank|ranking|ranked|leaderboard|standings)\b", q):
            return "RANK"

        # 5c. Share queries (explicit share/proportion requests)
        if re.search(r"\b(share|market share|contribution|what percentage|what percent|what portion|what fraction)\b", q):
            return "SHARE"

        # 5d. Percentile queries
        if re.search(r"\b(percentile|quartile|p\d{1,2}|90th|95th|99th|75th|25th|10th)\b", q):
            return "PERCENTILE"

        # 6. CRITICAL: COUNT_UNIQUE vs COUNT
        # Paraphrases: "How many regions?", "How many unique regions?", "How many different regions?", "What is the number of regions?", "Tell me how many regions are covered."
        unique_patterns = [
            r"\bhow many\b.*\b(unique|distinct|different)\b",
            r"\bhow many\b.*\b(regions|products|categories|cities|departments|reps|representatives|branches|states|countries)\b",
            r"\b(number of|count of)\b.*\b(unique|distinct|different)\b",
            r"\b(number of|count of)\b.*\b(regions|products|categories|cities|departments|reps|representatives|branches|states|countries)\b",
            r"\b(how many)\b.*\b(covered|available|represented|present|exist)\b",
            r"\btell me how many\b.*\b(covered|exist|are there)\b",
        ]
        for pat in unique_patterns:
            if re.search(pat, q):
                return "COUNT_UNIQUE"

        # 7. Total Row / Record Count
        if re.search(r"\bhow many\b.*\b(transactions|records|rows|orders|entries|items|employees|people|users|customers)\b", q):
            return "COUNT"
        if re.search(r"\b(total count|row count|record count|total transactions|total employees)\b", q):
            return "COUNT"

        # 7b. Filter queries (show me X where Y)
        if re.search(r"\b(filter|where|only|subset|restrict|show me.*where|show.*with)\b", q) and re.search(r"\b(equals?|greater|less|above|below|between|is|are)\b", q):
            return "FILTER"

        # 8. Numerical Aggregations
        if re.search(r"\b(average|avg|mean)\b", q):
            return "AVERAGE"
        if re.search(r"\b(median)\b", q):
            return "MEDIAN"
        if re.search(r"\b(maximum|highest|max)\b", q) and not re.search(r"\b(which|who)\b", q):
            return "MAXIMUM"
        if re.search(r"\b(minimum|lowest|min)\b", q) and not re.search(r"\b(which|who)\b", q):
            return "MINIMUM"
        # 8b. LIST_UNIQUE (e.g. "What sales channels are available?", "What categories exist?")
        if re.search(r"\b(what|which)\b.*\b(exist|available|used|present|options|types|categories|channels|methods)\b", q):
            return "LIST_UNIQUE"

        if re.search(r"\b(total|sum of|aggregate)\b", q):
            return "SUM"
        if re.search(r"\b(quantity|qty|volume|units sold|units|sales|revenue|amount)\b", q) and not re.search(r"\b(which|who|top|highest|lowest|list|unique|breakdown|distribution|trend|channels|categories|available|exist)\b", q):
            return "SUM"

        # 9. Time Trend / Growth
        if re.search(r"\b(growth rate|growth|growing|grew|declined|declining|year over year|yoy|month over month|mom)\b", q):
            return "GROWTH"
        if re.search(r"\b(trend|over time|monthly|quarterly|yearly|by month|by year|across months)\b", q):
            return "TREND"

        # 10. DISTRIBUTION
        if re.search(r"\b(distribution|breakdown|by each|in each|share of|percentage of|proportion)\b", q):
            return "DISTRIBUTION"

        # Default fallback
        return "SUMMARY"
