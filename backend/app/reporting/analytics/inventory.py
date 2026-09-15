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


class InventoryAnalytics:
    """Computes warehouse and inventory tracking metrics."""

    @classmethod
    def analyze(
        cls, frame: pd.DataFrame
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        stock_s = pd.to_numeric(frame.get("stock_quantity", pd.Series(dtype="float64")), errors="coerce").dropna()
        total_stock = float(stock_s.sum()) if not stock_s.empty else None
        sku_count = int(len(frame.index))

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="total_stock",
                name="Total Stock On Hand",
                value=int(total_stock) if total_stock is not None else None,
                formatted_value=format_value(total_stock, "units"),
                unit="units",
                description="Cumulative physical inventory units stored across warehouses",
                priority=1,
                category="inventory",
                available=total_stock is not None,
            ),
            ReportMetric(
                id="total_skus",
                name="Tracked SKUs",
                value=sku_count,
                formatted_value=format_value(sku_count, "items"),
                unit="items",
                description="Unique product variants in inventory catalogue",
                priority=2,
                category="inventory",
            ),
        ]

        sections: list[ReportSection] = []
        charts: list[ChartDefinition] = []
        if "category" in frame.columns and total_stock is not None:
            c = ChartBuilder.group_metric_comparison(
                frame, "category", "stock_quantity", "Stock by Product Category", "inv_cat_stock", agg="sum", unit="units"
            )
            if c:
                charts.append(c)

        sections.append(
            ReportSection(
                id="inventory_tracking",
                title="Inventory & Stock Health",
                description="Analysis of on-hand reserves, safety stock levels, and supply chain readiness.",
                metrics=kpis,
                charts=charts,
            )
        )

        anomalies: list[ReportAnomaly] = []
        recommendations: list[ReportRecommendation] = [
            ReportRecommendation(
                id="rec_inv_reorder",
                title="Optimize Reorder Point Triggers",
                description="Recalibrate safety thresholds based on supplier lead times and moving demand averages.",
                priority="medium",
                category="operational",
            )
        ]

        return kpis, sections, anomalies, recommendations
