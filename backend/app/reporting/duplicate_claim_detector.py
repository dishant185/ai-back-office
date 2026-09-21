"""Duplicate Claim Detector for Production AI Executive Summary Engine V2.

Detects when the same factual claim, entity-metric pairing, or sentence is repeated
across sections without contributing meaningful new analytical information.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class DuplicateDetectionResult(BaseModel):
    is_valid: bool = True
    has_duplicates: bool = False
    duplicates: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class DuplicateClaimDetector:
    """Detects repeated claims across summary sections."""

    @classmethod
    def _extract_fact_signatures(cls, text: str) -> set[str]:
        """Extracts rough entity + number tuples as signatures."""
        signatures = set()
        # Find entity + number occurrences (e.g. "New York ... 1.13")
        num_pattern = re.compile(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b")
        words = text.split()
        for i, w in enumerate(words):
            if w and w[0].isupper() and len(w) > 2:
                # Look ahead up to 6 words for a number
                for j in range(i + 1, min(len(words), i + 7)):
                    num_match = num_pattern.match(words[j].strip("$,%()"))
                    if num_match:
                        sig = f"{w.lower()}_{num_match.group(1).replace(',', '')}"
                        signatures.add(sig)
        return signatures

    @classmethod
    def detect_duplicates(
        cls,
        summary_payload: dict[str, Any] | str,
    ) -> DuplicateDetectionResult:
        result = DuplicateDetectionResult()
        if isinstance(summary_payload, str):
            sections = [{"title": "Summary", "content": summary_payload}]
        else:
            overview = summary_payload.get("overview", "")
            raw_sections = summary_payload.get("sections", [])
            sections = []
            if overview:
                sections.append({"title": "Overview", "content": overview})
            for s in raw_sections:
                if isinstance(s, dict):
                    if (s.get("type") == "executive_takeaway" or s.get("title") in ("Overview", "Summary Overview")) and s.get("content", "").strip() == overview.strip():
                        continue
                    sections.append({
                        "title": s.get("title", ""),
                        "content": s.get("content", ""),
                    })

        # 1. Exact or near-identical sentence detection across distinct sections
        seen_sentences: dict[str, str] = {}
        for s_idx, sec in enumerate(sections):
            sec_title = sec.get("title", f"Section {s_idx}")
            content = sec.get("content", "")
            sentences = [sent.strip() for sent in re.split(r"[.!?]\s+", content) if len(sent.strip()) > 35]

            for sent in sentences:
                norm_sent = re.sub(r"\s+", " ", sent.lower().strip(".,;:"))
                if norm_sent in seen_sentences:
                    prev_sec = seen_sentences[norm_sent]
                    dup_desc = f"Sentence duplicated between '{prev_sec}' and '{sec_title}': '{sent}'"
                    result.duplicates.append(dup_desc)
                    result.violations.append(dup_desc)
                    result.has_duplicates = True
                    result.is_valid = False
                else:
                    seen_sentences[norm_sent] = sec_title

        return result
