"""
Universal Report Engine for AI Back-Office Copilot.
Generates comprehensive, professional reports from any tabular dataset.
"""

from app.reporting.report_composer import ReportComposer
from app.reporting.report_context import ReportContext, build_report_context, compute_filter_hash

__all__ = ["ReportComposer", "ReportContext", "build_report_context", "compute_filter_hash"]
