"""Report Evidence Builder for Production AI Executive Summary Engine V2.

Collects verified analytical facts calculated by the deterministic engine for the CURRENT REPORT.
Enforces:
- Deterministic Evidence ID System (metric.total_revenue, ranking.region.revenue.1, etc.)
- Rich Semantic Data Model (semantic_measure, aggregation, unit, currency, scope, source)
- Zero cross-report and global dataset contamination via ReportRelevanceEngine
- Strict Zero != Unavailable differentiation
"""
from __future__ import annotations

import re
from typing import Any
from app.reporting.report_context import ReportContext
from app.reporting.report_relevance import RelevanceCategory, ReportRelevanceEngine


class ReportEvidenceBuilder:
    """Builds report-specific verified evidence payloads from authoritative analytics."""

    @classmethod
    def _slugify(cls, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", str(text).lower()).strip()
        return re.sub(r"[-\s]+", "_", s)

    @classmethod
    def infer_semantic_measure(cls, metric_id: str, name: str) -> tuple[str, str, str | None]:
        """Infers (semantic_measure, default_unit, currency)."""
        combined = f"{metric_id} {name}".lower()
        if "revenue" in combined or "sales" in combined or "turnover" in combined and "attrition" not in combined:
            if "volume" in combined:
                return "sales_volume", "units", None
            return "revenue", "currency", "USD"
        if "profit" in combined or "income" in combined or "margin" in combined:
            if "margin" in combined or "%" in combined or "pct" in combined or "rate" in combined:
                return "margin", "%", None
            return "profit", "currency", "USD"
        if "attrition" in combined or "turnover" in combined:
            return "attrition_rate", "%", None
        if "headcount" in combined or "employee" in combined:
            return "headcount", "count", None
        if "age" in combined:
            return "age", "years", None
        if "experience" in combined and "domain" in combined:
            return "domain_experience", "years", None
        if "experience" in combined:
            return "experience", "years", None
        if "tenure" in combined:
            return "tenure", "years", None
        if "missing" in combined:
            return "missing_values", "cells", None
        if "duplicate" in combined:
            return "duplicate_records", "records", None
        if "invalid" in combined:
            return "invalid_records", "records", None
        if "completeness" in combined:
            return "completeness", "%", None
        if "quality" in combined or "score" in combined:
            return "quality_score", "/100", None
        if "count" in combined or "records" in combined or "rows" in combined:
            return "record_count", "records", None
        if "columns" in combined:
            return "column_count", "columns", None
        if "order" in combined or "aov" in combined:
            return "average_order_value", "currency", "USD"
        return cls._slugify(metric_id or name), "value", None

    @classmethod
    def is_metric_allowed_for_report(
        cls,
        metric_id: str,
        metric_name: str,
        report_type: str,
        report_title: str,
        report_domain: str,
    ) -> bool:
        """Filters out global dataset metrics that are irrelevant to the current report."""
        mock_item = {
            "id": metric_id,
            "name": metric_name,
            "metric_name": metric_name,
        }
        res = ReportRelevanceEngine.classify_item(
            item=mock_item,
            report_type=report_type,
            report_title=report_title,
            dataset_domain=report_domain,
        )
        return res.category in (RelevanceCategory.DIRECT, RelevanceCategory.SUPPORTING)

    @classmethod
    def build_evidence(
        cls,
        context: ReportContext,
        report_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Collects verified empirical evidence strictly calculated for the current report."""
        kpis = report_payload.get("kpi_metrics", [])
        sections = report_payload.get("sections", [])
        anomalies = report_payload.get("anomalies", [])
        recommendations = report_payload.get("recommendations", [])
        row_count = report_payload.get("row_count") or (
            context.verified_metrics and next((m.get("value") for m in context.verified_metrics if m.get("id") == "row_count"), None)
        )
        col_count = report_payload.get("column_count")

        metrics: list[dict[str, Any]] = []
        unavailable_metrics: list[str] = []
        verified_number_pool: set[float] = set()
        evidence_id_map: dict[str, Any] = {}

        is_data_quality_report = (
            context.report_type.lower() in ("data_quality", "data_quality_report")
            or "quality" in context.report_type.lower()
            or "data quality" in context.report_title.lower()
        )

        # 1. Process KPIs with strict relevance and standardized evidence IDs
        for k in kpis:
            k_id = k.get("id", "")
            val = k.get("value")
            name = k.get("name") or k_id.replace("_", " ").title()
            fval = k.get("formatted_value") or (str(val) if val is not None else "Unavailable")
            is_avail = (
                k.get("available", True) is not False
                and val is not None
                and str(val).strip() != ""
                and str(val).lower() not in ("unavailable", "none", "null", "nan")
            )

            # Strict relevance check
            if not cls.is_metric_allowed_for_report(
                metric_id=k_id,
                metric_name=name,
                report_type=context.report_type,
                report_title=context.report_title,
                report_domain=context.dataset_profile,
            ):
                continue

            slug = cls._slugify(k_id or name)
            ev_id = f"metric.{slug}"
            alias_ev_id = f"metric_{slug}"
            measure, default_unit, default_curr = cls.infer_semantic_measure(k_id, name)
            unit = k.get("unit") or default_unit
            currency = k.get("currency") or default_curr

            if is_avail:
                metric_dict = {
                    "id": ev_id,
                    "evidence_id": ev_id,
                    "alias_evidence_id": alias_ev_id,
                    "dataset_id": context.dataset_id,
                    "metric_name": name,
                    "name": name,
                    "semantic_measure": measure,
                    "aggregation": k.get("aggregation", "sum"),
                    "value": val,
                    "formatted_value": fval,
                    "unit": unit,
                    "currency": currency,
                    "scope": "current_report",
                    "source": "deterministic_analytics",
                }
                metrics.append(metric_dict)
                evidence_id_map[ev_id] = metric_dict
                evidence_id_map[alias_ev_id] = metric_dict
                if k_id:
                    evidence_id_map[k_id] = metric_dict
                try:
                    verified_number_pool.add(float(val))
                except (ValueError, TypeError):
                    pass
            else:
                if name not in unavailable_metrics:
                    unavailable_metrics.append(name)

        # 2. Data Quality Audit Explicit Handling
        dq_raw = report_payload.get("data_quality") or context.data_quality or report_payload.get("quality") or {}
        if is_data_quality_report and dq_raw:
            if dq_raw.get("total_rows"):
                row_count = dq_raw["total_rows"]
            if dq_raw.get("total_columns"):
                col_count = dq_raw["total_columns"]
            dq_missing = dq_raw.get("missing_cells", dq_raw.get("missing_values"))
            dq_dups = dq_raw.get("duplicate_rows", dq_raw.get("duplicate_records"))
            dq_invalid = dq_raw.get("invalid_rows", dq_raw.get("invalid_records"))
            dq_comp = dq_raw.get("completeness_pct", dq_raw.get("completeness"))
            dq_score = dq_raw.get("score", dq_raw.get("quality_score"))

            dq_metric_defs = [
                ("total_records", "Total Records", row_count, f"{row_count:,}" if row_count else None, "records", "count", None),
                ("total_columns", "Total Columns", col_count, str(col_count) if col_count else None, "columns", "count", None),
                ("missing_values", "Missing Values", dq_missing, f"{int(dq_missing):,}" if dq_missing is not None else None, "cells", "count", None),
                ("duplicate_records", "Duplicate Records", dq_dups, f"{int(dq_dups):,}" if dq_dups is not None else None, "records", "count", None),
                ("invalid_records", "Invalid Records", dq_invalid, f"{int(dq_invalid):,}" if dq_invalid is not None else None, "records", "count", None),
                ("completeness", "Data Completeness", dq_comp, f"{float(dq_comp):.1f}%" if dq_comp is not None else None, "%", "rate", None),
                ("quality_score", "Quality Score", dq_score, f"{float(dq_score):.1f}" if dq_score is not None else None, "/100", "score", None),
            ]
            for m_id, m_name, m_val, m_fval, m_unit, m_agg, m_curr in dq_metric_defs:
                if m_val is not None:
                    ev_id = f"quality.{m_id}"
                    alias_ev_id = f"metric_dq_{m_id}"
                    if not any(m.get("id") in (ev_id, m_id) for m in metrics):
                        m_obj = {
                            "id": m_id,
                            "evidence_id": ev_id,
                            "alias_evidence_id": alias_ev_id,
                            "dataset_id": context.dataset_id,
                            "metric_name": m_name,
                            "name": m_name,
                            "semantic_measure": m_id,
                            "aggregation": m_agg,
                            "value": m_val,
                            "formatted_value": m_fval,
                            "unit": m_unit,
                            "currency": m_curr,
                            "scope": "current_report",
                            "source": "deterministic_analytics",
                        }
                        metrics.append(m_obj)
                        evidence_id_map[ev_id] = m_obj
                        evidence_id_map[alias_ev_id] = m_obj
                        evidence_id_map[m_id] = m_obj
                    try:
                        verified_number_pool.add(float(m_val))
                    except (ValueError, TypeError):
                        pass
                else:
                    if m_name not in unavailable_metrics:
                        unavailable_metrics.append(m_name)

        if row_count is not None:
            try:
                verified_number_pool.add(float(row_count))
            except (ValueError, TypeError):
                pass
        if col_count is not None:
            try:
                verified_number_pool.add(float(col_count))
            except (ValueError, TypeError):
                pass

        # 3. Rankings, Comparisons, Distributions, Trends
        rankings: list[dict[str, Any]] = []
        comparisons: list[dict[str, Any]] = []
        distributions: list[dict[str, Any]] = []
        trends: list[dict[str, Any]] = []

        if not is_data_quality_report:
            for s in sections:
                # Rankings
                for rk in s.get("rankings", []):
                    rk_dim = rk.get("dimension") or rk.get("title", "")
                    if not cls.is_metric_allowed_for_report(
                        metric_id=rk_dim,
                        metric_name=rk.get("title", ""),
                        report_type=context.report_type,
                        report_title=context.report_title,
                        report_domain=context.dataset_profile,
                    ):
                        continue

                    items = rk.get("items", [])
                    dim_slug = cls._slugify(rk_dim or rk.get("title", "dim"))
                    formatted_items = []
                    for idx, it in enumerate(items):
                        lbl = it.get("label", "")
                        v = it.get("value")
                        fv = it.get("formatted_value") or str(v)
                        rank_num = idx + 1
                        measure, unit, curr = cls.infer_semantic_measure(rk_dim, rk.get("title", ""))
                        item_id = f"ranking.{dim_slug}.{measure}.{rank_num}"
                        item_obj = {
                            "id": item_id,
                            "rank": rank_num,
                            "entity": lbl,
                            "dimension": rk_dim,
                            "semantic_measure": measure,
                            "value": v,
                            "formatted_value": fv,
                            "unit": unit,
                            "currency": curr,
                        }
                        formatted_items.append(item_obj)
                        evidence_id_map[item_id] = item_obj
                        if v is not None:
                            try:
                                verified_number_pool.add(float(v))
                            except (ValueError, TypeError):
                                pass

                    ev_id = f"ranking.{dim_slug}"
                    alias_ev_id = f"ranking_{dim_slug}"
                    rk_obj = {
                        "id": ev_id,
                        "evidence_id": ev_id,
                        "alias_evidence_id": alias_ev_id,
                        "title": rk.get("title", ""),
                        "dimension": rk_dim,
                        "items": formatted_items,
                        "top_entity": formatted_items[0] if formatted_items else None,
                        "bottom_entity": formatted_items[-1] if len(formatted_items) > 1 else None,
                    }
                    rankings.append(rk_obj)
                    evidence_id_map[ev_id] = rk_obj
                    evidence_id_map[alias_ev_id] = rk_obj

                    if len(formatted_items) >= 2:
                        top = formatted_items[0]
                        bot = formatted_items[-1]
                        top_slug = cls._slugify(top["entity"])
                        bot_slug = cls._slugify(bot["entity"])
                        cmp_id = f"comparison.{dim_slug}.{measure}.{top_slug}_vs_{bot_slug}"
                        alias_cmp_id = f"comparison_{top_slug}_{bot_slug}"
                        cmp_obj = {
                            "id": cmp_id,
                            "evidence_id": cmp_id,
                            "alias_evidence_id": alias_cmp_id,
                            "dimension": rk_dim,
                            "semantic_measure": measure,
                            "top_entity": top["entity"],
                            "top_value": top["formatted_value"],
                            "bottom_entity": bot["entity"],
                            "bottom_value": bot["formatted_value"],
                            "unit": unit,
                            "currency": curr,
                        }
                        comparisons.append(cmp_obj)
                        evidence_id_map[cmp_id] = cmp_obj
                        evidence_id_map[alias_cmp_id] = cmp_obj

                # Charts / Trends / Distributions
                for ch in s.get("charts", []):
                    ctype = ch.get("chart_type", "").lower()
                    c_title = ch.get("title", "")
                    c_data = ch.get("data", [])

                    for d in c_data:
                        for val in d.values():
                            try:
                                verified_number_pool.add(float(val))
                            except (ValueError, TypeError):
                                pass

                    title_slug = cls._slugify(c_title)
                    if ctype in ("line", "area") or "trend" in c_title.lower() or "time" in c_title.lower():
                        measure, unit, curr = cls.infer_semantic_measure(title_slug, c_title)
                        tr_id = f"trend.{title_slug}"
                        alias_tr_id = f"trend_{title_slug}"
                        tr_obj = {
                            "id": tr_id,
                            "evidence_id": tr_id,
                            "alias_evidence_id": alias_tr_id,
                            "title": c_title,
                            "semantic_measure": measure,
                            "data_points": len(c_data),
                            "summary": ch.get("description", ""),
                            "is_meaningful": len(c_data) >= 2,
                        }
                        trends.append(tr_obj)
                        evidence_id_map[tr_id] = tr_obj
                        evidence_id_map[alias_tr_id] = tr_obj
                    else:
                        dist_id = f"distribution.{title_slug}"
                        alias_dist_id = f"distribution_{title_slug}"
                        dist_obj = {
                            "id": dist_id,
                            "evidence_id": dist_id,
                            "alias_evidence_id": alias_dist_id,
                            "title": c_title,
                            "dimension": ch.get("x_axis", ""),
                            "metric": ch.get("y_axis", ""),
                            "category_count": len(c_data),
                        }
                        distributions.append(dist_obj)
                        evidence_id_map[dist_id] = dist_obj
                        evidence_id_map[alias_dist_id] = dist_obj

        # 4. Anomalies
        verified_anomalies: list[dict[str, Any]] = []
        for anom in anomalies:
            v = anom.get("value")
            anom_id = anom.get("id") or cls._slugify(anom.get("label", "anomaly"))
            slug_id = cls._slugify(anom_id)
            ev_id = f"anomaly.{slug_id}"
            alias_ev_id = f"anomaly_{slug_id}"
            anom_obj = {
                "id": ev_id,
                "evidence_id": ev_id,
                "alias_evidence_id": alias_ev_id,
                "label": anom.get("label"),
                "metric": anom.get("metric"),
                "value": v,
                "reason": anom.get("reason"),
                "severity": anom.get("severity", "medium"),
            }
            verified_anomalies.append(anom_obj)
            evidence_id_map[ev_id] = anom_obj
            evidence_id_map[alias_ev_id] = anom_obj
            if v is not None:
                try:
                    verified_number_pool.add(float(v))
                except (ValueError, TypeError):
                    pass

        # 5. Verified Recommendations
        verified_recs: list[dict[str, Any]] = []
        for idx, r in enumerate(recommendations):
            ev_id = f"rec.{idx+1}"
            alias_ev_id = f"rec_{idx+1}"
            r_obj = {
                "id": ev_id,
                "evidence_id": ev_id,
                "alias_evidence_id": alias_ev_id,
                "title": r.get("title"),
                "description": r.get("description"),
                "priority": r.get("priority", "medium"),
                "confidence": "supported",
            }
            verified_recs.append(r_obj)
            evidence_id_map[ev_id] = r_obj
            evidence_id_map[alias_ev_id] = r_obj

        # 6. Breakdowns
        specific_breakdowns: dict[str, Any] = {}
        if is_data_quality_report and dq_raw:
            specific_breakdowns["data_quality"] = {
                "total_rows": row_count,
                "total_columns": col_count,
                "missing_values": dq_raw.get("missing_cells", dq_raw.get("missing_values")),
                "duplicate_records": dq_raw.get("duplicate_rows", dq_raw.get("duplicate_records")),
                "invalid_records": dq_raw.get("invalid_rows", dq_raw.get("invalid_records")),
                "completeness": dq_raw.get("completeness_pct", dq_raw.get("completeness")),
                "field_quality": dq_raw.get("issues", dq_raw.get("field_quality", [])),
                "type_issues": dq_raw.get("type_issues", []),
                "quality_score": dq_raw.get("score", dq_raw.get("quality_score")),
            }
        else:
            for rk in rankings:
                dim = rk.get("dimension") or rk.get("title", "")
                if dim and rk.get("items"):
                    specific_breakdowns[dim.lower().replace(" ", "_")] = rk["items"]

        # 7. Limitations
        limitations = list(context.limitations)
        for u in unavailable_metrics:
            lim_msg = f"{u} is unavailable as the required fields were not present in the dataset."
            if lim_msg not in limitations:
                limitations.append(lim_msg)

        # 8. Scope & Target Metadata
        dataset_block = {
            "id": context.dataset_id,
            "name": context.dataset_name,
            "version": context.dataset_version,
            "row_count": row_count,
            "column_count": col_count,
            "domain": context.dataset_profile,
        }

        report_block = {
            "id": context.report_id,
            "type": context.report_type,
            "title": context.report_title,
            "purpose": context.report_purpose,
            "version": getattr(context, "report_version", 1),
        }

        scope_block = {
            "filters": context.filters,
            "date_range": context.date_range,
            "filter_hash": getattr(context, "filters_hash", "default"),
        }

        evidence_payload = {
            "dataset": dataset_block,
            "report": report_block,
            "scope": scope_block,
            "metrics": metrics,
            "rankings": rankings,
            "comparisons": comparisons,
            "trends": trends,
            "distributions": distributions,
            "anomalies": verified_anomalies,
            "quality": dq_raw if is_data_quality_report or (dq_raw.get("missing_cells") or 0) > 0 else {},
            "limitations": limitations,
            # Backward-compatible aliases
            "verified_metrics": metrics,
            "verified_rankings": rankings,
            "verified_comparisons": comparisons,
            "verified_trends": trends,
            "verified_distributions": distributions,
            "verified_anomalies": verified_anomalies,
            "data_quality": dq_raw if is_data_quality_report or (dq_raw.get("missing_cells") or 0) > 0 else {},
            "account_id": context.account_id,
            "dataset_id": context.dataset_id,
            "dataset_version": context.dataset_version,
            "report_id": context.report_id,
            "report_type": context.report_type,
            "report_title": context.report_title,
            "report_purpose": context.report_purpose,
            "row_count": row_count,
            "column_count": col_count,
            "unavailable_metrics": unavailable_metrics,
            "recommendations": verified_recs,
            "breakdowns": specific_breakdowns,
            "verified_numbers": sorted(list(verified_number_pool)),
            "evidence_density": "high" if (len(metrics) > 5 and len(rankings) > 0) else ("medium" if len(metrics) >= 3 else "low"),
            "evidence_id_map": evidence_id_map,
            "all_evidence_ids": list(evidence_id_map.keys()),
        }

        return evidence_payload
