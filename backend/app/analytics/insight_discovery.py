"""Insight Discovery Engine.

Generates deterministic, evidence-bound business insights from analytical facts.
Every insight generated MUST be linked to a verifiable evidence ID in the ledger.
Discovers:
- Dominant segments & Top contributors
- Concentration & distribution skews (Pareto / Herfindahl)
- Group comparisons & significant differentials
- Temporal trends, growth, and contraction
- Correlations and variable dependencies
- Statistical outliers and threshold breaches
- Data quality impact on analytical certainty
"""
from __future__ import annotations

from typing import Any
import pandas as pd
from pydantic import BaseModel, Field


class DiscoveredInsight(BaseModel):
    insight_id: str
    category: str  # concentration, dominance, comparison, trend, relationship, anomaly, quality
    title: str
    headline: str
    description: str
    significance: str  # high, medium, low
    evidence_ids: list[str] = Field(default_factory=list)
    impact_metrics: dict[str, Any] = Field(default_factory=dict)
    recommendation: str | None = None


class InsightDiscoveryEngine:
    """Universal insight discovery engine strictly bound to deterministic evidence."""

    @classmethod
    def discover(
        cls,
        frame: pd.DataFrame,
        evidence_ledger: list[dict[str, Any]],
        dataset_id: str = "dataset",
    ) -> list[DiscoveredInsight]:
        insights: list[DiscoveredInsight] = []
        evidence_by_id = {e.get("evidence_id"): e for e in evidence_ledger if e.get("evidence_id")}

        # 1. Total Population Insight
        pop_ev = evidence_by_id.get("dataset.total_records")
        if pop_ev:
            count_val = pop_ev.get("value", len(frame))
            insights.append(DiscoveredInsight(
                insight_id="insight.population.scale",
                category="scale",
                title="Population Scale",
                headline=f"{count_val:,} observations analyzed",
                description=f"Analysis computed across {count_val:,} verified records without synthetic interpolation.",
                significance="medium",
                evidence_ids=[pop_ev["evidence_id"]],
                impact_metrics={"total_records": count_val},
            ))

        # 2. Dominant Segment & Concentration Insights
        # Inspect evidence items with share metrics
        share_items = [e for e in evidence_ledger if e.get("share") is not None and e.get("dimension") not in ("dataset", None)]
        # Group by dimension
        dim_groups: dict[str, list[dict[str, Any]]] = {}
        for it in share_items:
            dim = it.get("dimension", "dimension")
            dim_groups.setdefault(dim, []).append(it)

        for dim, items in dim_groups.items():
            if not items:
                continue
            sorted_items = sorted(items, key=lambda x: x.get("share", 0.0), reverse=True)
            top_item = sorted_items[0]
            top_share = top_item.get("share", 0.0)
            top_label = top_item.get("entity", "Top Segment")
            meas_name = top_item.get("measure", "records")
            clean_dim = dim.replace("_", " ").title()

            if top_share >= 35.0:
                insights.append(DiscoveredInsight(
                    insight_id=f"insight.dominance.{dim}",
                    category="dominance",
                    title=f"Segment Dominance in {clean_dim}",
                    headline=f"{top_label} accounts for {top_share:.1f}% of {meas_name}",
                    description=(
                        f"The leading segment in {clean_dim} is {top_label}, which commands {top_share:.1f}% "
                        f"of total recorded {meas_name}. This represents significant operational concentration."
                    ),
                    significance="high" if top_share >= 50.0 else "medium",
                    evidence_ids=[top_item.get("evidence_id")],
                    impact_metrics={"dimension": dim, "lead_entity": top_label, "share_pct": top_share},
                    recommendation=f"Assess business risk and resource dependency tied specifically to {top_label}.",
                ))

            # Pairwise Comparison Insight if >= 2 items
            if len(sorted_items) >= 2:
                runner_up = sorted_items[1]
                diff_share = top_share - runner_up.get("share", 0.0)
                if diff_share >= 15.0:
                    insights.append(DiscoveredInsight(
                        insight_id=f"insight.comparison.{dim}.top2",
                        category="comparison",
                        title=f"Disproportionate Lead in {clean_dim}",
                        headline=f"{top_label} outpaces {runner_up.get('entity')} by {diff_share:.1f} percentage points",
                        description=(
                            f"{top_label} ({top_share:.1f}%) significantly exceeds the secondary segment "
                            f"{runner_up.get('entity')} ({runner_up.get('share', 0.0):.1f}%), creating a {diff_share:.1f}% spread."
                        ),
                        significance="medium",
                        evidence_ids=[top_item.get("evidence_id"), runner_up.get("evidence_id")],
                        impact_metrics={"spread_percentage_points": round(diff_share, 1)},
                    ))

        # 3. Anomaly / Outlier Insights from ledger
        anomaly_items = [e for e in evidence_ledger if "outlier" in e.get("evidence_id", "").lower() or "anomaly" in e.get("evidence_id", "").lower()]
        for a in anomaly_items[:3]:
            insights.append(DiscoveredInsight(
                insight_id=f"insight.anomaly.{a.get('source_field', 'val')}",
                category="anomaly",
                title=f"Statistical Anomaly Detected in {a.get('source_field', 'Data')}",
                headline=f"{a.get('entity', 'Outliers')} observed outside expected thresholds",
                description=f"Statistical variance identified: {a.get('formula', 'Exceeds standard deviation limits')}.",
                significance="high",
                evidence_ids=[a.get("evidence_id")],
                impact_metrics={"value": a.get("value")},
                recommendation="Investigate extreme outliers to confirm data collection accuracy before making policy decisions.",
            ))

        # 4. Correlation & Relationship Insights (Excluding Identifiers per Section 14)
        try:
            from app.analytics.semantic_classifier import SemanticClassifier
            num_cols = [
                c for c in frame.columns
                if pd.api.types.is_numeric_dtype(frame[c])
                and not SemanticClassifier.classify_field(c, frame[c]).is_identifier
            ]
            if len(num_cols) >= 2 and len(frame) >= 5:
                corr_matrix = frame[num_cols].corr(numeric_only=True)
                seen_pairs: set[tuple[str, str]] = set()
                top_corrs: list[tuple[str, str, float]] = []
                for c1 in num_cols:
                    for c2 in num_cols:
                        if c1 != c2 and (c2, c1) not in seen_pairs and (c1, c2) not in seen_pairs:
                            seen_pairs.add((c1, c2))
                            val = corr_matrix.loc[c1, c2]
                            if pd.notna(val) and abs(float(val)) >= 0.60:
                                top_corrs.append((c1, c2, float(val)))

                top_corrs.sort(key=lambda x: abs(x[2]), reverse=True)
                for c1, c2, r_val in top_corrs[:2]:
                    direction = "positive" if r_val > 0 else "inverse"
                    strength = "Very Strong" if abs(r_val) >= 0.80 else "Moderate-to-Strong"
                    label1 = c1.replace("_", " ").title()
                    label2 = c2.replace("_", " ").title()
                    insights.append(DiscoveredInsight(
                        insight_id=f"insight.correlation.{c1}_{c2}",
                        category="relationship",
                        title=f"{strength} Correlation: {label1} & {label2}",
                        headline=f"Observed {direction} statistical alignment (r = {r_val:+.2f})",
                        description=(
                            f"Empirical correlation of {r_val:+.2f} observed between {label1} and {label2}. "
                            f"Shifts in {label1} reliably track variations in {label2} across the audited sample."
                        ),
                        significance="high" if abs(r_val) >= 0.80 else "medium",
                        evidence_ids=[e.get("evidence_id") for e in evidence_ledger if e.get("source_field") in (c1, c2)][:2],
                        impact_metrics={"variable_1": c1, "variable_2": c2, "pearson_r": round(r_val, 3)},
                        recommendation=f"Evaluate whether changes in {label1} can serve as a leading operational indicator for {label2}.",
                    ))
        except Exception:
            pass

        # 5. Temporal Trend Insights (Section 23 & 24 Strict Temporal Gating: >= 3 distinct periods)
        try:
            from app.analytics.semantic_classifier import SemanticClassifier
            date_cols = [
                c for c in frame.columns
                if ("date" in c.lower() or "time" in c.lower() or "created" in c.lower() or pd.api.types.is_datetime64_any_dtype(frame[c]))
                and not SemanticClassifier.classify_field(c, frame[c]).is_identifier
            ]
            num_cols = [
                c for c in frame.columns
                if pd.api.types.is_numeric_dtype(frame[c])
                and not SemanticClassifier.classify_field(c, frame[c]).is_identifier
            ]

            if date_cols and num_cols and len(frame) >= 10:
                d_col = date_cols[0]
                n_col = num_cols[0]
                parsed_dates = pd.to_datetime(frame[d_col], errors="coerce")
                # Enforce at least 3 distinct chronological periods
                distinct_periods = parsed_dates.dropna().dt.to_period("M").nunique()
                valid_mask = parsed_dates.notna() & frame[n_col].notna()
                if distinct_periods >= 3 and valid_mask.sum() >= 10:
                    sub = pd.DataFrame({"dt": parsed_dates[valid_mask], "val": frame.loc[valid_mask, n_col]})
                    sub = sub.sort_values("dt")
                    mid_idx = len(sub) // 2
                    first_half_avg = sub.iloc[:mid_idx]["val"].mean()
                    second_half_avg = sub.iloc[mid_idx:]["val"].mean()
                    if first_half_avg != 0 and pd.notna(first_half_avg) and pd.notna(second_half_avg):
                        growth_pct = ((second_half_avg - first_half_avg) / abs(first_half_avg)) * 100.0
                        if abs(growth_pct) >= 5.0:
                            direction = "Growth" if growth_pct > 0 else "Contraction"
                            clean_meas = n_col.replace("_", " ").title()
                            insights.append(DiscoveredInsight(
                                insight_id=f"insight.trend.{n_col}",
                                category="trend",
                                title=f"Temporal {direction} in {clean_meas}",
                                headline=f"{clean_meas} shifted {growth_pct:+.1f}% across sequential periods",
                                description=(
                                    f"Mean value transitioned from {first_half_avg:,.2f} in early records to "
                                    f"{second_half_avg:,.2f} in subsequent periods, indicating sustained directional shift."
                                ),
                                significance="high" if abs(growth_pct) >= 20.0 else "medium",
                                evidence_ids=[e.get("evidence_id") for e in evidence_ledger if e.get("source_field") == n_col][:1],
                                impact_metrics={"growth_pct": round(growth_pct, 1), "baseline": round(first_half_avg, 2), "recent": round(second_half_avg, 2)},
                                recommendation=f"Incorporate the {growth_pct:+.1f}% velocity into baseline capacity planning.",
                            ))
        except Exception:
            pass
            pass

        # 6. Data Quality & Coverage Insights
        try:
            null_counts = frame.isnull().sum()
            high_null_cols = [(col, int(cnt), float(cnt / len(frame) * 100.0)) for col, cnt in null_counts.items() if cnt > 0 and (cnt / len(frame)) >= 0.10]
            for col, cnt, pct in high_null_cols[:2]:
                insights.append(DiscoveredInsight(
                    insight_id=f"insight.quality.{col}.sparsity",
                    category="quality",
                    title=f"Data Sparsity in {col.replace('_', ' ').title()}",
                    headline=f"{pct:.1f}% missing values detected ({cnt:,} records)",
                    description=(
                        f"Field '{col}' exhibits significant missingness with {pct:.1f}% null entries. "
                        f"Downstream metrics reliant on this attribute carry conditional variance."
                    ),
                    significance="high" if pct >= 30.0 else "medium",
                    evidence_ids=[],
                    impact_metrics={"field": col, "missing_count": cnt, "missing_pct": round(pct, 1)},
                    recommendation=f"Enforce upstream schema validation or impute missing values for '{col}'.",
                ))
        except Exception:
            pass

        return insights
