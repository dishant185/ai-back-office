from __future__ import annotations

import pandas as pd
from app.reporting.chart_builder import ChartBuilder
from app.reporting.formatter import format_value
from app.reporting.models import (
    ChartDefinition,
    ReportAnomaly,
    ReportMetric,
    ReportRanking,
    ReportRecommendation,
    ReportSection,
)


def _num_series(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[col], errors="coerce").dropna()


class SalesAnalytics:
    """Computes comprehensive metrics, sections, anomalies, and recommendations for Sales data."""

    @classmethod
    def analyze(
        cls,
        frame: pd.DataFrame,
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        row_count = int(len(frame.index))
        if row_count == 0:
            return [], [], [], []

        rev_series = _num_series(frame, "revenue")
        profit_series = _num_series(frame, "profit")
        qty_series = _num_series(frame, "quantity")

        total_revenue = float(rev_series.sum()) if not rev_series.empty else None
        total_profit = float(profit_series.sum()) if not profit_series.empty else None
        total_qty = float(qty_series.sum()) if not qty_series.empty else None

        margin_pct = (
            (total_profit / total_revenue * 100)
            if total_profit is not None and total_revenue and total_revenue > 0
            else None
        )

        aov = (total_revenue / row_count) if total_revenue is not None and row_count > 0 else None

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="total_revenue",
                name="Gross Revenue",
                value=round(total_revenue, 2) if total_revenue is not None else None,
                formatted_value=format_value(total_revenue, "currency"),
                unit="currency",
                description="Total aggregate sales revenue",
                priority=1,
                category="financial",
                status="positive" if total_revenue and total_revenue > 0 else "neutral",
                available=total_revenue is not None,
            ),
            ReportMetric(
                id="total_profit",
                name="Net Profit",
                value=round(total_profit, 2) if total_profit is not None else None,
                formatted_value=format_value(total_profit, "currency"),
                unit="currency",
                description="Cumulative operating profit generated",
                priority=2,
                category="financial",
                status="positive" if total_profit and total_profit > 0 else "warning",
                available=total_profit is not None,
            ),
            ReportMetric(
                id="profit_margin",
                name="Operating Margin",
                value=round(margin_pct, 2) if margin_pct is not None else None,
                formatted_value=format_value(margin_pct, "percent"),
                unit="percent",
                description="Net profit percentage of total revenue",
                priority=3,
                category="financial",
                status="positive" if (margin_pct or 0) > 15 else "neutral",
                available=margin_pct is not None,
            ),
            ReportMetric(
                id="avg_order_value",
                name="Average Order Value",
                value=round(aov, 2) if aov is not None else None,
                formatted_value=format_value(aov, "currency"),
                unit="currency",
                description="Mean revenue generated per transaction",
                priority=4,
                category="performance",
                available=aov is not None,
            ),
            ReportMetric(
                id="total_volume",
                name="Units Sold",
                value=int(total_qty) if total_qty is not None else None,
                formatted_value=format_value(total_qty, "units"),
                unit="units",
                description="Total unit volume moved across catalog",
                priority=5,
                category="volume",
                available=total_qty is not None,
            ),
        ]

        sections: list[ReportSection] = []

        # SECTION 1: Product & Category Revenue
        sales_charts: list[ChartDefinition] = []
        if "category" in frame.columns and total_revenue is not None:
            c = ChartBuilder.group_metric_comparison(
                frame, "category", "revenue", "Revenue by Product Category", "sales_cat_rev", agg="sum", unit="currency"
            )
            if c:
                sales_charts.append(c)

        if "order_date" in frame.columns and total_revenue is not None:
            c = ChartBuilder.time_series(
                frame, "order_date", "revenue", "Revenue Over Time", "sales_rev_trend", agg="sum", unit="currency"
            )
            if c:
                sales_charts.append(c)

        rankings: list[ReportRanking] = []
        if "product" in frame.columns and total_revenue is not None:
            r = ChartBuilder.build_ranking(
                frame, "product", "revenue", "Top Products by Revenue", "sales_top_products", agg="sum", unit="currency"
            )
            if r:
                rankings.append(r)

        if "region" in frame.columns and total_revenue is not None:
            r = ChartBuilder.build_ranking(
                frame, "region", "revenue", "Top Geographic Regions", "sales_top_regions", agg="sum", unit="currency"
            )
            if r:
                rankings.append(r)

        sections.append(
            ReportSection(
                id="revenue_performance",
                title="Revenue & Commercial Performance",
                description="Evaluation of revenue streams, profit margins, product category shares, and regional execution.",
                metrics=[m for m in kpis if m.id in ("total_revenue", "total_profit", "profit_margin")],
                charts=sales_charts,
                rankings=rankings,
                callout=f"Total gross revenue generated stands at {format_value(total_revenue, 'currency')}{f' with an overall profit margin of {margin_pct:.1f}%' if margin_pct else ''}." if total_revenue else None,
            )
        )

        anomalies: list[ReportAnomaly] = []
        if margin_pct is not None and margin_pct < 5.0:
            anomalies.append(
                ReportAnomaly(
                    id="sales_low_margin",
                    metric="profit_margin",
                    label="Sub-optimal Margin Threshold",
                    value=f"{margin_pct:.1f}%",
                    expected="> 10.0%",
                    severity="high",
                    reason="Operating margin is critically compressed, likely due to deep discounts or elevated COGS.",
                )
            )

        recommendations: list[ReportRecommendation] = [
            ReportRecommendation(
                id="rec_sales_upsell",
                title="Double Down on High-Contribution SKUs",
                description="Shift marketing allocation toward the top 20% revenue-generating product catalog.",
                priority="high",
                category="optimization",
            )
        ]

        return kpis, sections, anomalies, recommendations
