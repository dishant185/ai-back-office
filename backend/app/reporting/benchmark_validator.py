"""Benchmark Validator for Production AI Executive Summary Engine V2.

Distinguishes:
- OBSERVED_VALUE
- VERIFIED_INTERNAL_BENCHMARK
- VERIFIED_EXTERNAL_BENCHMARK
- NO_BENCHMARK

Strictly prohibits claiming comparisons to industry averages or external benchmarks
unless authoritative benchmark evidence is present in the report payload.
"""
from __future__ import annotations

from enum import Enum
import re
from typing import Any
from pydantic import BaseModel, Field


class BenchmarkCategory(str, Enum):
    OBSERVED_VALUE = "OBSERVED_VALUE"
    VERIFIED_INTERNAL_BENCHMARK = "VERIFIED_INTERNAL_BENCHMARK"
    VERIFIED_EXTERNAL_BENCHMARK = "VERIFIED_EXTERNAL_BENCHMARK"
    NO_BENCHMARK = "NO_BENCHMARK"


class BenchmarkValidationResult(BaseModel):
    is_valid: bool = True
    benchmark_status: BenchmarkCategory = BenchmarkCategory.NO_BENCHMARK
    violations: list[str] = Field(default_factory=list)


class BenchmarkValidator:
    """Validates that benchmark claims are grounded in verified benchmark evidence."""

    UNSUPPORTED_BENCHMARK_PATTERNS = [
        re.compile(r"\b(?:industry|market|external|standard|peer)\s+benchmarks?\b", re.IGNORECASE),
        re.compile(r"\b(?:industry|market|peer)\s+standards?\b", re.IGNORECASE),
        re.compile(r"\b(?:industry|market|national)\s+averages?\b", re.IGNORECASE),
        re.compile(r"\b(?:exceeds?|above|below|better\s+than|worse\s+than)\s+(?:the\s+|standard\s+)?industry\b", re.IGNORECASE),
        re.compile(r"\bstandard\s+industry\s+benchmarks?\b", re.IGNORECASE),
        re.compile(r"\boutperformed\s+peers\b", re.IGNORECASE),
        re.compile(r"\bmarket\s+norm\b", re.IGNORECASE),
    ]

    @classmethod
    def determine_benchmark_status(cls, evidence: dict[str, Any]) -> BenchmarkCategory:
        if evidence.get("external_benchmarks"):
            return BenchmarkCategory.VERIFIED_EXTERNAL_BENCHMARK
        if evidence.get("internal_benchmarks") or evidence.get("targets"):
            return BenchmarkCategory.VERIFIED_INTERNAL_BENCHMARK
        return BenchmarkCategory.NO_BENCHMARK

    @classmethod
    def validate_benchmarks(
        cls,
        summary_text: str,
        evidence: dict[str, Any],
    ) -> BenchmarkValidationResult:
        status = cls.determine_benchmark_status(evidence)
        result = BenchmarkValidationResult(benchmark_status=status)

        # If no verified external benchmarks, prohibit external benchmark claims
        if status in (BenchmarkCategory.NO_BENCHMARK, BenchmarkCategory.VERIFIED_INTERNAL_BENCHMARK):
            for pat in cls.UNSUPPORTED_BENCHMARK_PATTERNS:
                match = pat.search(summary_text)
                if match:
                    # Check if it's explicitly stating that NO benchmark is available (which is allowed)
                    context_snippet = summary_text[max(0, match.start() - 30):min(len(summary_text), match.end() + 30)].lower()
                    if any(neg in context_snippet for neg in ["no external benchmark", "no benchmark", "cannot be established", "not included"]):
                        continue
                    result.is_valid = False
                    result.violations.append(
                        f"Unsupported Benchmark: Claimed comparison '{match.group(0)}' without verified external benchmark data in evidence."
                    )

        # If no verified targets exist, prohibit target-based language (Bug 3)
        has_targets = bool(evidence.get("targets"))
        if not has_targets:
            for pat in [
                re.compile(r"\b(?:against|above|below|versus|vs\.?)\s+(?:the\s+)?targets?\b", re.IGNORECASE),
                re.compile(r"\btarget\s+(?:achievement|variance|value|benchmark)\b", re.IGNORECASE),
                re.compile(r"\bagainst\s+targets?\b", re.IGNORECASE),
            ]:
                match = pat.search(summary_text)
                if match:
                    result.is_valid = False
                    result.violations.append(
                        f"Unsupported Target: Claimed '{match.group(0)}' without verified target evidence."
                    )

        return result

    @classmethod
    def validate_text(cls, text: str, has_benchmark_data: bool = False) -> BenchmarkValidationResult:
        ev = {"external_benchmarks": ["verified_benchmark"]} if has_benchmark_data else {}
        return cls.validate_benchmarks(text, ev)

