"""Evidence Selector for Executive Summary Engine.

Implements Sections 2, 8, 9, 24 of the Executive Summary Specification:
- Filters and ranks evidence by composite score
- Selects the most important evidence without metric dumping
- Deduplicates evidence candidates and groups by semantic topic
"""
from __future__ import annotations

from typing import Any
from app.ai.evidence.evidence_builder import EvidenceItem
from app.ai.evidence.evidence_relevance import EvidenceRelevanceFilter
from app.ai.evidence.evidence_significance import EvidenceSignificanceAnalyzer


class EvidenceSelector:
    """Selects the most executive-relevant evidence items from raw candidate pool."""

    @classmethod
    def select_evidence(
        cls,
        evidence_items: list[EvidenceItem],
        report_type: str,
        report_title: str,
        domain: str,
        max_items: int = 15,
    ) -> list[tuple[EvidenceItem, dict[str, float]]]:
        """Selects top-ranked evidence with score breakdown."""
        # 1. Filter out irrelevant cross-report metrics
        relevant = EvidenceRelevanceFilter.filter_evidence(
            evidence_items=evidence_items,
            report_type=report_type,
            report_title=report_title,
            domain=domain,
            min_relevance=0.35,
        )

        # 2. Score significance and novelty
        scored: list[tuple[EvidenceItem, dict[str, float]]] = []
        seen_measures: set[str] = set()
        seen_entities: set[str] = set()

        for item, rel_score in relevant:
            scores = EvidenceSignificanceAnalyzer.score_item(
                item=item,
                relevance_score=rel_score,
                seen_measures=seen_measures,
                seen_entities=seen_entities,
            )
            scored.append((item, scores))

        # 3. Sort by composite score descending
        scored.sort(key=lambda x: x[1]["composite"], reverse=True)

        # 4. Cap at max_items to prevent executive overload
        return scored[:max_items]
