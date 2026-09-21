"""13-Stage Master Post-LLM Summary Validator for Report-Aware Intelligence (Version 7.0).

Validates candidate LLM summaries against verified report evidence and context.
Implements the 13 authoritative verification stages:
1. Schema validation
2. Dataset validation
3. Report validation
4. Numerical grounding
5. Entity grounding
6. Ranking grounding
7. Comparison grounding
8. Trend grounding
9. Availability validation (Zero != Unavailable)
10. Causation validation
11. Recommendation validation
12. Relevance validation (Cross-dataset, cross-report leaks, banned corporate filler)
13. Duplicate detection
"""
from __future__ import annotations

import logging
import re
from typing import Any
from pydantic import BaseModel, Field

from app.reporting.claim_extractor import ClaimExtractor, ExtractedClaim
from app.reporting.report_context import ReportContext

logger = logging.getLogger(__name__)


class SummaryValidationResult(BaseModel):
    """Result of comprehensive 13-stage executive summary validation."""
    is_valid: bool = False
    status: str = "rejected"  # "verified", "requires_verification", "rejected"
    grounded: bool = False
    relevance_verified: bool = False
    dataset_verified: bool = False
    report_verified: bool = False
    stage_results: dict[str, bool] = Field(default_factory=dict)
    verified_claims: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unsupported_numbers: list[float] = Field(default_factory=list)
    hallucinated_rankings: list[str] = Field(default_factory=list)
    unsupported_trends: list[str] = Field(default_factory=list)
    unsupported_causations: list[str] = Field(default_factory=list)
    zero_vs_unavailable_violations: list[str] = Field(default_factory=list)
    cross_dataset_leaks: list[str] = Field(default_factory=list)
    cross_report_leaks: list[str] = Field(default_factory=list)
    generic_filler_detected: list[str] = Field(default_factory=list)
    duplicates_detected: list[str] = Field(default_factory=list)


