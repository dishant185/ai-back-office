"""Service facade for Report Summary Validator (Rule #25)."""
from app.reporting.report_summary_validator import (
    ReportSummaryValidator,
    DifferentiationResult,
)

__all__ = ["ReportSummaryValidator", "DifferentiationResult"]
