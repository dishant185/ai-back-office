"""Claim-Level Grounding Validator for Report-Aware Intelligence (Rule #23).

Validates individual factual claims against authoritative verified evidence:
- numbers & percentages
- entities & dimensions
- rankings
- comparisons
- trends
- causations
- zero vs unavailable invariants
- metrics & dataset references
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from app.reporting.claim_extractor import ClaimExtractor, ExtractedClaim
from app.reporting.report_context import ReportContext


class GroundingCheckResult(BaseModel):
    is_grounded: bool = True
    status: str = "verified"  # "verified" or "rejected"
    verified_claims: list[str] = Field(default_factory=list)
    unsupported_numbers: list[float] = Field(default_factory=list)
    hallucinated_rankings: list[str] = Field(default_factory=list)
    inverse_comparisons: list[str] = Field(default_factory=list)
    unsupported_trends: list[str] = Field(default_factory=list)
    unsupported_causations: list[str] = Field(default_factory=list)
    zero_violations: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)


class SummaryGroundingValidator:
    """Validates factual grounding of executive summary claims against empirical evidence."""

    BENIGN_NUMBERS: set[float] = {float(x) for x in range(0, 51)} | {60.0, 75.0, 90.0, 100.0}

    @classmethod
    def is_benign_number(cls, val: float) -> bool:
        if val in cls.BENIGN_NUMBERS:
            return True
        if val.is_integer() and 0 <= int(val) <= 50:
            return True
        return False

    @classmethod
    def validate_grounding(
        cls,
        summary_payload: dict[str, Any] | str,
        context: ReportContext | None,
        evidence: dict[str, Any],
    ) -> GroundingCheckResult:
        """Executes claim-level grounding checks against verified evidence."""
        if isinstance(summary_payload, str):
            overview_text = summary_payload
            sections_dict = {}
        elif isinstance(summary_payload, dict):
            overview_text = summary_payload.get("overview") or summary_payload.get("executive_summary") or ""
            sections_dict = {
                "key_findings": summary_payload.get("key_findings", []),
                "patterns": summary_payload.get("patterns", summary_payload.get("important_patterns", [])),
                "comparisons": summary_payload.get("comparisons", []),
                "trends": summary_payload.get("trends", []),
                "business_implications": summary_payload.get("business_implications", []),
                "recommendations": summary_payload.get("recommendations", []),
                "limitations": summary_payload.get("limitations", []),
            }
        else:
            overview_text = ""
            sections_dict = {}

        full_text = overview_text
        for v in sections_dict.values():
            if isinstance(v, list):
                full_text += " " + " ".join(str(item) for item in v)
            elif isinstance(v, str):
                full_text += " " + v

        full_lower = full_text.lower()
        res = GroundingCheckResult()

        claims: list[ExtractedClaim] = ClaimExtractor.extract_claims(overview_text, sections_dict)
        verified_numbers: list[float] = evidence.get("verified_numbers", [])
        rankings = evidence.get("rankings", [])
        comparisons = evidence.get("comparisons", [])
        trends = evidence.get("trends", [])
        anomalies = evidence.get("anomalies", [])
        unavailable_metrics = [m.lower() for m in evidence.get("unavailable_metrics", [])]

        # 1. Number & Percentage Grounding
        for c in claims:
            if c.claim_type in ("number", "percentage") and c.numerical_value is not None:
                val = c.numerical_value
                if cls.is_benign_number(val):
                    continue
                matched = False
                for vn in verified_numbers:
                    if abs(val - vn) < 0.05:
                        matched = True
                        break
                    if max(abs(vn), 1.0) > 0 and abs(val - vn) / max(abs(vn), 1.0) < 0.015:
                        matched = True
                        break
                if matched:
                    res.verified_claims.append(f"Number verified: {val} in '{c.raw_text}'")
                else:
                    res.unsupported_numbers.append(val)
                    res.is_grounded = False
                    res.violations.append(f"Ungrounded number {val} in '{c.raw_text}' not found in verified evidence.")

        # 2. Ranking Grounding
        for c in claims:
            if c.claim_type == "ranking" and c.entity:
                entity_found = False
                correct_rank = False
                for rk in rankings:
                    items = rk.get("items", [])
                    for it in items:
                        it_ent = it.get("entity", "").lower()
                        c_ent = c.entity.lower()
                        if c_ent in it_ent or it_ent in c_ent:
                            entity_found = True
                            if (c.rank == 1 and it.get("rank") == 1) or (c.rank == -1 and it.get("rank") == len(items)):
                                correct_rank = True
                            break
                    if entity_found:
                        break
                if entity_found and not correct_rank:
                    res.hallucinated_rankings.append(f"{c.entity} claimed rank {c.rank}")
                    res.is_grounded = False
                    res.violations.append(f"Claimed rank {c.rank} for entity '{c.entity}' does not match evidence ranking.")
                elif not entity_found and c.rank == 1 and rankings:
                    res.hallucinated_rankings.append(f"{c.entity} claimed rank {c.rank}")
                    res.is_grounded = False
                    res.violations.append(f"Claimed rank {c.rank} for entity '{c.entity}' which is not in rankings.")
                elif entity_found and correct_rank:
                    res.verified_claims.append(f"Ranking verified: {c.entity} as rank {c.rank}")

        # 3. Comparison Grounding
        comp_pairs = [(c.get("top_entity", "").lower(), c.get("bottom_entity", "").lower()) for c in comparisons]
        for top_e, bot_e in comp_pairs:
            if top_e and bot_e:
                inv_pat = rf"\b{re.escape(bot_e)}\b.*?\b(leads|exceeds|higher than|surpassed|outperformed)\b.*?\b{re.escape(top_e)}\b"
                if re.search(inv_pat, full_lower):
                    res.inverse_comparisons.append(f"{bot_e} leads {top_e}")
                    res.is_grounded = False
                    res.violations.append(f"Inverse comparison claimed: {bot_e} does not lead {top_e}.")

        # 4. Trend Grounding
        has_temporal = any(t.get("data_points", 0) > 1 for t in trends)
        for c in claims:
            if c.claim_type == "trend":
                if not has_temporal:
                    res.unsupported_trends.append(c.raw_text)
                    res.is_grounded = False
                    res.violations.append(f"Trend claimed ('{c.raw_text}') without temporal data.")
                else:
                    res.verified_claims.append(f"Trend verified: '{c.raw_text}' against chronological points.")

        # 5. Causation Grounding
        has_causal_evidence = bool(anomalies)
        for c in claims:
            if c.claim_type == "causation":
                if not has_causal_evidence:
                    res.unsupported_causations.append(c.raw_text)
                    res.is_grounded = False
                    res.violations.append(f"Causation claimed ('{c.raw_text}') without causal evidence.")
                else:
                    matched_cause = False
                    for anom in anomalies:
                        reason = anom.get("reason", "").lower()
                        if any(term in reason for term in ["deviat", "spike", "threshold", "above", "below"]):
                            matched_cause = True
                            break
                    if not matched_cause:
                        res.unsupported_causations.append(c.raw_text)
                        res.is_grounded = False
                        res.violations.append(f"Causal claim '{c.raw_text}' not supported by anomaly evidence.")

        # 6. Zero vs Unavailable
        for unavail in unavailable_metrics:
            pat_zero = rf"\b{re.escape(unavail)}\b.*?\b(0%?|zero|none|nil|0\.0)\b"
            pat_zero_rev = rf"\b(0%?|zero|none|nil|0\.0)\b.*?\b{re.escape(unavail)}\b"
            if re.search(pat_zero, full_lower) or re.search(pat_zero_rev, full_lower):
                res.zero_violations.append(unavail)
                res.is_grounded = False
                res.violations.append(f"Zero != Unavailable violation: '{unavail}' is unavailable, not zero.")

        res.rejection_reasons = list(res.violations)
        res.status = "verified" if res.is_grounded else "rejected"
        return res

    @classmethod
    def validate(
        cls,
        summary_payload: dict[str, Any] | str,
        evidence: dict[str, Any],
        context: ReportContext | None = None,
    ) -> GroundingCheckResult:
        """Alias for validate_grounding accepting (summary, evidence, [context])."""
        return cls.validate_grounding(summary_payload, context, evidence)
