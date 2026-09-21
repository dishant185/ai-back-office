"""AI Evidence Planner (Stage A) for Production AI Executive Summary Engine V2.

Determines:
- Which evidence deserves attention
- Which evidence should be omitted (redundant or irrelevant)
- Which comparisons are meaningful
- Whether a trend is meaningful
- Whether recommendations are justified
- Limitations

NON-NEGOTIABLE PRINCIPLE:
The planner is NOT allowed to calculate new authoritative numbers.
It only selects/interprets evidence already supplied.
It must NOT invent evidence IDs.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from pydantic import BaseModel, Field

from app.ai.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class SelectedEvidenceItem(BaseModel):
    evidence_id: str
    importance: str = "high"  # "high", "medium", "low"
    reason: str


class OmittedEvidenceItem(BaseModel):
    evidence_id: str
    reason: str = "redundant_or_irrelevant"


class EvidencePlanResult(BaseModel):
    selected_evidence: list[SelectedEvidenceItem] = Field(default_factory=list)
    omitted_evidence: list[OmittedEvidenceItem] = Field(default_factory=list)
    meaningful_comparisons: list[Any] = Field(default_factory=list)
    meaningful_trends: list[Any] = Field(default_factory=list)
    supported_implications: list[str] = Field(default_factory=list)
    supported_actions: list[Any] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


def deterministic_evidence_planner(
    dataset_context: dict[str, Any],
    report_context: dict[str, Any],
    verified_evidence: dict[str, Any],
) -> EvidencePlanResult:
    """Deterministic Stage A planner ensuring zero-failure, strictly grounded evidence selection."""
    valid_ids: set[str] = set(verified_evidence.get("all_evidence_ids", []))
    metrics = verified_evidence.get("metrics", verified_evidence.get("verified_metrics", []))
    rankings = verified_evidence.get("rankings", verified_evidence.get("verified_rankings", []))
    comparisons = verified_evidence.get("comparisons", verified_evidence.get("verified_comparisons", []))
    trends = verified_evidence.get("trends", verified_evidence.get("verified_trends", []))
    recs = verified_evidence.get("recommendations", [])
    limitations = list(verified_evidence.get("limitations", []))

    selected: list[SelectedEvidenceItem] = []
    omitted: list[OmittedEvidenceItem] = []

    # 1. Select primary metrics (up to 5 most salient metrics)
    for idx, m in enumerate(metrics):
        ev_id = m.get("id") or m.get("evidence_id")
        if not ev_id or ev_id not in valid_ids:
            continue
        val = m.get("value")
        if val is None or str(val).lower() in ("unavailable", "none", "null", "nan"):
            omitted.append(OmittedEvidenceItem(evidence_id=ev_id, reason="metric_value_unavailable"))
            continue

        importance = "high" if idx < 3 else "medium"
        selected.append(SelectedEvidenceItem(
            evidence_id=ev_id,
            importance=importance,
            reason=f"Authoritative metric: {m.get('name', 'Metric')} = {m.get('formatted_value', val)}"
        ))

    # 2. Select rankings
    for rk in rankings:
        rk_id = rk.get("id") or rk.get("evidence_id")
        if rk_id and rk_id in valid_ids:
            top = rk.get("top_entity")
            if top:
                selected.append(SelectedEvidenceItem(
                    evidence_id=rk_id,
                    importance="high",
                    reason=f"Dominant entity in {rk.get('title', 'ranking')}: {top.get('entity')}"
                ))

    # 3. Meaningful comparisons (require at least 2 distinct entities with values)
    meaningful_cmps = []
    for cmp in comparisons:
        cmp_id = cmp.get("id") or cmp.get("evidence_id")
        if cmp_id and cmp_id in valid_ids:
            top_v = cmp.get("top_value")
            bot_v = cmp.get("bottom_value")
            if top_v and bot_v and top_v != bot_v:
                meaningful_cmps.append(cmp)
                selected.append(SelectedEvidenceItem(
                    evidence_id=cmp_id,
                    importance="medium",
                    reason=f"Meaningful variance between {cmp.get('top_entity')} and {cmp.get('bottom_entity')}"
                ))
            else:
                omitted.append(OmittedEvidenceItem(evidence_id=cmp_id, reason="no_meaningful_difference"))

    # 4. Meaningful trends (require >= 2 chronological data points)
    meaningful_tr = []
    for tr in trends:
        tr_id = tr.get("id") or tr.get("evidence_id")
        data_pts = tr.get("data_points", 0)
        if data_pts >= 2:
            meaningful_tr.append(tr)
            if tr_id and tr_id in valid_ids:
                selected.append(SelectedEvidenceItem(
                    evidence_id=tr_id,
                    importance="medium",
                    reason=f"Chronological trajectory with {data_pts} intervals"
                ))
        else:
            if tr_id and tr_id in valid_ids:
                omitted.append(OmittedEvidenceItem(evidence_id=tr_id, reason="insufficient_temporal_data_points"))

    # 5. Supported actions (strictly from verified recommendations)
    supported_acts = []
    for r in recs:
        r_id = r.get("id") or r.get("evidence_id")
        if r_id and r_id in valid_ids:
            supported_acts.append(r)
            selected.append(SelectedEvidenceItem(
                evidence_id=r_id,
                importance="medium",
                reason=f"Grounded recommendation: {r.get('title')}"
            ))

    return EvidencePlanResult(
        selected_evidence=selected,
        omitted_evidence=omitted,
        meaningful_comparisons=meaningful_cmps,
        meaningful_trends=meaningful_tr,
        supported_implications=[],
        supported_actions=supported_acts,
        limitations=limitations,
    )


async def plan_summary_evidence(
    dataset_context: dict[str, Any],
    report_context: dict[str, Any],
    verified_evidence: dict[str, Any],
    llm_client: LLMProvider | None = None,
) -> EvidencePlanResult:
    """Stage A: Plans evidence selection and importance prior to narrative generation."""
    valid_ids: set[str] = set(verified_evidence.get("all_evidence_ids", []))
    deterministic_plan = deterministic_evidence_planner(dataset_context, report_context, verified_evidence)

    if not llm_client:
        return deterministic_plan

    # Try LLM Stage A planning with strict schema
    try:
        available_ids_summary = [
            {
                "id": ev_id,
                "type": item.get("semantic_measure") or item.get("dimension") or "metric",
                "name": item.get("name") or item.get("title") or item.get("label") or ev_id,
                "value": item.get("formatted_value") or item.get("value"),
            }
            for ev_id, item in verified_evidence.get("evidence_id_map", {}).items()
            if not ev_id.startswith("metric_") and not ev_id.startswith("ranking_")  # pass clean dot IDs
        ][:30]

        prompt = f"""You are the AI Evidence Planner for an enterprise analytics platform.
