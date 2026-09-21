"""Claim Grounding Validator for Production AI Executive Summary Engine V2.

Validates extracted factual claims against authoritative verified evidence:
- Numerical tolerance & rounding matching (e.g. $6.18M vs 6,180,000 -> PASS; 34.39% vs 34.3864% -> PASS; $6.81M -> FAIL)
- Ranking & entity grounding
- Trend grounding
- Causation grounding
- Zero vs Unavailable invariants
- Integrates dedicated validators (Semantics, Benchmarks, Risks, Comparisons, Recommendations, Duplicates)
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from app.reporting.claim_extractor import ClaimExtractor, ExtractedClaim
from app.reporting.report_context import ReportContext
from app.reporting.semantic_validator import SemanticValidator
from app.reporting.benchmark_validator import BenchmarkValidator
from app.reporting.risk_claim_validator import RiskClaimValidator
from app.reporting.trend_validator import TrendValidator
from app.reporting.comparison_validator import ComparisonValidator
from app.reporting.recommendation_validator import RecommendationValidator
from app.reporting.duplicate_claim_detector import DuplicateClaimDetector


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


class ClaimGroundingValidator:
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
    def numbers_match(cls, claim_val: float, evidence_val: float) -> bool:
        """Evaluates whether a claimed number matches an authoritative number within tolerances."""
        if abs(claim_val - evidence_val) < 0.05:
            return True
        # Scale-aware relative tolerance (1.5%)
        denom = max(abs(evidence_val), 1.0)
        if abs(claim_val - evidence_val) / denom < 0.015:
            return True
        return False

    @classmethod
    def validate_grounding(
        cls,
        summary_payload: dict[str, Any] | str,
        evidence: dict[str, Any],
        context: ReportContext | None = None,
    ) -> GroundingCheckResult:
        """Executes claim-level grounding checks against verified evidence."""
        if isinstance(summary_payload, str):
            overview_text = summary_payload
            sections_dict = {}
        elif isinstance(summary_payload, dict):
            overview_text = summary_payload.get("overview") or summary_payload.get("executive_summary") or ""
            raw_secs = summary_payload.get("sections", [])
            sections_dict = {}
            for idx, s in enumerate(raw_secs):
                if isinstance(s, dict):
                    sections_dict[f"sec_{idx}"] = s.get("content", "")
                elif isinstance(s, str):
                    sections_dict[f"sec_{idx}"] = s
            # Legacy fallbacks
            for k in ["key_findings", "patterns", "comparisons", "trends", "business_implications", "recommendations", "limitations"]:
                if k in summary_payload:
                    sections_dict[k] = summary_payload[k]
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
        rankings = evidence.get("rankings", evidence.get("verified_rankings", []))
        comparisons = evidence.get("comparisons", evidence.get("verified_comparisons", []))
        trends = evidence.get("trends", evidence.get("verified_trends", []))
        anomalies = evidence.get("anomalies", evidence.get("verified_anomalies", []))
        unavailable_metrics = [m.lower() for m in evidence.get("unavailable_metrics", [])]
        zero_valid_metrics = [
            m.get("name", "").lower()
            for m in evidence.get("metrics", [])
            if m.get("value") == 0 or m.get("value") == 0.0
        ]

        # 1. Number & Percentage Grounding
        for c in claims:
            if c.claim_type in ("number", "percentage") and c.numerical_value is not None:
                val = c.numerical_value
                if cls.is_benign_number(val):
                    continue
                matched = False
                for vn in verified_numbers:
                    if cls.numbers_match(val, vn):
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
                        it_ent = (it.get("entity") or it.get("label") or "").lower()
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

        # 3. Dedicated Comparison Validation
        comp_res = ComparisonValidator.validate_comparisons(full_text, evidence)
        if not comp_res.is_valid:
            res.is_grounded = False
            res.violations.extend(comp_res.violations)
            res.inverse_comparisons.extend(comp_res.violations)

        # 4. Dedicated Trend Validation
        trend_res = TrendValidator.validate_trends(full_text, evidence)
        if not trend_res.is_valid:
            res.is_grounded = False
            res.violations.extend(trend_res.violations)
            res.unsupported_trends.extend(trend_res.violations)

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
                        if any(term in reason for term in ["deviat", "spike", "threshold", "above", "below", "exceed"]):
                            matched_cause = True
                            break
                    if not matched_cause:
                        res.unsupported_causations.append(c.raw_text)
                        res.is_grounded = False
                        res.violations.append(f"Causal claim '{c.raw_text}' not supported by anomaly evidence.")

        # 6. Zero vs Unavailable Invariant
        for unavail in unavailable_metrics:
            if unavail in zero_valid_metrics:
                continue
            pat_zero = rf"\b{re.escape(unavail)}\b.*?\b(?:0%?|zero|none|nil|0\.0)\b"
            pat_zero_rev = rf"\b(?:0%?|zero|none|nil|0\.0)\b.*?\b{re.escape(unavail)}\b"
            if re.search(pat_zero, full_lower) or re.search(pat_zero_rev, full_lower):
                res.zero_violations.append(unavail)
                res.is_grounded = False
                res.violations.append(f"Zero != Unavailable violation: '{unavail}' is unavailable, not zero.")

        # 7. Dedicated Semantic Validation
        sem_res = SemanticValidator.validate_semantics(full_text, evidence)
        if not sem_res.is_valid:
            res.is_grounded = False
            res.violations.extend(sem_res.violations)

        # 8. Dedicated Benchmark Validation
        bench_res = BenchmarkValidator.validate_benchmarks(full_text, evidence)
        if not bench_res.is_valid:
            res.is_grounded = False
            res.violations.extend(bench_res.violations)

        # 9. Dedicated Risk Validation
        risk_res = RiskClaimValidator.validate_risks(full_text, evidence)
        if not risk_res.is_valid:
            res.is_grounded = False
            res.violations.extend(risk_res.violations)

        # 10. Dedicated Recommendation Validation
        recs_to_check = []
        if isinstance(summary_payload, dict):
            recs_to_check = summary_payload.get("recommendations", [])
            for s in summary_payload.get("sections", []):
                if isinstance(s, dict) and s.get("type") == "recommendation":
                    recs_to_check.append(s)
        rec_res = RecommendationValidator.validate_recommendations(recs_to_check, evidence)
        if not rec_res.is_valid:
            res.is_grounded = False
            res.violations.extend(rec_res.violations)

        # 11. Dedicated Duplicate Claim Detection
        dup_res = DuplicateClaimDetector.detect_duplicates(summary_payload)
        if not dup_res.is_valid:
            res.is_grounded = False
            res.violations.extend(dup_res.violations)

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
        return cls.validate_grounding(summary_payload, evidence, context)
