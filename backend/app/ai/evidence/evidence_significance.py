"""Evidence Significance and Novelty Analyzer for AI Executive Summary Engine.

Implements Sections 2, 8, 9, 24 of the Executive Summary Specification:
- Computes significance_score (0.0 to 1.0) and novelty_score (0.0 to 1.0)
- Prioritizes top metrics (#1 rankings, primary totals, notable differences)
- Suppresses repetitive middle rankings or low-value data points
"""
from __future__ import annotations

from typing import Any
from app.ai.evidence.evidence_builder import EvidenceItem


class EvidenceSignificanceAnalyzer:
    """Analyzes empirical significance, novelty, and executive impact of evidence items."""

    @classmethod
    def calculate_significance(cls, item: EvidenceItem) -> float:
        """Determines executive importance score (0.0 to 1.0)."""
        # Primary metrics or top ranking entity (#1) have highest significance
        if item.rank == 1:
            return 0.95
        if item.rank == 2:
            return 0.85
        if item.rank and item.rank > 3:
            return 0.40  # Lower significance for middle/tail ranks

        if item.metric_type == "limitation":
            return 0.88  # Clear limitations are significant for executive context

        if item.is_meaningful_trend:
            return 0.92  # Meaningful trends are high impact

        if item.evidence_id.startswith("comparison."):
            return 0.86  # Concrete comparative differences are significant

        # Primary totals / key rates
        if item.semantic_measure in ("revenue", "headcount", "profit", "attrition_rate", "quality_score"):
            return 0.94

        if item.semantic_measure in ("record_count", "column_count"):
            return 0.80

        return 0.70

    @classmethod
    def calculate_novelty(cls, item: EvidenceItem, seen_measures: set[str], seen_entities: set[str]) -> float:
        """Determines how much new information this evidence adds compared to prior items."""
        novelty = 1.0
        if item.semantic_measure in seen_measures:
            novelty -= 0.30  # Already introduced this measure
        if item.entity and item.entity in seen_entities:
            novelty -= 0.35  # Already discussed this entity
        return max(0.1, novelty)

    @classmethod
    def score_item(
        cls,
        item: EvidenceItem,
        relevance_score: float,
        seen_measures: set[str],
        seen_entities: set[str],
    ) -> dict[str, float]:
        """Calculates combined scoring dictionary matching Section 9."""
        sig = cls.calculate_significance(item)
        nov = cls.calculate_novelty(item, seen_measures, seen_entities)
        conf = float(item.confidence)

        # Update trackers
        seen_measures.add(item.semantic_measure)
        if item.entity:
            seen_entities.add(item.entity)

        return {
            "relevance": round(relevance_score, 2),
            "significance": round(sig, 2),
            "novelty": round(nov, 2),
            "confidence": round(conf, 2),
            "composite": round((relevance_score * 0.35) + (sig * 0.35) + (nov * 0.20) + (conf * 0.10), 2),
        }
