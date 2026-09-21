"""Response Style Router — Automatically determines the appropriate conversational presentation style.

Separates factual analytics accuracy from response presentation format.
Supports ChatGPT / Gemini-style flexibility:
- Simple factual question -> DIRECT (1 concise sentence)
- Comparison -> COMPARISON (concise delta or comparison table)
- Summary -> SUMMARY (structured sections with overview and key metrics)
- Explanation / Why -> EXPLANATION (evidence-backed explanation)
- Action / Recommendation -> RECOMMENDATION (actionable numbered list)
- Distribution / Table -> TABLE (clean Markdown table)
- Missing metric -> UNAVAILABLE (factual disclaimer, never zero)
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

from app.ai.query_router import QueryClassification, QueryType


class ResponseStyle(str, Enum):
    DIRECT = "DIRECT"
    EXPLANATION = "EXPLANATION"
    COMPARISON = "COMPARISON"
    SUMMARY = "SUMMARY"
    ANALYSIS = "ANALYSIS"
    RECOMMENDATION = "RECOMMENDATION"
    TREND = "TREND"
    TABLE = "TABLE"
    STEP_BY_STEP = "STEP_BY_STEP"
    CLARIFICATION = "CLARIFICATION"
    UNAVAILABLE = "UNAVAILABLE"
    CONVERSATIONAL = "CONVERSATIONAL"


TABLE_TRIGGERS = [
    re.compile(r"\b(show|give|display|provide)\s+(me\s+)?(a\s+)?(table|tabular|breakdown|distribution|matrix|grid)\b", re.I),
    re.compile(r"\b(regional|category|department|city)\s+(breakdown|distribution)\b", re.I),
    re.compile(r"\b(tabulate|table\s+format|grid\s+format)\b", re.I),
    re.compile(r"\b(in|as)\s+(a\s+)?(table|grid)\b", re.I),
]

ANALYSIS_TRIGGERS = [
    re.compile(r"\b(detailed|in-depth|comprehensive|root\s+cause)\s+(analysis|report|breakdown|overview|drivers?)\b", re.I),
    re.compile(r"\bdeep\s+dive\b", re.I),
    re.compile(r"\banalyze\s+(the\s+)?(performance|dataset|numbers|trends?|drivers?|root\s+causes?)\b", re.I),
]

CONVERSATIONAL_GREETINGS = [
    re.compile(r"^(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings)\b", re.I),
    re.compile(r"^(who\s+are\s+you|what\s+can\s+you\s+do|help|help\s+me)\b", re.I),
    re.compile(r"\b(thank\s+you|thanks)\b", re.I),
]


def determine_response_style(
    question: str,
    classification: QueryClassification | None = None,
    context: dict[str, Any] | None = None,
) -> ResponseStyle:
    """Determine the optimal conversational style based on question phrasing and analytics intent.

    Parameters
    ----------
    question:
        The natural language query.
    classification:
        Analytical query classification (QueryType, target_metric, target_dimension, etc.).
        If None, automatically inferred via `classify_query`.
    context:
        Canonical analytics context dict.

    Returns
    -------
    ResponseStyle enum value.
    """
    if classification is None:
        from app.ai.query_router import classify_query
        classification = classify_query(question, context)

    cleaned = question.strip().lower()

    # 1. Unavailable metric handling
    if classification.query_type == QueryType.UNAVAILABLE:
        return ResponseStyle.UNAVAILABLE

    # 2. Conversational greetings
    for pattern in CONVERSATIONAL_GREETINGS:
        if pattern.search(cleaned):
            return ResponseStyle.CONVERSATIONAL

    # 3. Explicit Table requests
    for pattern in TABLE_TRIGGERS:
        if pattern.search(cleaned):
            return ResponseStyle.TABLE

    # 4. Detailed Analysis requests
    for pattern in ANALYSIS_TRIGGERS:
        if pattern.search(cleaned):
            return ResponseStyle.ANALYSIS

    # 5. Recommendation requests
    if classification.query_type == QueryType.RECOMMENDATION or any(
        kw in cleaned for kw in ["recommend", "should we", "should management", "next steps", "action plan", "focus on", "suggest", "actionable"]
    ):
        return ResponseStyle.RECOMMENDATION

    # 6. Explanations & "Why" inquiries
    if classification.query_type == QueryType.EXPLANATION or any(
        kw in cleaned for kw in ["why", "what caused", "reason for", "explain"]
    ):
        return ResponseStyle.EXPLANATION

    # 7. Comparison inquiries
    if classification.query_type == QueryType.COMPARISON or any(
        kw in cleaned for kw in ["compare", "versus", "vs.", "difference between"]
    ):
        return ResponseStyle.COMPARISON

    # 8. Summary inquiries
    if classification.query_type == QueryType.SUMMARY or any(
        kw in cleaned for kw in ["summarize", "executive summary", "overview", "key takeaways", "recap"]
    ):
        return ResponseStyle.SUMMARY

    # 9. Trends & Time-series
    if classification.query_type == QueryType.TREND or any(
        kw in cleaned for kw in ["trend", "over time", "by year", "growth rate", "trajectory", "seasonal"]
    ):
        return ResponseStyle.TREND

    # 10. Direct metrics and simple dimension lookups
    # (e.g. "How many regions?", "What is total revenue?", "Which region has the most?")
    if classification.query_type in (QueryType.DIRECT_METRIC, QueryType.DIMENSION_LOOKUP):
        # If user explicitly asked for distribution/breakdown, use TABLE
        if "distribution" in cleaned or "breakdown" in cleaned:
            return ResponseStyle.TABLE
        return ResponseStyle.DIRECT

    # Fallback to direct or conversational
    return ResponseStyle.DIRECT
