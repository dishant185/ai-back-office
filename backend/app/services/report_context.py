"""Service facade for Report Context (Rule #4)."""
from app.reporting.report_context import (
    ReportContext,
    build_report_context,
)

__all__ = ["ReportContext", "build_report_context"]
