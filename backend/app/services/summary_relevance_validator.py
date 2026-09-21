"""Service facade for Summary Relevance Validator (Rule #24)."""
from app.reporting.summary_relevance_validator import (
    SummaryRelevanceValidator,
    RelevanceCheckResult,
)

__all__ = ["SummaryRelevanceValidator", "RelevanceCheckResult"]
