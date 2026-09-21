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
        report_type: str = "standard",
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        row_count = int(len(frame.index))
        if row_count == 0:
            return [], [], [], []

        # Find columns dynamically
        rev_col = next((c for c in ["revenue", "sales", "amount", "sales_amount"] if c in frame.columns), "revenue")
        profit_col = next((c for c in ["profit", "margin", "gross_profit", "net_profit"] if c in frame.columns), "profit")
        qty_col = next((c for c in ["quantity", "units_sold", "units", "qty"] if c in frame.columns), "quantity")
        cat_col = next((c for c in ["category", "product_category", "segment", "department"] if c in frame.columns), None)
        prod_col = next((c for c in ["product", "sku", "item", "product_name"] if c in frame.columns), None)
        region_col = next((c for c in ["region", "territory", "city", "location", "market"] if c in frame.columns), None)
        cust_col = next((c for c in ["customer_name", "customer_id", "client_name", "account_name"] if c in frame.columns), None)
        disc_col = next((c for c in ["discount", "discount_pct", "discount_amount"] if c in frame.columns), None)
        pay_col = next((c for c in ["payment_method", "payment_tier", "payment", "payment_type"] if c in frame.columns), None)
        date_col = next((c for c in ["order_date", "transaction_date", "date", "created_at"] if c in frame.columns), None)

        rev_series = _num_series(frame, rev_col)
        profit_series = _num_series(frame, profit_col)
        qty_series = _num_series(frame, qty_col)
        disc_series = _num_series(frame, disc_col) if disc_col else pd.Series(dtype="float64")

        total_revenue = float(rev_series.sum()) if not rev_series.empty else None
        total_profit = float(profit_series.sum()) if not profit_series.empty else None
        total_qty = float(qty_series.sum()) if not qty_series.empty else None

        margin_pct = (
            (total_profit / total_revenue * 100)
            if total_profit is not None and total_revenue and total_revenue > 0
            else None
        )
        aov = (total_revenue / row_count) if total_revenue is not None and row_count > 0 else None

        rpt = (report_type or "standard").lower()

        # SPECIALIZED: Regional Sales
        if rpt in ("regional_sales", "regional"):
            top_region_name = "N/A"
            top_region_rev = 0
            top_region_share = 0
            if region_col and total_revenue:
                reg_grouped = frame.groupby(region_col)[rev_col].sum().sort_values(ascending=False)
                if not reg_grouped.empty:
                    top_region_name = str(reg_grouped.index[0])
                    top_region_rev = float(reg_grouped.iloc[0])
                    top_region_share = (top_region_rev / total_revenue * 100)

            kpis = [
                ReportMetric(
                    id="total_revenue",
                    name="Gross Revenue",
                    value=round(total_revenue, 2) if total_revenue is not None else None,
                    formatted_value=format_value(total_revenue, "currency"),
                    unit="currency",
                    description="Total sales across all territories",
                    priority=1,
                    category="financial",
                    status="positive",
                ),
                ReportMetric(
                    id="top_region_revenue",
                    name="Lead Region Sales",
                    value=round(top_region_rev, 2) if top_region_rev > 0 else None,
                    formatted_value=format_value(top_region_rev, "currency"),
                    unit="currency",
                    description=f"Revenue generated in {top_region_name}",
                    priority=2,
                    category="regional",
                ),
                ReportMetric(
                    id="top_region_share",
                    name="Lead Region Contribution",
                    value=round(top_region_share, 1),
                    formatted_value=f"{top_region_share:.1f}% ({top_region_name})",
                    unit="percent",
                    description="Share of total business in primary territory",
                    priority=3,
                    category="regional",
                ),
                ReportMetric(
                    id="active_regions",
                    name="Active Territories",
                    value=frame[region_col].nunique() if region_col else None,
                    formatted_value=f"{frame[region_col].nunique()} Markets" if region_col else "N/A",
                    unit="markets",
                    description="Discrete geographical markets tracked",
                    priority=4,
                    category="regional",
                ),
            ]

            sections = []
            reg_charts = []
            if region_col and total_revenue:
                c = ChartBuilder.group_metric_comparison(
                    frame, region_col, rev_col, "Regional Revenue Contribution", "sales_reg_bar", agg="sum", unit="currency"
                )
                if c:
                    reg_charts.append(c)

            reg_rankings = []
            if region_col and total_revenue:
                r = ChartBuilder.build_ranking(
                    frame, region_col, rev_col, "Territory Revenue Leaderboard", "sales_reg_table", agg="sum", unit="currency"
                )
                if r:
                    reg_rankings.append(r)

            sections.append(ReportSection(
                id="regional_breakdown",
                title="Geographic Revenue & Territory Performance",
                description="Analysis of market penetration, territory contributions, and geographical concentration.",
                charts=reg_charts,
                rankings=reg_rankings,
                callout=f"Regional revenue is spearheaded by {top_region_name}, contributing {top_region_share:.1f}% of aggregate commercial turnover.",
            ))

            anomalies = []
            if top_region_share > 60:
                anomalies.append(ReportAnomaly(
                    id="sales_geo_concentration",
                    metric="top_region_share",
                    label="Geographic Revenue Concentration",
                    value=f"{top_region_share:.1f}%",
                    expected="< 45.0%",
                    severity="medium",
                    reason=f"High reliance on {top_region_name} introduces territory vulnerability.",
                ))

            recommendations = [
                ReportRecommendation(
                    id="rec_geo_expansion",
                    title="Scale Investment in Emerging Territories",
                    description="Reallocate channel marketing to under-penetrated secondary regions to diversify revenue base.",
                    priority="high",
                    category="financial",
                )
            ]
            return kpis, sections, anomalies, recommendations

        # SPECIALIZED: Product Performance
        if rpt in ("product_performance", "product"):
            sku_count = frame[prod_col].nunique() if prod_col else 0
            top_sku_name = "N/A"
            top_sku_rev = 0
            if prod_col and total_revenue:
                p_grouped = frame.groupby(prod_col)[rev_col].sum().sort_values(ascending=False)
                if not p_grouped.empty:
                    top_sku_name = str(p_grouped.index[0])
                    top_sku_rev = float(p_grouped.iloc[0])

            kpis = [
                ReportMetric(
                    id="total_revenue",
                    name="Gross Sales Revenue",
                    value=round(total_revenue, 2) if total_revenue is not None else None,
                    formatted_value=format_value(total_revenue, "currency"),
                    unit="currency",
                    description="Aggregate portfolio commercial revenue",
                    priority=1,
                    category="financial",
                    status="positive",
                ),
                ReportMetric(
                    id="catalog_skus",
                    name="Active Catalog SKUs",
                    value=sku_count,
                    formatted_value=f"{sku_count} SKUs",
                    unit="skus",
                    description="Total commercial products moved",
                    priority=2,
                    category="volume",
                ),
                ReportMetric(
                    id="top_sku_sales",
                    name="Top SKU Revenue",
                    value=round(top_sku_rev, 2) if top_sku_rev > 0 else None,
                    formatted_value=format_value(top_sku_rev, "currency"),
                    unit="currency",
                    description=f"Best-performing product: {top_sku_name}",
                    priority=3,
                    category="product",
                ),
                ReportMetric(
                    id="total_volume",
                    name="Aggregate Units Sold",
                    value=int(total_qty) if total_qty else None,
                    formatted_value=format_value(total_qty, "units"),
                    unit="units",
                    description="Total item volume fulfilled",
                    priority=4,
                    category="volume",
                ),
            ]

            sections = []
            prod_charts = []
            if prod_col and total_revenue:
                c = ChartBuilder.group_metric_comparison(
                    frame, prod_col, rev_col, "Top Products by Sales Volume", "sales_top_sku_bar", agg="sum", max_groups=8, unit="currency"
                )
                if c:
                    prod_charts.append(c)

            prod_rankings = []
            if prod_col and total_revenue:
                r = ChartBuilder.build_ranking(
                    frame, prod_col, rev_col, "Product Revenue Ranking", "sales_prod_rank_tbl", agg="sum", top_n=8, unit="currency"
                )
                if r:
                    prod_rankings.append(r)

            sections.append(ReportSection(
                id="product_performance_sec",
                title="Product Catalog & SKU Velocity Analysis",
                description="Detailed unit economics, top-selling items, and catalog revenue distribution.",
                charts=prod_charts,
                rankings=prod_rankings,
                callout=f"Leading product is '{top_sku_name}' generating {format_value(top_sku_rev, 'currency')} across audited transactions.",
            ))

            anomalies = []
            recommendations = [
                ReportRecommendation(
                    id="rec_sku_rationalization",
                    title="Optimize Underperforming Catalog SKUs",
                    description="Audit long-tail SKUs with negligible revenue contribution to eliminate warehousing carrying costs.",
                    priority="medium",
                    category="optimization",
                )
            ]
            return kpis, sections, anomalies, recommendations

        # DEFAULT: Standard Sales Overview
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
        sales_charts: list[ChartDefinition] = []
        if cat_col and total_revenue is not None:
            c = ChartBuilder.group_metric_comparison(
                frame, cat_col, rev_col, "Revenue by Product Category", "sales_cat_rev", agg="sum", unit="currency"
            )
            if c:
                sales_charts.append(c)

        if date_col and total_revenue is not None:
            c = ChartBuilder.time_series(
                frame, date_col, rev_col, f"{rev_col.replace('_', ' ').title()} Over Time", "sales_rev_trend", agg="sum", unit="currency"
            )
            if c:
                sales_charts.append(c)

        rankings: list[ReportRanking] = []
        if prod_col and total_revenue is not None:
            r = ChartBuilder.build_ranking(
                frame, prod_col, rev_col, "Top Products by Revenue", "sales_top_products", agg="sum", unit="currency"
            )
            if r:
                rankings.append(r)

        if region_col and total_revenue is not None:
            r = ChartBuilder.build_ranking(
                frame, region_col, rev_col, "Top Geographic Regions", "sales_top_regions", agg="sum", unit="currency"
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

        # Recommendations (Strictly Report-Specific & Evidence-Grounded)
        rpt = (report_type or "standard").lower()
        recommendations: list[ReportRecommendation] = []
        if anomalies:
            for anom in anomalies:
                recommendations.append(ReportRecommendation(
                    id=f"rec_anom_{anom.id}",
                    title=f"Address {anom.label}",
                    description=anom.reason,
                    priority=anom.severity,
                    category="risk_mitigation",
                ))
        elif rpt in ("regional_sales", "regional_performance"):
            recommendations.append(ReportRecommendation(
                id="rec_regional_gap",
                title="Review Regional Performance Disparities",
                description="Examine commercial factors contributing to the revenue gap between leading and trailing territories.",
                priority="medium",
                category="commercial_strategy",
            ))
        elif rpt in ("product_performance",):
            recommendations.append(ReportRecommendation(
                id="rec_product_portfolio",
                title="Optimize Product Catalog Focus",
                description="Align promotional allocation and supply chain prioritization with top-contributing SKUs.",
                priority="medium",
                category="portfolio_management",
            ))
        elif rpt in ("category_performance",):
            recommendations.append(ReportRecommendation(
                id="rec_category_mix",
                title="Evaluate Category Contribution",
                description="Review merchandise allocation across high-share product categories.",
                priority="low",
                category="merchandising",
            ))
        elif rpt in ("customer_analysis",):
            recommendations.append(ReportRecommendation(
                id="rec_customer_concentration",
                title="Monitor Account Concentration",
                description="Evaluate revenue dependency across primary customer accounts.",
                priority="medium",
                category="account_management",
            ))
        else:
            recommendations.append(ReportRecommendation(
                id="rec_sales_baseline",
                title="Maintain Commercial Performance Tracking",
                description="Continue tracking core revenue, transaction volumes, and transaction values against targets.",
                priority="low",
                category="commercial_operations",
            ))

        return kpis, sections, anomalies, recommendations