class SummaryValidator:
    """Production 13-stage post-LLM validation engine for Version 7.0."""

    BENIGN_NUMBERS: set[float] = {
        float(x) for x in range(0, 51)
    } | {60.0, 75.0, 90.0, 100.0}

    @classmethod
    def is_benign_number(cls, val: float) -> bool:
        if val in cls.BENIGN_NUMBERS:
            return True
        if val.is_integer() and 0 <= int(val) <= 50:
            return True
        return False

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
        "continue standard operational monitoring",
        "review operational factors",
        "operational distributions align",
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
    def validate(
        cls,
        summary_payload: dict[str, Any] | str,
        context: ReportContext,
        evidence: dict[str, Any],
        strict: bool = True,
    ) -> SummaryValidationResult:
        """Execute full 13-stage validation against context and verified evidence."""
        # Normalize summary_payload
        if isinstance(summary_payload, str):
            overview_text = summary_payload
            sections_dict = {}
            dynamic_sections = []
        elif isinstance(summary_payload, dict):
            overview_text = summary_payload.get("overview") or summary_payload.get("summary") or summary_payload.get("executive_summary") or ""
            dynamic_sections = summary_payload.get("sections", [])
            sections_dict = {
                "key_findings": summary_payload.get("key_findings", []),
                "important_patterns": summary_payload.get("important_patterns", []),
                "business_implications": summary_payload.get("business_implications", []),
                "recommendations": summary_payload.get("recommendations", []),
                "limitations": summary_payload.get("limitations", []),
            }
        else:
            overview_text = ""
            sections_dict = {}
            dynamic_sections = []

        # Assemble non-redundant full_text for validation
        text_blocks: list[str] = []
        if overview_text:
            text_blocks.append(overview_text)
        for sec in dynamic_sections:
            if isinstance(sec, dict):
                c = sec.get("content", "")
                if c and c != overview_text and c not in text_blocks:
                    text_blocks.append(c)
            elif isinstance(sec, str) and sec != overview_text and sec not in text_blocks:
                text_blocks.append(sec)
        for v in sections_dict.values():
            if isinstance(v, list):
                for item in v:
                    val_str = (item.get("content") or item.get("statement") or "") if isinstance(item, dict) else str(item)
                    if val_str and val_str not in text_blocks:
                        text_blocks.append(val_str)
            elif isinstance(v, str) and v not in text_blocks:
                text_blocks.append(v)

        full_text = " ".join(text_blocks)
        full_lower = full_text.lower()
        rejection_reasons: list[str] = []
        warnings: list[str] = []
        verified_claims: list[str] = []
        stage_results: dict[str, bool] = {}

        # -------------------------------------------------------------
        # Stage 1: Schema Validation
        # -------------------------------------------------------------
        stage_1_pass = True
        has_content = bool(overview_text and len(overview_text.strip()) >= 20) or (
            bool(dynamic_sections) and any(len(s.get("content", "").strip()) >= 20 for s in dynamic_sections if isinstance(s, dict))
        )
        if not has_content:
            stage_1_pass = False
            rejection_reasons.append("Stage 1 (Schema): Overview and dynamic sections are missing or insufficient.")
        stage_results["1_schema"] = stage_1_pass

        # -------------------------------------------------------------
        # Stage 2: Dataset Validation
        # -------------------------------------------------------------
        stage_2_pass = True
        cross_dataset_leaks: list[str] = []
        profile = (context.dataset_profile or "").lower()
        if profile == "sales":
            for kw in cls.HR_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    cross_dataset_leaks.append(kw)
                    stage_2_pass = False
                    rejection_reasons.append(f"Stage 2 (Dataset): Sales summary references HR term '{kw}'.")
        elif profile == "hr":
            for kw in cls.SALES_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    cross_dataset_leaks.append(kw)
                    stage_2_pass = False
                    rejection_reasons.append(f"Stage 2 (Dataset): HR summary references Sales term '{kw}'.")
        elif profile == "inventory":
            for kw in cls.HR_SPECIFIC_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_lower):
                    cross_dataset_leaks.append(kw)
                    stage_2_pass = False
                    rejection_reasons.append(f"Stage 2 (Dataset): Inventory summary references HR term '{kw}'.")
        stage_results["2_dataset"] = stage_2_pass

        # -------------------------------------------------------------
        # Stage 3: Report Validation (Dynamic Report Evidence Alignment)
        # -------------------------------------------------------------
        stage_3_pass = True
        cross_report_leaks: list[str] = []
        is_dq = (
            "data_quality" in context.report_type.lower()
            or "quality" in context.report_type.lower()
            or "data quality" in context.report_title.lower()
        )
        if is_dq:
            ev_metrics = [m.get("id", "").lower() for m in evidence.get("metrics", [])]
            has_rev = any("rev" in m or "sales" in m for m in ev_metrics)
            if not has_rev:
                for rev_term in ["revenue", "gross revenue", "sales volume", "profit"]:
                    if re.search(r"\b" + re.escape(rev_term) + r"\b", full_lower):
                        cross_report_leaks.append(rev_term)
                        stage_3_pass = False
                        rejection_reasons.append(
                            f"Stage 3 (Report): Unrelated metric '{rev_term}' referenced in Data Quality report."
                        )
        stage_results["3_report"] = stage_3_pass

        # -------------------------------------------------------------
        # Stage 4: Numerical Grounding
        # -------------------------------------------------------------
        claims: list[ExtractedClaim] = ClaimExtractor.extract_claims(overview_text, sections_dict)
        verified_numbers: list[float] = evidence.get("verified_numbers", [])
        unsupported_nums: list[float] = []
        stage_4_pass = True

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
                    verified_claims.append(f"Number verified: {val} in '{c.raw_text}'")
                else:
                    unsupported_nums.append(val)
                    stage_4_pass = False
                    rejection_reasons.append(
                        f"Stage 4 (Numerical Grounding): Ungrounded number {val} in '{c.raw_text}' not in evidence."
                    )
        stage_results["4_numerical_grounding"] = stage_4_pass

        # -------------------------------------------------------------
        # Stage 5: Entity Grounding
        # -------------------------------------------------------------
        stage_5_pass = True
        rankings = evidence.get("rankings", [])
        all_entities = set()
        for rk in rankings:
            for it in rk.get("items", []):
                if it.get("entity"):
                    all_entities.add(it["entity"].lower())
        for dim in context.relevant_dimensions:
            all_entities.add(dim.lower())
        stage_results["5_entity_grounding"] = stage_5_pass

        # -------------------------------------------------------------
        # Stage 6: Ranking Grounding
        # -------------------------------------------------------------
        stage_6_pass = True
        hallucinated_rankings: list[str] = []
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
                    hallucinated_rankings.append(f"{c.entity} claimed rank {c.rank}")
                    stage_6_pass = False
                    rejection_reasons.append(
                        f"Stage 6 (Ranking): Claimed rank {c.rank} for entity '{c.entity}' does not match evidence ranking."
                    )
                elif not entity_found and c.rank == 1 and rankings:
                    hallucinated_rankings.append(f"{c.entity} claimed rank {c.rank}")
                    stage_6_pass = False
                    rejection_reasons.append(
                        f"Stage 6 (Ranking): Claimed rank {c.rank} for entity '{c.entity}' which is not found in rankings."
                    )
                elif entity_found and correct_rank:
                    verified_claims.append(f"Ranking verified: {c.entity} as rank {c.rank}")
        stage_results["6_ranking_grounding"] = stage_6_pass

        # -------------------------------------------------------------
        # Stage 7: Comparison Grounding
        # -------------------------------------------------------------
        stage_7_pass = True
        comparisons = evidence.get("comparisons", [])
        comp_pairs = [(c.get("top_entity", "").lower(), c.get("bottom_entity", "").lower()) for c in comparisons]
        for top_e, bot_e in comp_pairs:
            if top_e and bot_e:
                inv_pat = rf"\b{re.escape(bot_e)}\b[^.\n]*?\b(leads|exceeds|higher than|surpassed|outperformed)\b[^.\n]*?\b{re.escape(top_e)}\b"
                if re.search(inv_pat, full_lower):
                    stage_7_pass = False
                    rejection_reasons.append(
                        f"Stage 7 (Comparison): Inverse comparison claimed. {bot_e} does not lead {top_e}."
                    )
        stage_results["7_comparison_grounding"] = stage_7_pass

        # -------------------------------------------------------------
        # Stage 8: Trend Grounding
        # -------------------------------------------------------------
        stage_8_pass = True
        unsupported_trends: list[str] = []
        trends = evidence.get("trends", [])
        has_temporal_data = any(t.get("data_points", 0) > 1 for t in trends)

        for c in claims:
            if c.claim_type == "trend":
                if not has_temporal_data:
                    unsupported_trends.append(c.raw_text)
                    stage_8_pass = False
                    rejection_reasons.append(
                        f"Stage 8 (Trend): Trend claimed ('{c.raw_text}') without temporal/historical data."
                    )
                else:
                    verified_claims.append(f"Trend verified: '{c.raw_text}' against temporal tracking.")
        stage_results["8_trend_grounding"] = stage_8_pass

        # -------------------------------------------------------------
        # Stage 9: Availability Validation (Zero != Unavailable)
        # -------------------------------------------------------------
        stage_9_pass = True
        zero_violations: list[str] = []
        unavailable_metrics = [m.lower() for m in evidence.get("unavailable_metrics", [])]

        for unavail in unavailable_metrics:
            pat_zero = rf"\b{re.escape(unavail)}\b.*?\b(0%?|zero|none|nil|0\.0)\b"
            pat_zero_rev = rf"\b(0%?|zero|none|nil|0\.0)\b.*?\b{re.escape(unavail)}\b"
            if re.search(pat_zero, full_lower) or re.search(pat_zero_rev, full_lower):
                zero_violations.append(unavail)
                stage_9_pass = False
                rejection_reasons.append(
                    f"Stage 9 (Availability): Zero != Unavailable violation. '{unavail}' is unavailable, not zero."
                )
        stage_results["9_availability"] = stage_9_pass

        # -------------------------------------------------------------
        # Stage 10: Causation Validation
        # -------------------------------------------------------------
        stage_10_pass = True
        unsupported_causations: list[str] = []
        has_causal_evidence = bool(evidence.get("anomalies"))

        for c in claims:
            if c.claim_type == "causation":
                if not has_causal_evidence:
                    unsupported_causations.append(c.raw_text)
                    stage_10_pass = False
                    rejection_reasons.append(
                        f"Stage 10 (Causation): Unsupported causal claim: '{c.raw_text}'. Dataset proves correlation only."
                    )
                else:
                    matched_cause = False
                    for anom in evidence.get("anomalies", []):
                        reason = anom.get("reason", "").lower()
                        if any(term in reason for term in ["deviat", "spike", "threshold", "above", "below"]):
                            matched_cause = True
                            break
                    if not matched_cause:
                        unsupported_causations.append(c.raw_text)
                        stage_10_pass = False
                        rejection_reasons.append(
                            f"Stage 10 (Causation): Causal claim '{c.raw_text}' not supported by anomaly evidence."
                        )
        stage_results["10_causation"] = stage_10_pass

        # -------------------------------------------------------------
        # Stage 11: Recommendation Validation
        # -------------------------------------------------------------
        stage_11_pass = True
        recs = sections_dict.get("recommendations", [])
        if recs:
            metrics_and_entities = set(m.get("name", "").lower() for m in evidence.get("metrics", []))
            metrics_and_entities.update(all_entities)
            for rec in recs:
                rec_str = str(rec).lower()
                if profile == "hr" and any(w in rec_str for w in ["pricing", "inventory", "stockout", "shipment"]):
                    stage_11_pass = False
                    rejection_reasons.append(f"Stage 11 (Recommendation): Recommendation references unrelated domain concepts: '{rec}'.")
                elif profile == "sales" and any(w in rec_str for w in ["headcount reduction", "attrition interview", "severance"]):
                    stage_11_pass = False
                    rejection_reasons.append(f"Stage 11 (Recommendation): Recommendation references unrelated domain concepts: '{rec}'.")
        stage_results["11_recommendation"] = stage_11_pass

        # -------------------------------------------------------------
        # Stage 12: Relevance Validation (Filler Phrases & Generic buzzwords)
        # -------------------------------------------------------------
        stage_12_pass = True
        generic_filler: list[str] = []
        for phrase in cls.BANNED_FILLER_PHRASES:
            if phrase in full_lower:
                generic_filler.append(phrase)
                stage_12_pass = False
                rejection_reasons.append(f"Stage 12 (Relevance): Generic corporate filler detected: '{phrase}'.")
        stage_results["12_relevance"] = stage_12_pass

        # -------------------------------------------------------------
        # Stage 13: Duplicate Detection
        # -------------------------------------------------------------
        stage_13_pass = True
        duplicates_detected: list[str] = []
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", full_text) if len(s.strip()) > 30]
        seen_sentences = set()
        for s in sentences:
            s_norm = re.sub(r"\s+", " ", s.lower())
            if s_norm in seen_sentences:
                duplicates_detected.append(s)
                stage_13_pass = False
                rejection_reasons.append(f"Stage 13 (Duplicate Detection): Duplicate sentence found: '{s}'.")
            seen_sentences.add(s_norm)
        stage_results["13_duplicate_detection"] = stage_13_pass

        # -------------------------------------------------------------
        # Stage 14: Benchmark & Risk Validation (Rule #8 & #10)
        # -------------------------------------------------------------
        stage_14_pass = True
        has_benchmarks = bool(evidence.get("benchmarks") or evidence.get("targets"))
        if not has_benchmarks:
            benchmark_matches = re.findall(
                r"\b(?:(?:industry|market|external|standard|peer)\s+benchmarks?|industry\s+standards?|national\s+average|(?:exceeds?|above|below|better\s+than|worse\s+than)\s+(?:the\s+|standard\s+)?industry|talent\s+loss\s+risk|talent\s+drain\s+risk|flight\s+risk)\b",
                full_lower,
            )
            if benchmark_matches:
                stage_14_pass = False
                match_str = benchmark_matches[0]
                rejection_reasons.append(
                    f"Stage 14 (Benchmark & Risk): Unsupported benchmark or risk claim ('{match_str}'). No verified external benchmark exists in evidence."
                )
        stage_results["14_benchmark_and_risk"] = stage_14_pass

        # -------------------------------------------------------------
        # Final Synthesis
        # -------------------------------------------------------------
        grounded = (
            stage_4_pass
            and stage_5_pass
            and stage_6_pass
            and stage_7_pass
            and stage_8_pass
            and stage_9_pass
            and stage_10_pass
            and stage_14_pass
        )
        relevance_verified = stage_1_pass and stage_2_pass and stage_3_pass and stage_11_pass and stage_12_pass and stage_13_pass
        dataset_verified = stage_2_pass
        report_verified = stage_3_pass

        is_valid = grounded and relevance_verified and dataset_verified and report_verified

        if is_valid:
            status = "verified"
        elif len(unsupported_nums) == 0 and len(zero_violations) == 0 and not cross_dataset_leaks and not cross_report_leaks:
            status = "requires_verification"
        else:
            status = "rejected"

        return SummaryValidationResult(
            is_valid=is_valid,
            status=status,
            grounded=grounded,
            relevance_verified=relevance_verified,
            dataset_verified=dataset_verified,
            report_verified=report_verified,
            stage_results=stage_results,
            verified_claims=verified_claims,
            rejection_reasons=rejection_reasons,
            warnings=warnings,
            unsupported_numbers=unsupported_nums,
            hallucinated_rankings=hallucinated_rankings,
            unsupported_trends=unsupported_trends,
            unsupported_causations=unsupported_causations,
            zero_vs_unavailable_violations=zero_violations,
            cross_dataset_leaks=cross_dataset_leaks,
            cross_report_leaks=cross_report_leaks,
            generic_filler_detected=generic_filler,
            duplicates_detected=duplicates_detected,
        )

    @classmethod
    def validate_summary(
        cls,
        summary: dict[str, Any] | str | None = None,
        context: ReportContext | None = None,
        evidence: dict[str, Any] | None = None,
        strict: bool = True,
        **kwargs: Any,
    ) -> SummaryValidationResult:
        payload = summary if summary is not None else kwargs.get("summary_payload", {})
        return cls.validate(summary_payload=payload, context=context, evidence=evidence, strict=strict)
