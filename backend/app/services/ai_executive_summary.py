"""Service facade for AI Executive Summary Generator (Rule #21, #22)."""
from app.reporting.executive_summary import (
    ExecutiveSummaryGenerator,
    StructuredSummaryResponse,
    EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
    SUMMARY_PROMPT_VERSION,
)

# Canonical class alias
AIExecutiveSummary = ExecutiveSummaryGenerator

__all__ = [
    "AIExecutiveSummary",
    "ExecutiveSummaryGenerator",
    "StructuredSummaryResponse",
    "EXECUTIVE_SUMMARY_SYSTEM_PROMPT",
    "SUMMARY_PROMPT_VERSION",
]
