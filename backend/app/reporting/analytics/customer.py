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


class CustomerAnalytics:
    """Computes customer cohort, retention, and segmentation intelligence."""

    @classmethod
    def analyze(
        cls, frame: pd.DataFrame
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        total_customers = int(len(frame.index))

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="customer_count",
                name="Total Customer Base",
                value=total_customers,
                formatted_value=format_value(total_customers, "customers"),
                unit="customers",
                description="Total unique active and archived customer records",
                priority=1,
                category="growth",
            )
        ]

        sections: list[ReportSection] = []
        charts: list[ChartDefinition] = []
        if "customer_type" in frame.columns:
            c = ChartBuilder.categorical_distribution(
                frame, "customer_type", "Customer Segmentation", "cust_segment_dist"
            )
            if c:
                charts.append(c)

        sections.append(
            ReportSection(
                id="customer_segmentation",
                title="Customer Segmentation & Cohort Analysis",
                description="Distribution of customer demographics, loyalty tiers, and account classifications.",
                metrics=kpis,
                charts=charts,
            )
        )

        return kpis, sections, [], []
