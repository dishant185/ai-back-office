"""Summary Deduplicator for Report-Aware Intelligence (Rule #37).

Removes duplicate facts, repeated limitations, identical recommendations,
and redundant empirical claims across report summaries.
"""
from __future__ import annotations

import re
from typing import Any


class SummaryDeduplicator:
    """Deduplicates facts, limitations, recommendations, and claims."""

    @staticmethod
    def _normalize(text: str) -> str:
        """Strip punctuation and extra whitespace for robust duplicate matching."""
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def deduplicate_list(cls, items: list[str]) -> list[str]:
        """Deduplicate a list of strings while preserving original order."""
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            if not item:
                continue
            norm = cls._normalize(str(item))
            if norm and norm not in seen:
                seen.add(norm)
                unique.append(item.strip() if isinstance(item, str) else item)
        return unique

    @classmethod
    def deduplicate_limitations(cls, limitations: list[str]) -> list[str]:
        """Deduplicate limitations (e.g. 'Average Domain Experience unavailable' appears twice -> once)."""
        seen: set[str] = set()
        deduped: list[str] = []
        for lim in limitations:
            if not lim or not isinstance(lim, str):
                continue
            # Normalize core metric name extracted from limitation
            norm = cls._normalize(lim)
            # Check for near-identical statements (e.g. 'X is unavailable' vs 'X could not be evaluated')
            key_metric_match = re.search(r"^([a-z\s]+?)(?:is unavailable|could not be evaluated|was not found)", norm)
            key = key_metric_match.group(1).strip() if key_metric_match else norm
            if key not in seen:
                seen.add(key)
                deduped.append(lim.strip())
        return deduped

    @classmethod
    def deduplicate_recommendations(cls, recommendations: list[str]) -> list[str]:
        """Deduplicate recommendations while preserving order."""
        return cls.deduplicate_list(recommendations)

    @classmethod
    def deduplicate_facts(cls, facts: list[str]) -> list[str]:
        """Deduplicate repeated facts / key findings."""
        return cls.deduplicate_list(facts)

    @classmethod
    def deduplicate_claims(cls, claims: list[str]) -> list[str]:
        """Deduplicate claims or sentences in text blocks."""
        return cls.deduplicate_list(claims)

    @classmethod
    def deduplicate_sections(cls, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate sentences across dynamic sections and remove duplicate sections."""
        seen_sentences: set[str] = set()
        deduped_sections: list[dict[str, Any]] = []
        seen_section_contents: set[str] = set()

        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                continue
            content = sec.get("content", "")
            norm_content = cls._normalize(content)
            if not norm_content or norm_content in seen_section_contents:
                continue

            # Check individual sentences inside section
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
            unique_sentences: list[str] = []
            for s in sentences:
                norm_s = cls._normalize(s)
                if len(norm_s) > 15 and norm_s in seen_sentences:
                    continue
                unique_sentences.append(s)
                if len(norm_s) > 15:
                    seen_sentences.add(norm_s)

            filtered_content = " ".join(unique_sentences).strip()
            if not filtered_content:
                # If subsequent section has all sentences redundant, skip it
                continue

            updated_sec = dict(sec)
            updated_sec["content"] = filtered_content
            seen_section_contents.add(cls._normalize(filtered_content))
            deduped_sections.append(updated_sec)

        return deduped_sections

    @classmethod
    def deduplicate_summary(cls, summary: dict[str, Any]) -> dict[str, Any]:
        """Runs deduplication across all structured sections of a summary."""
        cleaned = dict(summary)
        if "sections" in cleaned and isinstance(cleaned["sections"], list):
            cleaned["sections"] = cls.deduplicate_sections(cleaned["sections"])
        if "key_findings" in cleaned and isinstance(cleaned["key_findings"], list):
            cleaned["key_findings"] = cls.deduplicate_facts(cleaned["key_findings"])
        if "limitations" in cleaned and isinstance(cleaned["limitations"], list):
            cleaned["limitations"] = cls.deduplicate_limitations(cleaned["limitations"])
        if "recommendations" in cleaned and isinstance(cleaned["recommendations"], list):
            cleaned["recommendations"] = cls.deduplicate_recommendations(cleaned["recommendations"])
        if "important_patterns" in cleaned and isinstance(cleaned["important_patterns"], list):
            cleaned["important_patterns"] = cls.deduplicate_list(cleaned["important_patterns"])
        if "patterns" in cleaned and isinstance(cleaned["patterns"], list):
            cleaned["patterns"] = cls.deduplicate_list(cleaned["patterns"])
        if "business_implications" in cleaned and isinstance(cleaned["business_implications"], list):
            cleaned["business_implications"] = cls.deduplicate_list(cleaned["business_implications"])
        if "comparisons" in cleaned and isinstance(cleaned["comparisons"], list):
            cleaned["comparisons"] = cls.deduplicate_list(cleaned["comparisons"])
        if "trends" in cleaned and isinstance(cleaned["trends"], list):
            cleaned["trends"] = cls.deduplicate_list(cleaned["trends"])
        return cleaned
