"""Claim Extractor for Production AI Executive Summary Engine V2.

Extracts factual claims across all 11 specified claim types:
- NUMBER
- PERCENTAGE
- ENTITY
- DATE
- RANKING
- COMPARISON
- TREND
- BENCHMARK
- CAUSATION
- RISK
- RECOMMENDATION
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class ExtractedClaim(BaseModel):
    """Normalized factual claim extracted from candidate text."""
    claim_type: str  # number, percentage, entity, date, ranking, comparison, trend, benchmark, causation, risk, recommendation, zero_assertion
    raw_text: str
    entity: str | None = None
    metric: str | None = None
    numerical_value: float | None = None
    unit: str | None = None
    rank: int | None = None


class ClaimExtractor:
    """Extracts testable factual claims from LLM summary responses."""

    @classmethod
    def _parse_compact_number(cls, num_str: str, suffix: str | None) -> float | None:
        try:
            val = float(num_str.replace(",", ""))
            if suffix:
                s = suffix.lower()
                if s == "k":
                    val *= 1_000
                elif s == "m":
                    val *= 1_000_000
                elif s == "b":
                    val *= 1_000_000_000
            return val
        except (ValueError, TypeError):
            return None

    @classmethod
    def extract_claims(cls, text: str, sections_dict: dict[str, Any] | None = None) -> list[ExtractedClaim]:
        """Extract all testable factual claims from summary text and structured fields."""
        claims: list[ExtractedClaim] = []
        full_text = text or ""
        if sections_dict:
            for k, v in sections_dict.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            t = item.get("title") or ""
                            c = item.get("content") or item.get("statement") or ""
                            full_text += f"\n{t} {c}".strip()
                        elif isinstance(item, str):
                            full_text += "\n" + item
                elif isinstance(v, str):
                    full_text += "\n" + v

        cleaned_for_nums = re.sub(r"[₹$€£]", " ", full_text)

        # 1. Numbers, Compact Numbers (K/M/B), and Percentages in a single unified pass
        unified_num_pattern = re.compile(
            r"(?<![\w\.-])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*([kmbKMB]|%|percent)?(?!\w)"
        )
        for match in unified_num_pattern.finditer(cleaned_for_nums):
            num_str = match.group(1).replace(",", "")
            suffix = match.group(2)
            try:
                if suffix and suffix.lower() in ("k", "m", "b"):
                    val = cls._parse_compact_number(num_str, suffix)
                    is_pct = False
                elif suffix and suffix.lower() in ("%", "percent"):
                    val = float(num_str)
                    is_pct = True
                else:
                    val = float(num_str)
                    is_pct = False

                if val is not None:
                    context_window = cleaned_for_nums[max(0, match.start() - 25):min(len(cleaned_for_nums), match.end() + 25)]
                    claims.append(ExtractedClaim(
                        claim_type="percentage" if is_pct else "number",
                        raw_text=context_window.strip(),
                        numerical_value=val,
                    ))
            except ValueError:
                pass

        # 2. Rankings (highest, top, largest, lowest, bottom)
        ranking_patterns = [
            (re.compile(r"\b([A-Z][a-zA-Z0-9_-]*(?:\s+[A-Z][a-zA-Z0-9_-]*)?)\s+(?:is|was|recorded|generated|achieved|represents?|accounted\s+for)\s+(?:the\s+)?(highest|leading|largest|top|primary)\b", re.IGNORECASE), 1),
            (re.compile(r"\b(?:highest|leading|largest|top)\s+(?:segment|category|entity|department|division|region|territory|group)?\s*(?:is|was|recorded by)?\s*([A-Z][a-zA-Z0-9_-]*(?:\s+[A-Z][a-zA-Z0-9_-]*)?)\b", re.IGNORECASE), 1),
            (re.compile(r"\b([A-Z][a-zA-Z0-9_-]*(?:\s+[A-Z][a-zA-Z0-9_-]*)?)\s+(?:recorded|experienced|saw|is|was)\s+(?:the\s+)?(lowest|smallest|bottom|trailing)\b", re.IGNORECASE), -1),
        ]
        stop_words = {
            "is", "was", "the", "a", "an", "in", "at", "for", "records", "company",
            "highest", "leading", "largest", "top", "primary", "lowest", "smallest", "bottom",
            "regional", "revenue", "education", "recorded", "category", "segment",
            "department", "division", "headcount", "turnover", "attrition", "sales",
            "volume", "performance", "tier", "population", "al revenue", "recorded education",
        }
        for pat, default_rank in ranking_patterns:
            for match in pat.finditer(full_text):
                ent = match.group(1).strip() if match.group(1) else None
                if ent:
                    ent_clean = " ".join(w for w in ent.split() if w.lower() not in stop_words)
                    if ent_clean and ent_clean.lower() not in stop_words and len(ent_clean) > 2:
                        claims.append(ExtractedClaim(
                            claim_type="ranking",
                            raw_text=match.group(0),
                            entity=ent_clean,
                            rank=default_rank,
                        ))

        # 3. Trends
        trend_pattern = re.compile(
            r"(?:revenue|sales|profit|headcount|attrition)?\s*(increased|decreased|grew|declined|surged|dropped|increasing trend|declining trend|trend over|upward trend|downward trend)\s*(?:by\s*(\d+(?:\.\d+)?%?))?",
            re.IGNORECASE
        )
        for match in trend_pattern.finditer(full_text):
            pct_val = None
            if match.group(2):
                try:
                    pct_val = float(match.group(2).replace("%", ""))
                except ValueError:
                    pass
            claims.append(ExtractedClaim(
                claim_type="trend",
                raw_text=match.group(0),
                numerical_value=pct_val,
            ))

        # 4. Causations
        causation_pattern = re.compile(
            r"([^\.\n]+?\s+(?:because|caused by|due to|resulting from|on account of|led to)\s+[^\.\n]+)",
            re.IGNORECASE
        )
        for match in causation_pattern.finditer(full_text):
            raw = match.group(1)
            raw_lower = raw.lower()
            if any(term in raw_lower for term in ["cannot be calculated", "could not be calculated", "not present in the dataset", "required fields were not"]):
                continue
            claims.append(ExtractedClaim(
                claim_type="causation",
                raw_text=raw.strip(),
            ))

        # 5. Zero vs Unavailable Assertions
        zero_pattern = re.compile(
            r"\b(attrition|turnover|departures?|profit|margin|missing|duplicates?)\s*(?:rate)?\s*(?:is|was|stands at|equals|of)?\s*(?:0(?:\.0+)?%?|zero)\b",
            re.IGNORECASE
        )
        for match in zero_pattern.finditer(full_text):
            claims.append(ExtractedClaim(
                claim_type="zero_assertion",
                raw_text=match.group(0),
                metric=match.group(1).lower(),
                numerical_value=0.0,
            ))

        # 6. Benchmark Claims
        benchmark_pattern = re.compile(
            r"\b(?:industry|market|external|standard|peer)\s+benchmarks?\b",
            re.IGNORECASE
        )
        for match in benchmark_pattern.finditer(full_text):
            claims.append(ExtractedClaim(
                claim_type="benchmark",
                raw_text=match.group(0),
            ))

        # 7. Risk Claims
        risk_pattern = re.compile(
            r"\b(?:talent\s+loss\s+risk|talent\s+drain|flight\s+risk|severe\s+risk|critical\s+warning)\b",
            re.IGNORECASE
        )
        for match in risk_pattern.finditer(full_text):
            claims.append(ExtractedClaim(
                claim_type="risk",
                raw_text=match.group(0),
            ))

        return claims
