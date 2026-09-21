"""Executive Summary Planner for Dynamic Section Selection.

Implements Sections 4, 8, 9 of the Executive Summary Specification:
- Groups verified evidence into cohesive candidate topics
- Assigns relevance, significance, novelty, and confidence scores to each potential section
- Excludes low-value or low-novelty sections (include = False)
- Ensures dynamic section count: 1, 2, 3, 4 or more based solely on available evidence
"""
from __future__ import annotations

import logging
from typing import Any
from app.ai.evidence.evidence_builder import EvidenceItem
from app.ai.summary.evidence_selector import EvidenceSelector
from app.ai.summary.summary_schema import EvidencePlanItem

logger = logging.getLogger(__name__)


class ExecutiveSummaryPlanner:
    """Plans dynamic summary sections based on empirical evidence scores."""

    @classmethod
    def plan_sections(
        cls,
        evidence_items: list[EvidenceItem],
        report_type: str,
        report_title: str,
        domain: str,
    ) -> list[EvidencePlanItem]:
        """Evaluates potential sections and produces an evidence plan."""
        # 1. Select and score candidate evidence items
        selected = EvidenceSelector.select_evidence(
            evidence_items=evidence_items,
            report_type=report_type,
            report_title=report_title,
            domain=domain,
            max_items=20,
        )

        # 2. Cluster evidence items into candidate topics
        topic_groups: dict[str, list[tuple[EvidenceItem, dict[str, float]]]] = {}
        for item, scores in selected:
            # Topic key derived from dimension or primary semantic measure
            if item.evidence_id.startswith("ranking."):
                parts = item.evidence_id.split(".")
                topic = f"{parts[1]}_{parts[2]}"
            elif item.evidence_id.startswith("comparison."):
                parts = item.evidence_id.split(".")
                topic = f"comparison_{parts[1]}"
            elif item.evidence_id.startswith("trend."):
                topic = "temporal_trend"
            elif item.metric_type == "limitation":
                topic = "scope_limitations"
            else:
                topic = item.semantic_measure

            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append((item, scores))

        # 3. Score each potential section
        planned_sections: list[EvidencePlanItem] = []
        for topic, group in topic_groups.items():
            ev_ids = [item.evidence_id for item, _ in group]
            avg_rel = sum(scores["relevance"] for _, scores in group) / len(group)
            avg_sig = sum(scores["significance"] for _, scores in group) / len(group)
            avg_nov = sum(scores["novelty"] for _, scores in group) / len(group)
            avg_conf = sum(scores["confidence"] for _, scores in group) / len(group)

            # Formulate clean, natural section title
            title = cls._generate_section_title(topic, group[0][0])

            # Decide include: True only if composite score meets executive threshold
            composite = (avg_rel * 0.35) + (avg_sig * 0.35) + (avg_nov * 0.20) + (avg_conf * 0.10)
            should_include = composite >= 0.55 and len(group) >= 1

            # Trend section safeguard (Section 15): ONLY include trend if meaningful
            if topic == "temporal_trend":
                has_meaningful_trend = any(item.is_meaningful_trend for item, _ in group)
                if not has_meaningful_trend:
                    should_include = False

            planned_sections.append(
                EvidencePlanItem(
                    topic=topic,
                    title=title,
                    relevance=round(avg_rel, 2),
                    significance=round(avg_sig, 2),
                    novelty=round(avg_nov, 2),
                    confidence=round(avg_conf, 2),
                    include=should_include,
                    evidence_ids=ev_ids,
                )
            )

        # Sort sections by relevance and significance
        planned_sections.sort(key=lambda s: (s.relevance + s.significance), reverse=True)
        return planned_sections

    @classmethod
    def _generate_section_title(cls, topic: str, sample_item: EvidenceItem) -> str:
        """Generates dynamic, human-readable section title from topic and evidence."""
        clean_topic = topic.replace("_", " ").title()

        if sample_item.entity:
            if "ranking" in sample_item.evidence_id:
                dim_name = sample_item.evidence_id.split(".")[1].replace("_", " ").title()
                meas_name = sample_item.semantic_measure.replace("_", " ").title()
                return f"{dim_name} {meas_name} Distribution"
            if "comparison" in sample_item.evidence_id:
                return f"{sample_item.entity} Comparative Analysis"

        if sample_item.is_meaningful_trend:
            return f"{sample_item.semantic_measure.replace('_', ' ').title()} Observed Trend"

        if sample_item.metric_type == "limitation":
            return "Evaluated Scope & Data Limitations"

        return clean_topic
