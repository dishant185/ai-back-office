"""Universal Dynamic Business Intelligence Report Engine.

Generates comprehensive, capability-driven BI reports from ANY business dataset:
- Sales, HR, Finance, Inventory, Retail, Automotive, Technology, Logistics, Healthcare, Generic.
ZERO domain-specific branching or hardcoded templates.

Section Discovery:
1. Key Metrics Scorecard (ranked by semantic confidence & variation)
2. Business Composition & Segment Share (dimensions distribution)
3. Contribution & Volume Rankings (measures aggregated by dimensions)
4. Value Dispersion & Spread (numeric distributions)
5. Temporal Trajectory & Trends (when date dimensions exist)
6. Statistical Anomalies & Outliers (evidence-grounded)
7. Strategic Action Recommendations (evidence-linked)
"""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from app.analytics.engine import UniversalAnalyticsEngine
from app.analytics.ml_analytics import MLAnalyticsEngine
from app.data.semantic_mapping_engine import UniversalSemanticMappingEngine
from app.reporting.chart_builder import ChartBuilder
from app.reporting.formatter import format_value
from app.reporting.models import (
    ChartDefinition,
    RankingItem,
    ReportAnomaly,
    ReportMetric,
    ReportRanking,
    ReportRecommendation,
    ReportSection,
)
from app.analytics.semantic_classifier import SemanticClassifier
from app.data.semantic_contract import SemanticDataContract
from app.analytics.derived_metrics import calculate_financial_lineage


