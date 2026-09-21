"""Service facade for Summary Grounding Validator (Rule #23)."""
from app.reporting.summary_grounding_validator import (
    SummaryGroundingValidator,
    GroundingCheckResult,
)

__all__ = ["SummaryGroundingValidator", "GroundingCheckResult"]
