"""Report Relevance Engine for Production AI Executive Summary Engine V2.

Classifies evidence items as DIRECT, SUPPORTING, or IRRELEVANT.
Strictly prevents cross-report and global dataset contamination:
- Data Quality Audit: permits only hygiene, completeness, and structural metrics.
- Profitability Analysis: rejects workforce metrics (age, education, attrition).
- Workforce Analysis: rejects commercial/revenue/margin metrics.
"""
from __future__ import annotations

from enum import Enum
import re
from typing import Any
from pydantic import BaseModel


class RelevanceCategory(str, Enum):
    DIRECT = "DIRECT"
    SUPPORTING = "SUPPORTING"
    IRRELEVANT = "IRRELEVANT"


class RelevanceClassification(BaseModel):
    evidence_id: str
    category: RelevanceCategory
    reason: str


class ReportRelevanceEngine:
    """Classifies and filters evidence items based on current report scope and purpose."""

    DQ_TERMS = {
        "quality", "missing", "duplicate", "null", "invalid", "completeness",
        "row", "column", "record", "cell", "score", "audit", "hygiene", "schema"
    }
    SALES_TERMS = {
        "revenue", "sales", "profit", "margin", "order", "orders", "aov", "sku",
        "units", "discount", "customer", "price", "gross", "net", "commercial"
    }
    HR_TERMS = {
        "workforce", "headcount", "employee", "attrition", "turnover", "tenure",
        "department", "salary", "experience", "age", "education", "retention"
    }

    @classmethod
    def classify_item(
        cls,
        item: dict[str, Any],
        report_type: str,
        report_title: str,
        report_purpose: str = "",
        dataset_domain: str = "",
    ) -> RelevanceClassification:
        ev_id = str(item.get("id") or item.get("evidence_id") or "")
        name = str(item.get("name") or item.get("metric_name") or item.get("title") or "")
        measure = str(item.get("semantic_measure") or "").lower()
        dim = str(item.get("dimension") or "").lower()
        combined_text = f"{ev_id} {name} {measure} {dim}".lower()

        rpt = (report_type or "").lower()
        title = (report_title or "").lower()
        purpose = (report_purpose or "").lower()
        domain = (dataset_domain or "").lower()

        is_dq_report = (
            "quality" in rpt
            or "quality" in title
            or rpt in ("data_quality", "data_quality_report", "quality_audit")
            or "data quality" in title
        )
        is_hr_report = (
            domain == "hr"
            or any(t in rpt or t in title for t in ["workforce", "headcount", "attrition", "employee", "age", "tenure", "hr"])
        )
        is_profit_report = any(t in rpt or t in title for t in ["profit", "profitability", "margin", "pnl", "ebitda"])
        is_sales_report = (
            any(t in rpt or t in title for t in ["sales", "revenue", "commercial", "order", "customer", "regional"])
            or is_profit_report
        )

        # 1. Data Quality Audit Report Isolation
        if is_dq_report:
            # Check if any DQ terms are present
            is_dq_item = any(t in combined_text for t in cls.DQ_TERMS) or ev_id.startswith("quality.") or "dq" in ev_id
            is_sales_item = any(t in combined_text for t in ["revenue", "profit", "aov", "order_value", "product", "sales"])
            is_hr_item = any(t in combined_text for t in ["attrition", "salary", "employee_count", "education", "age"])

            if is_sales_item or is_hr_item or not is_dq_item:
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.IRRELEVANT,
                    reason="Data Quality Audit permits only structural and data hygiene evidence.",
                )
            return RelevanceClassification(
                evidence_id=ev_id,
                category=RelevanceCategory.DIRECT,
                reason="Direct data hygiene/structure evidence for quality audit.",
            )

        # 2. Profitability Analysis Isolation
        if is_profit_report:
            # Strict rejection of HR concepts unless explicitly part of report
            if any(t in combined_text for t in ["employee", "attrition", "education", "tenure", "workforce", "headcount"]):
                if not any(t in title or t in purpose for t in ["employee", "attrition", "workforce"]):
                    return RelevanceClassification(
                        evidence_id=ev_id,
                        category=RelevanceCategory.IRRELEVANT,
                        reason="Workforce demographic evidence is irrelevant to Profitability Analysis.",
                    )
            if any(t in combined_text for t in ["profit", "margin", "revenue", "ebitda", "gross_profit", "net_profit"]):
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.DIRECT,
                    reason="Direct profitability metric.",
                )
            return RelevanceClassification(
                evidence_id=ev_id,
                category=RelevanceCategory.SUPPORTING,
                reason="Supporting context for profitability.",
            )

        # 3. Workforce / HR Analysis Isolation
        if is_hr_report and not is_sales_report:
            # Reject commercial financial metrics
            if any(t in combined_text for t in ["regional_revenue", "revenue", "gross_margin", "product_revenue", "margin", "sales_volume", "aov"]):
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.IRRELEVANT,
                    reason="Commercial financial metrics are irrelevant to Workforce Analysis.",
                )
            if any(t in combined_text for t in ["employee", "attrition", "headcount", "turnover", "tenure", "department", "education", "age"]):
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.DIRECT,
                    reason="Direct workforce metric.",
                )
            return RelevanceClassification(
                evidence_id=ev_id,
                category=RelevanceCategory.SUPPORTING,
                reason="Supporting workforce context.",
            )

        # 4. Sales Analysis Isolation
        if is_sales_report and not is_hr_report:
            if any(t in combined_text for t in ["attrition", "employee", "turnover", "tenure", "headcount"]):
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.IRRELEVANT,
                    reason="HR metric is irrelevant to Sales Analysis.",
                )
            if any(t in combined_text for t in ["revenue", "sales", "aov", "units", "customer", "region", "product"]):
                return RelevanceClassification(
                    evidence_id=ev_id,
                    category=RelevanceCategory.DIRECT,
                    reason="Direct sales metric.",
                )
            return RelevanceClassification(
                evidence_id=ev_id,
                category=RelevanceCategory.SUPPORTING,
                reason="Supporting sales context.",
            )

        # 5. Generic / Custom Report:
        # If item matches terms in report title or purpose, DIRECT; otherwise SUPPORTING
        title_tokens = set(re.findall(r"\w+", f"{title} {purpose}".lower()))
        item_tokens = set(re.findall(r"\w+", combined_text))
        if title_tokens.intersection(item_tokens):
            return RelevanceClassification(
                evidence_id=ev_id,
                category=RelevanceCategory.DIRECT,
                reason="Directly aligned with report title/purpose.",
            )

        return RelevanceClassification(
            evidence_id=ev_id,
            category=RelevanceCategory.SUPPORTING,
            reason="General contextual evidence for current report.",
        )

    @classmethod
    def filter_evidence_list(
        cls,
        evidence_items: list[dict[str, Any]],
        report_type: str,
        report_title: str,
        report_purpose: str = "",
        dataset_domain: str = "",
    ) -> tuple[list[dict[str, Any]], list[RelevanceClassification]]:
        """Filters out IRRELEVANT evidence items and returns allowed items along with audit log."""
        allowed: list[dict[str, Any]] = []
        classifications: list[RelevanceClassification] = []

        for item in evidence_items:
            cls_res = cls.classify_item(
                item=item,
                report_type=report_type,
                report_title=report_title,
                report_purpose=report_purpose,
                dataset_domain=dataset_domain,
            )
            classifications.append(cls_res)
            if cls_res.category in (RelevanceCategory.DIRECT, RelevanceCategory.SUPPORTING):
                allowed.append(item)

        return allowed, classifications
