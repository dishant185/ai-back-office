"""Summary Relevance Validator for Dynamic Report Intelligence (Phase 6.7).

Validates topical relevance of the summary strictly against the current report evidence:
- Detects cross-dataset terminology leaks (e.g. HR terms in sales report).
- Detects ungrounded metrics and themes not present in the current report evidence.
- Detects generic corporate buzzwords and unsupported filler phrases.
- Computes empirical relevance score against a configurable threshold (default 0.85).
No static report focus catalog or hardcoded prompt templates.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from app.reporting.report_context import ReportContext


class RelevanceCheckResult(BaseModel):
    is_relevant: bool = True
    relevance_score: float = 1.0
    threshold: float = 0.85
    violations: list[str] = Field(default_factory=list)
    cross_dataset_leaks: list[str] = Field(default_factory=list)
    cross_report_leaks: list[str] = Field(default_factory=list)
    generic_filler_detected: list[str] = Field(default_factory=list)


class SummaryRelevanceValidator:
    """Validates summary topical alignment and eliminates generic filler or cross-report leakage."""

    BANNED_FILLER_PHRASES: list[str] = [
        "operational governance standpoint",
        "organizational resilience",
        "zero synthetic extrapolations",
        "capability density",
        "core organizational weight is balanced",
        "prevent further talent drain and margin compression",
        "proactive retention stay-interviews",
        "analyzed operational roster represents a comprehensive census",
        "stable operational performance across",
        "data hygiene completeness rating of",
        "addressing localized friction points",
        "targeted compensation parity reviews",
        "formalized career progression pathways",
        "synergistic operational alignment",
        "holistic ecosystem paradigm",
        "best-in-class operational excellence",
        "proactive governance",
        "standard operational monitoring",
        "continue standard operational monitoring",
        "review operational factors",
        "operational distributions align",
        "strengthen strategic alignment",
        "improve business performance",
        "distribution evaluation across",
        "distribution evaluation",
        "lowest baseline",
        "leading segment at",
        "operational segments",
        "automated analytical audit",
        "temporal trajectory",
        "talent loss risk",
        "talent drain",
        "industry benchmark",
        "market benchmark",
        "industry standard",
        "standard benchmark",
        "evaluate revenue",
        "evaluate the integrity",
        "evaluate recorded departures",
        "evaluate workforce",
        "primary verified metrics include",
        "you should discuss",
        "the task is to",
        "review the following",
    ]

    HR_SPECIFIC_KEYWORDS: list[str] = [
        "workforce", "headcount", "attrition", "turnover", "employee", "tenure", "retention",
    ]
    SALES_SPECIFIC_KEYWORDS: list[str] = [
        "gross revenue", "sales volume", "sku", "units sold", "order value", "commercial revenue",
    ]
    INVENTORY_SPECIFIC_KEYWORDS: list[str] = [
        "stockout", "reorder point", "safety stock", "warehouse inventory", "inventory turnover",
    ]

    @classmethod
    def validate_relevance(
        cls,
        summary_payload: dict[str, Any] | str,
        context: ReportContext,
        evidence: dict[str, Any] | None = None,
        threshold: float = 0.85,
    ) -> RelevanceCheckResult:
        """Evaluates relevance and leakage against context and current report evidence."""
        if isinstance(summary_payload, str):
            full_text = summary_payload
        elif isinstance(summary_payload, dict):
            overview = summary_payload.get("overview") or summary_payload.get("summary") or summary_payload.get("executive_summary") or ""
            parts = [overview]
            for sec in summary_payload.get("sections", []):
                if isinstance(sec, dict):
                    parts.append(sec.get("title", ""))
                    parts.append(sec.get("content", ""))
                elif isinstance(sec, str):
                    parts.append(sec)
            for k in ["key_findings", "patterns", "comparisons", "trends", "business_implications", "recommendations", "limitations"]:
                v = summary_payload.get(k)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            parts.append(item.get("content") or item.get("statement") or "")
                        else:
                            parts.append(str(item))
                elif isinstance(v, str):
                    parts.append(v)
            full_text = " ".join(parts)
        else:
            full_text = ""

        full_lower = full_text.lower()
        res = RelevanceCheckResult(threshold=threshold)
        penalties: float = 0.0

        # 1. Cross-dataset leaks
        profile = (context.dataset_profile or "").lower()
        if profile == "sales":
            for kw in cls.HR_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    res.cross_dataset_leaks.append(kw)
                    res.violations.append(f"Sales report references unrelated HR concept '{kw}'.")
                    penalties += 0.3
        elif profile == "hr":
            for kw in cls.SALES_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    res.cross_dataset_leaks.append(kw)
                    res.violations.append(f"HR report references unrelated Sales concept '{kw}'.")
                    penalties += 0.3
        elif profile == "inventory":
            for kw in cls.HR_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    res.cross_dataset_leaks.append(kw)
                    res.violations.append(f"Inventory report references unrelated HR concept '{kw}'.")
                    penalties += 0.3

        # 2. Dynamic Evidence Relevance: Check for ungrounded report-level themes
        # E.g. If current report is Data Quality Audit, commercial revenue is not in evidence
        ev_metrics = []
        if evidence:
            ev_metrics = [m.get("id", "").lower() for m in evidence.get("metrics", [])] + [m.get("name", "").lower() for m in evidence.get("metrics", [])]
        
        is_data_quality = (
            "data_quality" in context.report_type.lower()
            or "quality" in context.report_type.lower()
            or "data quality" in context.report_title.lower()
        )
        if is_data_quality:
            # If summary discusses revenue or sales when revenue is not in verified evidence
            has_revenue_in_evidence = any("rev" in m or "sales" in m for m in ev_metrics)
            if not has_revenue_in_evidence:
                for rev_term in ["revenue", "gross revenue", "sales volume", "profit"]:
                    if re.search(r"\b" + re.escape(rev_term) + r"\b", full_lower):
                        res.cross_report_leaks.append(rev_term)
                        res.violations.append(f"Data Quality report references unrelated metric '{rev_term}' not in evidence.")
                        penalties += 0.3

        # 3. Generic corporate filler
        for phrase in cls.BANNED_FILLER_PHRASES:
            if phrase in full_lower:
                res.generic_filler_detected.append(phrase)
                res.violations.append(f"Generic corporate filler detected: '{phrase}'.")
                penalties += 0.2

        # 4. Compute final score
        res.relevance_score = max(0.0, 1.0 - penalties)
        if res.relevance_score < threshold or penalties > 0:
            res.is_relevant = False

        return res

    @classmethod
    def validate(
        cls,
        summary_payload: dict[str, Any] | str,
        context: ReportContext,
        evidence: dict[str, Any] | None = None,
        threshold: float = 0.85,
    ) -> RelevanceCheckResult:
        """Alias for validate_relevance accepting (summary, context, [evidence], [threshold])."""
        return cls.validate_relevance(summary_payload, context, evidence, threshold)