Review the following verified evidence for report '{report_context.get("title")}' ({report_context.get("type")}):

Available Evidence Items:
{json.dumps(available_ids_summary, indent=2)}

Select which evidence items should be highlighted (selected_evidence) and which omitted (omitted_evidence).
Identify meaningful comparisons and trends.

CRITICAL RULES:
1. ONLY use evidence IDs from the Available Evidence Items list. NEVER invent IDs.
2. NEVER calculate or output new authoritative numbers.
3. Respond ONLY with a valid JSON object matching the schema.

Schema:
{{
  "selected_evidence": [{{"evidence_id": "string", "importance": "high"|"medium"|"low", "reason": "string"}}],
  "omitted_evidence": [{{"evidence_id": "string", "reason": "string"}}],
  "meaningful_comparisons": [],
  "meaningful_trends": [],
  "supported_implications": [],
  "supported_actions": [],
  "limitations": []
}}
"""
        response_text = await llm_client.generate_text(
            prompt=prompt,
            system_prompt="You are an AI Evidence Planner. Return valid JSON only. Never invent evidence IDs.",
            temperature=0.1,
        )

        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        data = json.loads(clean_json)

        # Validate that no IDs were invented
        sanitized_selected: list[SelectedEvidenceItem] = []
        for item in data.get("selected_evidence", []):
            eid = item.get("evidence_id")
            if eid in valid_ids:
                sanitized_selected.append(SelectedEvidenceItem(
                    evidence_id=eid,
                    importance=item.get("importance", "medium"),
                    reason=item.get("reason", "Selected by planner")
                ))

        sanitized_omitted: list[OmittedEvidenceItem] = []
        for item in data.get("omitted_evidence", []):
            eid = item.get("evidence_id")
            if eid in valid_ids:
                sanitized_omitted.append(OmittedEvidenceItem(
                    evidence_id=eid,
                    reason=item.get("reason", "Omitted by planner")
                ))

        if sanitized_selected:
            return EvidencePlanResult(
                selected_evidence=sanitized_selected,
                omitted_evidence=sanitized_omitted,
                meaningful_comparisons=data.get("meaningful_comparisons", deterministic_plan.meaningful_comparisons),
                meaningful_trends=data.get("meaningful_trends", deterministic_plan.meaningful_trends),
                supported_implications=data.get("supported_implications", []),
                supported_actions=data.get("supported_actions", deterministic_plan.supported_actions),
                limitations=data.get("limitations", deterministic_plan.limitations),
            )
    except Exception as e:
        logger.warning(f"LLM evidence planning failed, using deterministic plan: {e}")

    return deterministic_plan