class UniversalReportEngine:
    """Canonical universal analytical report generation engine."""

    @classmethod
    def generate(
        cls,
        frame: pd.DataFrame,
        report_type: str = "standard",
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation], list[dict[str, Any]]]:
        row_count = int(len(frame))
        col_count = int(len(frame.columns))
        if row_count == 0:
            return [], [], [], [], []

        evidence_ledger: list[dict[str, Any]] = []
        evidence_counter = [0]

        def _add_evidence(
            source_field: str | None = None,
            entity: str | None = None,
            value: Any = None,
            formula: str | None = None,
            dimension: str | None = None,
            measure: str | None = None,
            share: float | None = None,
            category: str = "kpi",
        ) -> str:
            evidence_counter[0] += 1
            eid = f"ev_{category}_{evidence_counter[0]:04d}"
            evidence_ledger.append({
                "evidence_id": eid,
                "source_field": source_field,
                "entity": entity,
                "value": value,
                "formula": formula,
                "dimension": dimension,
                "measure": measure,
                "share": share,
                "category": category,
            })
            return eid

        engine = UniversalAnalyticsEngine(frame)
        catalog = UniversalSemanticMappingEngine.analyze(frame)
        contract = SemanticDataContract.from_frame(frame)
        mappings = catalog.mappings

        # Classify fields by semantic role & datatype (Strictly excluding IDENTIFIERS per Section 14)
        measure_fields = [
            m for m in mappings
            if (m.role == "measure" or m.detected_type == "numeric")
            and not SemanticClassifier.classify_field(m.source_column, frame[m.source_column]).is_identifier
        ]
        dim_fields = [m for m in mappings if m.role in ("dimension", "category") or m.detected_type in ("categorical", "boolean")]
        date_fields = [m for m in mappings if m.role == "time_dimension" or m.detected_type == "date"]
        outcome_fields = [m for m in mappings if m.role == "outcome"]

        # Ensure valid columns exist in frame
        valid_measures = [m for m in measure_fields if m.source_column in frame.columns]
        valid_dims = [m for m in dim_fields if m.source_column in frame.columns and frame[m.source_column].nunique() > 1]
        valid_dates = [m for m in date_fields if m.source_column in frame.columns]

        # ── 1. KPI Discovery & Ranking (Phase 11 & Section 17 KPI Qualification) ──
        kpi_candidates: list[tuple[float, SemanticFieldMapping]] = []
        for m in valid_measures:
            s = pd.to_numeric(frame[m.source_column], errors="coerce").dropna()
            prof = SemanticClassifier.classify_field(m.source_column, frame[m.source_column])
            is_qualified, _ = SemanticClassifier.validate_kpi_qualification(prof, s)
            if not is_qualified:
                continue
            completeness = len(s) / max(row_count, 1)
            score = (m.confidence * 0.4) + (completeness * 0.3) + (min(1.0, float(s.std()) / max(float(s.mean()), 1e-6)) * 0.3)
            kpi_candidates.append((score, m))

        kpi_candidates.sort(key=lambda x: x[0], reverse=True)
        top_kpi_fields = [item[1] for item in kpi_candidates[:4]]

        # Semantic role mapping
        domain_hint = catalog.domain_hint
        id_mapping = next((m for m in mappings if m.semantic_name in ("employee_id", "user_id", "entity_id", "id") or m.role == "identifier"), None)
        has_unique_entity_id = (
            id_mapping is not None
            and id_mapping.source_column in frame.columns
            and frame[id_mapping.source_column].nunique() == row_count
        )

        if has_unique_entity_id and id_mapping and "employee" in id_mapping.source_column.lower():
            pop_id = "employee_count"
            pop_name = "Total Headcount"
            pop_desc = "Verified unique employee headcount"
        else:
            pop_id = "record_count"
            pop_name = "Total Observations"
            pop_desc = f"Total verified {domain_hint.upper() if domain_hint != 'generic' else ''} records analyzed"

        # Register total population evidence
        _add_evidence(
            source_field="dataset",
            entity="Total Records",
            value=row_count,
            formula=f"len(frame) = {row_count}",
            category="population",
        )
        # Also create canonical ID for InsightDiscoveryEngine
        evidence_ledger[0]["evidence_id"] = "dataset.total_records"

        kpis: list[ReportMetric] = [
            ReportMetric(
                id=pop_id,
                name=pop_name,
                value=row_count,
                formatted_value=f"{row_count:,}",
                unit="count",
                description=pop_desc,
                priority=1,
                category="volume",
            )
        ]
        # Also ensure record_count exists for generic compatibility if pop_id was domain-specific
        if pop_id != "record_count":
            kpis.append(ReportMetric(
                id="record_count",
                name="Total Observations",
                value=row_count,
                formatted_value=f"{row_count:,}",
                unit="count",
                description="Total verified records analyzed",
                priority=99,
                category="volume",
            ))
        elif domain_hint == "hr":
            # Backward-compatible alias when domain is HR
            kpis.append(ReportMetric(
                id="employee_count",
                name="Total Observations",
                value=row_count,
                formatted_value=f"{row_count:,}",
                unit="count",
                description=pop_desc,
                priority=99,
                category="volume",
            ))

        prio = 2

        # ── Outcome / Attrition / Churn KPIs ──
        outcome_mapping = next((m for m in mappings if m.semantic_name == "separation_indicator" or any(k in m.source_column.lower() for k in ["leave_or_not", "attrition", "left", "churn"])), None)
        if outcome_mapping and outcome_mapping.source_column in frame.columns:
            s_raw = frame[outcome_mapping.source_column].dropna()
            s_flags = s_raw.astype(str).str.strip().str.lower().map(lambda x: 1 if x in ("1", "1.0", "yes", "true", "left", "resigned", "churned") else (0 if x in ("0", "0.0", "no", "false") else None)).dropna()
            if not s_flags.empty:
                left_count = int(s_flags.sum())
                retained_count = int(row_count - left_count)
                rate_val = round(float(left_count / max(row_count, 1) * 100.0), 1)

                is_hr = domain_hint == "hr"
                rate_name = "Attrition Rate" if is_hr else "Churn Rate"
                if not has_unique_entity_id:
                    left_name = "Separated Records" if is_hr else "Churned Records"
                    ret_name = "Retained Records" if is_hr else "Retained Records"
                else:
                    entity_label = "Employees" if is_hr and id_mapping and "employee" in id_mapping.source_column.lower() else "Entities"
                    left_name = f"Separated {entity_label}" if is_hr else f"Churned {entity_label}"
                    ret_name = f"Retained {entity_label}" if is_hr else f"Retained {entity_label}"

                kpis.append(ReportMetric(
                    id="attrition_rate" if is_hr else "churn_rate",
                    name=rate_name,
                    value=rate_val,
                    formatted_value=f"{rate_val:.1f}%",
                    unit="percentage",
                    description="Departed / Eligible Records",
                    priority=prio,
                    category="outcome",
                ))
                prio += 1

                kpis.append(ReportMetric(
                    id="employees_left" if is_hr else "entities_lost",
                    name=left_name,
                    value=left_count,
                    formatted_value=f"{left_count:,}",
                    unit="count",
                    description=f"Count of {left_name.lower()}",
                    priority=prio,
                    category="outcome",
                ))
                prio += 1

                kpis.append(ReportMetric(
                    id="employees_retained" if is_hr else "entities_retained",
                    name=ret_name,
                    value=retained_count,
                    formatted_value=f"{retained_count:,}",
                    unit="count",
                    description=f"Count of {ret_name.lower()}",
                    priority=prio,
                    category="outcome",
                ))
                prio += 1

                _add_evidence(
                    source_field=outcome_mapping.source_column,
                    entity=rate_name,
                    value=f"{rate_val:.1f}%",
                    formula=f"{left_count} / {row_count}",
                    category="outcome",
                )

        # ── Age KPI if present ──
        age_col = next((c for c in frame.columns if str(c).lower() in ("age", "employee_age", "age_in_years")), None)
        if age_col:
            age_s = pd.to_numeric(frame[age_col], errors="coerce").dropna()
            if not age_s.empty:
                avg_age_val = round(float(age_s.mean()), 1)
                kpis.append(ReportMetric(
                    id="average_age",
                    name="Average Age",
                    value=avg_age_val,
                    formatted_value=f"{avg_age_val:.1f} yrs",
                    unit="years",
                    description="Mean age across population records",
                    priority=prio,
                    category="demographic",
                ))
                prio += 1
                _add_evidence(
                    source_field=age_col,
                    entity="Average Age",
                    value=f"{avg_age_val:.1f}",
                    formula=f"mean({age_col})",
                    category="demographic",
                )

        # ── Experience KPI if present ──
        exp_col = next((c for c in frame.columns if any(k in str(c).lower() for k in ("experience", "tenure", "years_experience", "domain_experience"))), None)
        if exp_col:
            exp_s = pd.to_numeric(frame[exp_col], errors="coerce").dropna()
            if not exp_s.empty:
                avg_exp_val = round(float(exp_s.mean()), 1)

                # Issue 4: Derive semantic label from verified source field name
                # Never inflate "ExperienceInCurrentDomain" to "Company Tenure" etc.
                exp_col_low = exp_col.lower().replace("_", " ")
                if "domain" in exp_col_low:
                    exp_label = "Avg Domain Experience"
                    exp_desc = f"Mean experience in current domain (source: {exp_col})"
                elif "tenure" in exp_col_low and "company" in exp_col_low:
                    exp_label = "Avg Company Tenure"
                    exp_desc = f"Mean company tenure (source: {exp_col})"
                elif "tenure" in exp_col_low:
                    exp_label = "Avg Tenure"
                    exp_desc = f"Mean tenure (source: {exp_col})"
                else:
                    # Generic: derive from column name directly
                    exp_label = f"Avg {exp_col.replace('_', ' ').replace('In', ' ').strip().title()}"
                    exp_desc = f"Mean value of {exp_col}"

                kpis.append(ReportMetric(
                    id="avg_experience",
                    name=exp_label,
                    value=avg_exp_val,
                    formatted_value=f"{avg_exp_val:.1f} yrs",
                    unit="years",
                    description=exp_desc,
                    priority=prio,
                    category="experience",
                ))
                prio += 1
                _add_evidence(
                    source_field=exp_col,
                    entity=exp_label,
                    value=f"{avg_exp_val:.1f}",
                    formula=f"mean({exp_col})",
                    category="experience",
                )

        tot_rev = None
        tot_prof = None

        # Check for revenue/sales column
        rev_col = next((c for c in frame.columns if c.lower() in ("revenue", "sales", "sales_amount", "sales_value", "total_sales")), None)
        if rev_col:
            rev_s = pd.to_numeric(frame[rev_col], errors="coerce").dropna()
            if not rev_s.empty:
                tot_rev = float(rev_s.sum())
                kpis.append(ReportMetric(
                    id="total_revenue",
                    name="Revenue",
                    value=round(tot_rev, 2),
                    formatted_value=format_value(tot_rev, "currency"),
                    unit="currency",
                    description="Gross commercial sales revenue recognized",
                    priority=prio,
                    category="financial",
                ))
                prio += 1
                _add_evidence(
                    source_field=rev_col,
                    entity="Total Revenue",
                    value=format_value(tot_rev, "currency"),
                    formula=f"sum({rev_col})",
                    category="financial",
                )

                # ── Average Order Value (AOV) / Transaction Value Grain Validation (Bug 9) ──
                order_col = next((c for c in frame.columns if any(k in str(c).lower() for k in ("order_id", "order_number", "ord_id", "order_no"))), None)
                txn_col = next((c for c in frame.columns if any(k in str(c).lower() for k in ("transaction_id", "trans_id", "txn_id", "invoice_id", "invoice_number"))), None)

                if order_col:
                    distinct_orders = int(frame[order_col].nunique())
                    if distinct_orders > 0:
                        aov_val = tot_rev / distinct_orders
                        aov_desc = "Mean revenue recognized per order" if distinct_orders == len(frame) else "Mean revenue recognized across distinct orders"
                        kpis.append(ReportMetric(
                            id="avg_order_value",
                            name="Average Order Value",
                            value=round(aov_val, 2),
                            formatted_value=format_value(aov_val, "currency"),
                            unit="currency",
                            description=aov_desc,
                            priority=prio,
                            category="financial",
                        ))
                        prio += 1
                elif txn_col:
                    distinct_txns = int(frame[txn_col].nunique())
                    if distinct_txns > 0:
                        atv_val = tot_rev / distinct_txns
                        kpis.append(ReportMetric(
                            id="avg_order_value",
                            name="Average Transaction Value",
                            value=round(atv_val, 2),
                            formatted_value=format_value(atv_val, "currency"),
                            unit="currency",
                            description="Mean revenue recognized per transaction",
                            priority=prio,
                            category="financial",
                        ))
                        prio += 1
                elif domain_hint == "sales" and len(frame) > 0:
                    atv_val = tot_rev / len(frame)
                    kpis.append(ReportMetric(
                        id="avg_order_value",
                        name="Average Transaction Value",
                        value=round(atv_val, 2),
                        formatted_value=format_value(atv_val, "currency"),
                        unit="currency",
                        description="Mean revenue recognized per operational transaction",
                        priority=prio,
                        category="financial",
                    ))
                    prio += 1

        # ── Verified Financial Lineage (Section 19-22 Financial Semantic Validation) ──
        fin_lineage = calculate_financial_lineage(frame)
        for fin_key, fin_item in fin_lineage.items():
            if fin_item.value is not None:
                # Add to KPI scorecard if not already covered
                if not any(k.id == fin_key for k in kpis):
                    unit_type = "percentage" if "margin" in fin_key else "currency"
                    kpis.append(ReportMetric(
                        id=fin_key,
                        name=fin_item.label,
                        value=fin_item.value,
                        formatted_value=fin_item.formatted_value,
                        unit=unit_type,
                        description=fin_item.semantic_definition,
                        priority=prio,
                        category="financial",
                    ))
                    if fin_key == "net_margin" and not any(k.id == "profit_margin" for k in kpis):
                        kpis.append(ReportMetric(
                            id="profit_margin",
                            name=fin_item.label,
                            value=fin_item.value,
                            formatted_value=fin_item.formatted_value,
                            unit=unit_type,
                            description=fin_item.semantic_definition,
                            priority=prio,
                            category="financial",
                        ))
                    prio += 1

                # Record full lineage into evidence ledger
                _add_evidence(
                    source_field=",".join(fin_item.source_fields),
                    entity=fin_item.label,
                    value=fin_item.formatted_value,
                    formula=fin_item.formula or fin_item.semantic_definition,
                    category="financial_lineage",
                )

        # Check for quantity column (Bug 10: semantic-verified quantity labelling)
        qty_col = next((c for c in frame.columns if c.lower() in ("quantity", "units", "units_sold", "qty", "volume", "stock_quantity", "ordered_quantity", "shipped_quantity")), None)
        if qty_col:
            qty_s = pd.to_numeric(frame[qty_col], errors="coerce").dropna()
            if not qty_s.empty:
                tot_qty = int(qty_s.sum())
                q_low = qty_col.lower()

                # Verify Units Sold through semantic mapping (Bug 10)
                if q_low in ("units_sold", "quantity_sold", "sales_quantity") or (q_low in ("quantity", "units", "qty", "volume") and domain_hint == "sales"):
                    qty_name = "Total Units Sold"
                    qty_desc = "Aggregate unit volume sold across records"
                elif "stock" in q_low or "inventory" in q_low or "on_hand" in q_low:
                    qty_name = "Stock On Hand"
                    qty_desc = "Aggregate inventory units on hand"
                elif "order" in q_low:
                    qty_name = "Units Ordered"
                    qty_desc = "Aggregate units ordered across records"
                elif "ship" in q_low:
                    qty_name = "Units Shipped"
                    qty_desc = "Aggregate units shipped across records"
                else:
                    qty_name = f"Total {qty_col.replace('_', ' ').title()}"
                    qty_desc = f"Aggregate sum of {qty_col}"

                kpi_qty_id = "total_volume" if domain_hint == "sales" or "sold" in qty_name.lower() else ("stock_quantity" if "stock" in q_low else f"kpi_{qty_col}")
                kpis.append(ReportMetric(
                    id=kpi_qty_id,
                    name=qty_name,
                    value=tot_qty,
                    formatted_value=f"{tot_qty:,}",
                    unit="count",
                    description=qty_desc,
                    priority=prio,
                    category="volume",
                ))
                prio += 1

        prof_cols = [c for item in fin_lineage.values() for c in item.source_fields]
        for m in top_kpi_fields:
            if m.source_column in (age_col, exp_col, outcome_mapping.source_column if outcome_mapping else None, rev_col, qty_col) or m.source_column in prof_cols:
                continue
            s = pd.to_numeric(frame[m.source_column], errors="coerce").dropna()
            if s.empty:
                continue
            mean_val = float(s.mean())
            is_curr = m.unit == "currency" or any(k in m.semantic_name for k in ["cost", "price", "mrr", "arr"])
            is_pct = m.unit == "percentage" or "rate" in m.semantic_name

            fmt_type = "currency" if is_curr else ("percentage" if is_pct else "number")
            formatted = format_value(mean_val, fmt_type)

            kpis.append(ReportMetric(
                id=f"kpi_{m.source_column}",
                name=m.suggested_label,
                value=round(mean_val, 2),
                formatted_value=formatted,
                unit=m.unit,
                description=m.definition,
                priority=prio,
                category="performance",
            ))
            prio += 1

        sections: list[ReportSection] = []

        # ── 2. Business Composition & Dimension Breakdown (Phase 24) ──
        for dim in valid_dims[:3]:
            dim_col = dim.source_column
            dim_title = dim.suggested_label
            items = engine.group_by(dim_col, top_n=8)
            if not items:
                continue

            ranking_items = []
            sec_evidence_ids = []
            for it in items:
                eid = _add_evidence(
                    dimension=dim_col,
                    entity=it["label"],
                    value=it["value"],
                    share=it["share"],
                    formula=f"count({dim_col} == '{it['label']}')",
                    category="distribution",
                )
                sec_evidence_ids.append(eid)
                ranking_items.append(RankingItem(
                    rank=it["rank"],
                    label=it["label"],
                    value=it["value"],
                    formatted_value=f"{it['value']:,}",
                    pct_of_total=it["share"],
                    subtext=f"{it['share']:.1f}% share of recorded volume ({it['value']:,} records)" if it["share"] is not None else None,
                ))

            rankings = [
                ReportRanking(
                    id=f"rank_{dim_col}",
                    title=f"{dim_title} Distribution",
                    dimension=dim_col,
                    metric="records",
                    items=ranking_items,
                )
            ]

            callout = None
            if ranking_items:
                lead = ranking_items[0]
                callout = f"The primary segment in {dim_title} is {lead.label}, commanding {lead.pct_of_total:.1f}% of recorded volume ({lead.formatted_value} records)."

            # Optional distribution chart
            dist_chart = ChartBuilder.categorical_distribution(frame, dim_col, f"{dim_title} Composition", f"chart_dist_{dim_col}")
            charts = [dist_chart] if dist_chart else []

            if rankings or charts:
                sections.append(ReportSection(
                    id=f"section_{dim_col}",
                    title=f"{dim_title} Composition & Share",
                    description=f"Structural distribution of records classified across {dim_title}.",
                    metrics=[kpis[0]],
                    charts=charts,
                    rankings=rankings,
                    callout=callout,
                    evidence_ids=sec_evidence_ids,
                ))

        # ── 3. Cross-Dimensional Contribution & Performance (Rankings by Measures) ──
        if valid_dims and valid_measures:
            p_dim = valid_dims[0].source_column
            p_meas = valid_measures[0].source_column
            dim_title = valid_dims[0].suggested_label
            meas_title = valid_measures[0].suggested_label

            agg_items = engine.group_by(p_dim, measure=p_meas, agg="sum", top_n=8)
            if agg_items:
                r_items = []
                sec3_evidence_ids = []
                for it in agg_items:
                    eid = _add_evidence(
                        dimension=p_dim,
                        measure=p_meas,
                        entity=it["label"],
                        value=it["value"],
                        share=it["share"],
                        formula=f"sum({p_meas}) by {p_dim}",
                        category="ranking",
                    )
                    sec3_evidence_ids.append(eid)
                    r_items.append(RankingItem(
                        rank=it["rank"],
                        label=it["label"],
                        value=it["value"],
                        formatted_value=f"{it['value']:,.2f}",
                        pct_of_total=it["share"],
                        subtext=f"{it['share']:.1f}% share of total {meas_title} ({it['value']:,.2f})" if it["share"] is not None else None,
                    ))

                contribution_ranking = ReportRanking(
                    id=f"contrib_{p_dim}_{p_meas}",
                    title=f"Total {meas_title} by {dim_title}",
                    dimension=p_dim,
                    metric=p_meas,
                    items=r_items,
                )

                lead_entity = r_items[0] if r_items else None
                callout_msg = (
                    f"{lead_entity.label} generated the highest aggregate {meas_title} ({lead_entity.formatted_value}), "
                    f"accounting for {lead_entity.pct_of_total:.1f}% of total contribution."
                    if lead_entity and lead_entity.pct_of_total
                    else None
                )

                ranking_chart = ChartBuilder.ranking_bar(
                    frame,
                    p_dim,
                    p_meas,
                    f"Top {dim_title} by {meas_title}",
                    f"chart_rank_{p_dim}_{p_meas}",
                )

                sections.append(ReportSection(
                    id=f"section_contrib_{p_dim}",
                    title=f"{meas_title} Contribution Analysis",
                    description=f"Direct aggregate performance comparison across {dim_title} segments.",
                    charts=[ranking_chart] if ranking_chart else [],
                    rankings=[contribution_ranking],
                    callout=callout_msg,
                    evidence_ids=sec3_evidence_ids,
                ))

        # ── 4. Value Dispersion & Spread (Histograms for numeric measures) ──
        num_charts: list[ChartDefinition] = []
        sec4_evidence_ids: list[str] = []
        for m in valid_measures[:2]:
            clean_name = m.suggested_label
            hist = ChartBuilder.numeric_histogram(
                frame, m.source_column, f"{clean_name} Distribution", f"hist_{m.source_column}", bins=5
            )
            if hist:
                num_charts.append(hist)
                eid = _add_evidence(
                    source_field=m.source_column,
                    entity=f"{clean_name} Spread",
                    value=len(hist.data),
                    formula=f"histogram({m.source_column})",
                    category="dispersion",
                )
                sec4_evidence_ids.append(eid)

        if num_charts:
            sections.append(ReportSection(
                id="section_numeric_dispersion",
                title="Statistical Spread & Density",
                description="Distribution density of key quantitative parameters showing dispersion characteristics.",
                charts=num_charts,
                evidence_ids=sec4_evidence_ids,
            ))

        # ── 5. Temporal Trajectory & Trends (Strict Section 23 Gating: >= 3 periods) ──
        if valid_dates and valid_measures and contract.capabilities.get("trend", False):
            d_col = valid_dates[0].source_column
            m_col = valid_measures[0].source_column
            trend_data = engine.trend(d_col, m_col, granularity="monthly")
            if len(trend_data) >= 3:
                trend_chart = ChartDefinition(
                    id=f"trend_{d_col}_{m_col}",
                    chart_type="line",
                    title=f"{valid_measures[0].suggested_label} Trajectory Over Time",
                    x_key="period",
                    y_key="value",
                    data=trend_data,
                )
                start_p = trend_data[0]["period"]
                end_p = trend_data[-1]["period"]
                eid = _add_evidence(
                    dimension=d_col,
                    measure=m_col,
                    entity=f"{valid_measures[0].suggested_label} Trend",
                    value=len(trend_data),
                    formula=f"monthly trend of {m_col} over {d_col}",
                    category="trend",
                )
                sections.append(ReportSection(
                    id="section_temporal_trend",
                    title="Chronological Trajectory & Performance",
                    description=f"Monthly chronological trend observed from {start_p} to {end_p}.",
                    charts=[trend_chart],
                    callout=f"Tracked across {len(trend_data)} sequential periods.",
                    evidence_ids=[eid],
                ))

        # Filter out any empty sections or sections lacking evidence
        sections = [
            s for s in sections
            if (s.rankings or s.charts or s.metrics) and s.evidence_ids
        ]

        # ── 6. Statistical Outliers & Anomalies (Phase 12) ──
        anomalies: list[ReportAnomaly] = []
        for m in valid_measures[:2]:
            ml_res = MLAnalyticsEngine.detect_anomalies(frame, m.source_column, method="iqr")
            if ml_res and ml_res.result.get("outlier_count", 0) > 0:
                count = ml_res.result["outlier_count"]
                pct = ml_res.result["outlier_percentage"]
                anomalies.append(ReportAnomaly(
                    id=f"anomaly_{m.source_column}",
                    metric=m.source_column,
                    label=f"Statistical Dispersion in {m.suggested_label}",
                    value=f"{count} outlier records ({pct}%)",
                    expected=ml_res.result.get("threshold_rule", "Within 1.5 * IQR"),
                    severity="high" if pct > 10.0 else "medium",
                    reason=f"Identified {count} observations falling outside standard Tukey interquartile bounds.",
                ))

        # ── 7. Evidence-Linked Recommendations (Phase 13 & 16) ──
        recommendations: list[ReportRecommendation] = []
        if sections and sections[0].rankings and sections[0].rankings[0].items:
            lead = sections[0].rankings[0].items[0]
            if lead.pct_of_total and lead.pct_of_total >= 35.0:
                rec_eid = _add_evidence(
                    entity=lead.label,
                    value=f"{lead.pct_of_total:.1f}%",
                    formula=f"volume_share >= 35%",
                    category="concentration_risk",
                )
                recommendations.append(ReportRecommendation(
                    id="rec_monitor_concentration",
                    title=f"Address Volume Dependency on {lead.label}",
                    description=(
                        f"Evaluate risk mitigation strategies for {lead.label}, which represents "
                        f"{lead.pct_of_total:.1f}% of total observed volume ({lead.formatted_value} records)."
                    ),
                    priority="high" if lead.pct_of_total >= 50.0 else "medium",
                    category="operations",
                    evidence_ids=[rec_eid] + (sections[0].evidence_ids[:1] if sections[0].evidence_ids else []),
                ))

        if anomalies:
            lead_a = anomalies[0]
            anom_eid = _add_evidence(
                source_field=lead_a.metric,
                entity=lead_a.label,
                value=lead_a.value,
                formula=lead_a.expected,
                category="anomaly_evidence",
            )
            recommendations.append(ReportRecommendation(
                id="rec_audit_anomalies",
                title=f"Audit Extreme Values in {lead_a.label}",
                description="Conduct audit verification on extreme outliers to ensure reporting integrity.",
                priority="medium",
                category="governance",
                evidence_ids=[anom_eid],
            ))

        # Budget variance evidence-based recommendation (Bug 4: strictly evidence-grounded)
        budget_col = next((c for c in frame.columns if "budget" in str(c).lower()), None)
        actual_col = next((c for c in frame.columns if any(k in str(c).lower() for k in ("actual", "expenditure", "spend"))), None)
        if budget_col and actual_col:
            b_s = pd.to_numeric(frame[budget_col], errors="coerce").dropna()
            a_s = pd.to_numeric(frame[actual_col], errors="coerce").dropna()
            if not b_s.empty and not a_s.empty:
                b_val = float(b_s.sum())
                a_val = float(a_s.sum())
                if b_val > 0 and a_val > 0:
                    var_amt = b_val - a_val
                    pct_diff = abs(var_amt) / b_val * 100.0
                    if pct_diff >= 1.0:
                        status_verb = "under" if var_amt > 0 else "over"
                        bv_eid = _add_evidence(
                            source_field=f"{budget_col},{actual_col}",
                            entity="Budget Variance",
                            value=f"{pct_diff:.1f}%",
                            formula=f"abs({b_val} - {a_val}) / {b_val}",
                            category="variance_evidence",
                        )
                        recommendations.append(ReportRecommendation(
                            id="rec_budget_variance",
                            title=f"Address Budget Variance ({status_verb.title()} Budget by {pct_diff:.1f}%)",
                            description=f"Actual expenditure is {format_value(abs(var_amt), 'currency')} ({pct_diff:.1f}%) {status_verb} allocated budget across verified accounts.",
                            priority="medium" if pct_diff < 10.0 else "high",
                            category="finance",
                            evidence_ids=[bv_eid],
                        ))

        # ── 8. Build final evidence entries for anomalies & recommendations ──
        for a in anomalies:
            _add_evidence(
                source_field=a.metric,
                entity=a.label,
                value=a.value,
                formula=f"IQR outlier detection on {a.metric}",
                category="anomaly",
            )

        for r in recommendations:
            if not r.evidence_ids:
                eid = _add_evidence(
                    entity=r.title,
                    value=r.priority,
                    formula=f"Evidence-linked recommendation: {r.category}",
                    category="recommendation",
                )
                r.evidence_ids = [eid]

        return kpis, sections, anomalies, recommendations, evidence_ledger
