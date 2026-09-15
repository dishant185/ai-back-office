from __future__ import annotations

from typing import Any
from app.reporting.models import ReportTypeStatus


GLOBAL_REPORT_CATALOG = [
    # HR Reports
    {
        "key": "employee_overview",
        "title": "Workforce Overview & Headcount",
        "description": "Total personnel, departmental distribution, and key workforce parameters.",
        "domain": "hr",
        "required_capabilities": ["employee_analysis"],
    },
    {
        "key": "attrition_analysis",
        "title": "Attrition & Retention Diagnostics",
        "description": "Employee departure patterns, risk factors across tenure, and flight probabilities.",
        "domain": "hr",
        "required_capabilities": ["attrition_analysis"],
    },
    {
        "key": "workforce_demographics",
        "title": "Workforce Demographics & Education",
        "description": "Age brackets, educational qualifications, and diversity parity breakdown.",
        "domain": "hr",
        "required_capabilities": ["demographics_analysis"],
    },
    {
        "key": "location_analysis",
        "title": "Regional & Location Distribution",
        "description": "Employee presence and retention breakdown across regional office hubs.",
        "domain": "hr",
        "required_capabilities": ["location_analysis"],
    },
    {
        "key": "compensation_tier_analysis",
        "title": "Compensation & Payment Tier Analysis",
        "description": "Workforce distribution and retention metrics grouped by payment tiers.",
        "domain": "hr",
        "required_capabilities": ["payment_tier_analysis"],
    },

    # Sales Reports
    {
        "key": "revenue_analysis",
        "title": "Revenue & Sales Performance",
        "description": "Top-line commercial revenue trends, volume dynamics, and run-rates.",
        "domain": "sales",
        "required_capabilities": ["revenue_analysis"],
    },
    {
        "key": "profit_margin_analysis",
        "title": "Profitability & Margin Breakdown",
        "description": "Gross and operating margins across product lines and operating markets.",
        "domain": "sales",
        "required_capabilities": ["profit_analysis"],
    },
    {
        "key": "product_sales_analysis",
        "title": "Product & Category Contribution",
        "description": "Top-performing SKUs, product mix, and category contribution analysis.",
        "domain": "sales",
        "required_capabilities": ["product_analysis"],
    },

    # Finance Reports
    {
        "key": "expense_breakdown",
        "title": "Cost & Expenditure Breakdown",
        "description": "Departmental spend tracking, cost category analysis, and budget variance.",
        "domain": "finance",
        "required_capabilities": ["expense_analysis"],
    },

    # Inventory Reports
    {
        "key": "inventory_stock_analysis",
        "title": "Inventory Levels & Stock Readiness",
        "description": "Warehouse stock levels, safety buffer monitoring, and turnover velocity.",
        "domain": "inventory",
        "required_capabilities": ["inventory_analysis"],
    },

    # Universal / Generic Reports
    {
        "key": "tabular_audit_summary",
        "title": "Comprehensive Data Audit & Distribution",
        "description": "Deterministic statistical profiling and value dispersion across all dataset dimensions.",
        "domain": "generic",
        "required_capabilities": ["generic_numeric"],
    },
]


class ReportRegistry:
    """Evaluates catalog report availability against detected capabilities and domain."""

    @classmethod
    def evaluate(cls, domain: str, capabilities: dict[str, bool]) -> list[ReportTypeStatus]:
        statuses: list[ReportTypeStatus] = []

        for report in GLOBAL_REPORT_CATALOG:
            report_domain = report["domain"]
            req_caps = report["required_capabilities"]

            missing = [c for c in req_caps if not capabilities.get(c, False)]
            # Is available if all required capabilities are satisfied AND domain matches or is generic
            is_domain_match = (report_domain == domain) or (report_domain == "generic")
            is_available = is_domain_match and len(missing) == 0

            statuses.append(
                ReportTypeStatus(
                    key=report["key"],
                    title=report["title"],
                    description=report["description"],
                    domain=report_domain,
                    available=is_available,
                    status="Available" if is_available else "Unavailable",
                    required_capabilities=req_caps,
                    missing_capabilities=missing,
                )
            )

        # Sort: available reports first, then domain-matched
        statuses.sort(key=lambda s: (not s.available, s.domain != domain))
        return statuses
