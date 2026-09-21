"""Claim Extractor and Fingerprinter for AI Executive Summary Engine.

Implements Sections 2, 22, 28 of the Executive Summary Specification:
- Single-pass claim extraction from generated sentences
- Extracts numerical quantities, currency amounts, percentages, entities, comparisons, and benchmarks
- Computes canonical claim fingerprints: (metric, entity, value, scope)
- Detects cross-section duplicates between overview and sections
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class ExtractedClaimItem(BaseModel):
    """Represents a factual claim extracted from narrative text."""
    sentence: str
    section_id: str
    numbers: list[float] = Field(default_factory=list)
    percentages: list[float] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    contains_benchmark: bool = False
    contains_risk: bool = False
    contains_causation: bool = False
    contains_trend: bool = False
    fingerprint: str = ""


class ClaimExtractor:
    """Extracts claims and computes canonical fingerprints for duplicate prevention."""

    # Benchmark indicator patterns (Section 17)
    BENCHMARK_REGEX = re.compile(r"\b(industry (benchmark|average|standard)|competitors?|market rate)\b", re.IGNORECASE)

    # Risk indicator patterns (Section 18)
    RISK_REGEX = re.compile(r"\b(flight risk|talent risk|critical risk|severe operational risk|high risk)\b", re.IGNORECASE)

    # Unsupported causation patterns (Section 19)
    CAUSATION_REGEX = re.compile(r"\b(caused|causing|because of|due to|led to|drove the increase|resulted from)\b", re.IGNORECASE)

    # Trend patterns (Section 15)
    TREND_REGEX = re.compile(r"\b(increasing|decreasing|growing|declining|historical trend|revenue over time)\b", re.IGNORECASE)

    @classmethod
    def split_sentences(cls, text: str) -> list[str]:
        """Splits narrative into discrete sentences."""
        raw = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in raw if len(s.strip()) > 3]

    @classmethod
    def extract_numbers(cls, sentence: str) -> tuple[list[float], list[float]]:
        """Extracts standard numbers and percentages from sentence."""
        numbers: list[float] = []
        percentages: list[float] = []

        # Find percentages
        pct_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", sentence)
        for pm in pct_matches:
            try:
                percentages.append(float(pm))
            except ValueError:
                pass

        # Find currency and numbers with multipliers ($1.37M, $220K, 4,653)
        num_matches = re.finditer(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*([KkMmBb%])?", sentence)
        for m in num_matches:
            num_str = m.group(1).replace(",", "")
            mult = (m.group(2) or "").upper()
            try:
                val = float(num_str)
                if mult == "%":
                    continue  # already captured
                if mult == "K":
                    val *= 1_000
                elif mult == "M":
                    val *= 1_000_000
                elif mult == "B":
                    val *= 1_000_000_000
                numbers.append(val)
            except ValueError:
                pass

        return numbers, percentages

    @classmethod
    def compute_fingerprint(cls, sentence: str, numbers: list[float], entities: list[str]) -> str:
        """Computes deterministic fingerprint based on (entity, value) pairs (Section 22)."""
        rounded_nums = sorted([round(n, 2) for n in numbers])
        ent_str = "_".join(sorted([e.lower().strip() for e in entities]))
        num_str = "_".join([str(n) for n in rounded_nums])
        return f"fp:{ent_str}::{num_str}"

    @classmethod
    def extract_claims(
        cls,
        text: str,
        section_id: str,
        known_entities: list[str] | None = None,
    ) -> list[ExtractedClaimItem]:
        """Extracts all claims with indicators and fingerprints."""
        sentences = cls.split_sentences(text)
        claims: list[ExtractedClaimItem] = []
        entities_pool = known_entities or []

        for sent in sentences:
            numbers, percentages = cls.extract_numbers(sent)

            # Match entities
            matched_entities = []
            for ent in entities_pool:
                if re.search(rf"\b{re.escape(ent)}\b", sent, re.IGNORECASE):
                    matched_entities.append(ent)

            has_bench = bool(cls.BENCHMARK_REGEX.search(sent))
            has_risk = bool(cls.RISK_REGEX.search(sent))
            has_cause = bool(cls.CAUSATION_REGEX.search(sent))
            has_trend = bool(cls.TREND_REGEX.search(sent))

            fp = cls.compute_fingerprint(sent, numbers, matched_entities)

            claims.append(
                ExtractedClaimItem(
                    sentence=sent,
                    section_id=section_id,
                    numbers=numbers,
                    percentages=percentages,
                    entities=matched_entities,
                    contains_benchmark=has_bench,
                    contains_risk=has_risk,
                    contains_causation=has_cause,
                    contains_trend=has_trend,
                    fingerprint=fp,
                )
            )

        return claims
