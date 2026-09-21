"""Summary Context Builder for Dynamic Report Intelligence (Phase 6.8).

Transforms DatasetContext, ReportContext, and ReportEvidence into a clean,
authoritative LLMContext that feeds the universal LLM prompt.
Includes unique evidence_ids for claim-level citation and grounding validation.
"""
from __future__ import annotations

from typing import Any
from app.reporting.report_context import ReportContext


class SummaryContextBuilder:
    """Builds the compact authoritative LLMContext from verified report evidence."""

    @classmethod
    def build_llm_context(
        cls,
        context: ReportContext,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Constructs strictly scoped dynamic LLMContext with evidence_ids."""
        # 1. Dataset metadata (compact, no raw rows)
        dataset_block = {
            "id": context.dataset_id,
            "name": context.dataset_name,
            "version": context.dataset_version,
            "domain": context.dataset_profile,
            "row_count": evidence.get("row_count", 0),
            "column_count": evidence.get("column_count", 0),
        }

        # 2. Report metadata (dynamic)
        report_block = {
            "id": context.report_id,
            "type": context.report_type,
            "title": context.report_title,
            "purpose": context.report_purpose,
            "filters": context.filters,
            "date_range": context.date_range,
        }

        # 3. Verified Metrics (with evidence_id)
        verified_metrics = [
            {
                "evidence_id": m.get("evidence_id", f"metric_{m.get('id') or m.get('metric') or m.get('name', 'metric')}"),
                "metric": m.get("name") or m.get("metric", "Metric"),
                "value": m.get("formatted_value", str(m.get("value", ""))),
            }
            for m in evidence.get("metrics", [])
        ]

        # 4. Verified Rankings (with evidence_id)
        verified_rankings = []
        for rk in evidence.get("rankings", []):
            top = rk.get("top_entity")
            bot = rk.get("bottom_entity")
            verified_rankings.append({
                "evidence_id": rk.get("evidence_id", f"ranking_{rk.get('dimension', 'dim')}"),
                "title": rk.get("title"),
                "top_entity": f"{top['entity']} ({top['formatted_value']})" if top else "None",
                "bottom_entity": f"{bot['entity']} ({bot['formatted_value']})" if bot else "None",
                "total_items": len(rk.get("items", [])),
            })

        # 5. Verified Comparisons (with evidence_id)
        verified_comparisons = []
        for idx, c in enumerate(evidence.get("comparisons", [])):
            dim = c.get("dimension")
            top_raw = str(c.get("top_entity", "")).strip()
            bot_raw = str(c.get("bottom_entity", "")).strip()
            top_lbl = f"{dim.title()} {top_raw}" if (dim and top_raw.isdigit()) else (f"Item {top_raw}" if top_raw.isdigit() else top_raw)
            bot_lbl = f"{dim.title()} {bot_raw}" if (dim and bot_raw.isdigit()) else (f"Item {bot_raw}" if bot_raw.isdigit() else bot_raw)
            verified_comparisons.append({
                "evidence_id": c.get("evidence_id", f"cmp_{idx}"),
                "statement": f"{top_lbl} leads with {c['top_value']} while {bot_lbl} records {c['bottom_value']} across {c.get('dimension', 'dimension')}",
            })

        # 6. Verified Trends (with evidence_id)
        verified_trends = [
            {
                "evidence_id": t.get("evidence_id", f"trend_{idx}"),
                "statement": f"{t['title']}: {t.get('summary') or 'Temporal tracking across available periods'}",
            }
            for idx, t in enumerate(evidence.get("trends", []))
        ]

        # 7. Verified Anomalies (with evidence_id)
        verified_anomalies = [
            {
                "evidence_id": a.get("evidence_id", f"anomaly_{idx}"),
                "statement": f"{a['label']} ({a['value']}): {a['reason']}",
            }
            for idx, a in enumerate(evidence.get("anomalies", []))
        ]

        # 8. Data Quality (contextual - only included if present or relevant)
        quality_raw = context.data_quality or {}
        quality_block = {}
        if quality_raw:
            score = quality_raw.get("score")
            missing = quality_raw.get("missing_cells", 0)
            dups = quality_raw.get("duplicate_rows", 0)
            comp = quality_raw.get("completeness_pct")
            if score is not None:
                quality_block["quality_score"] = f"{float(score):.1f}/100"
            if comp is not None:
                quality_block["completeness"] = f"{float(comp):.1f}%"
            if missing > 0:
                quality_block["missing_values"] = f"{missing:,} missing cells detected"
            if dups > 0:
                quality_block["duplicate_records"] = f"{dups:,} duplicate rows detected"

        # 9. Limitations & Unavailable Metrics (with evidence_id)
        limitations = []
        for idx, lim_str in enumerate(context.limitations):
            limitations.append({
                "evidence_id": f"limitation_ctx_{idx+1}",
                "statement": lim_str,
            })
        for idx, unavail in enumerate(evidence.get("unavailable_metrics", [])):
            msg = f"{unavail} is not available in the dataset and cannot be evaluated."
            if not any(l["statement"] == msg for l in limitations):
                limitations.append({
                    "evidence_id": f"limitation_{idx+1}",
                    "statement": msg,
                })

        row_cnt = evidence.get("row_count") or 0
        if 0 < row_cnt < 30:
            limitations.append({
                "evidence_id": "limitation_small_sample",
                "statement": f"Small sample size ({row_cnt} records); findings should be interpreted descriptively.",
            })

        return {
            "dataset": dataset_block,
            "report": report_block,
            "verified_metrics": verified_metrics,
            "verified_comparisons": verified_comparisons,
            "verified_rankings": verified_rankings,
            "verified_trends": verified_trends,
            "verified_anomalies": verified_anomalies,
            "data_quality": quality_block,
            "limitations": limitations,
            "evidence_density": evidence.get("evidence_density", "medium"),
            "specific_breakdowns": evidence.get("breakdowns", {}),
            "available_evidence_ids": evidence.get("all_evidence_ids", []),
        }
