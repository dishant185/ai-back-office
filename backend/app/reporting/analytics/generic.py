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


class GenericAnalytics:
    """Universal fallback analytics engine that creates rich intelligence from ANY tabular dataset."""

    @classmethod
    def analyze(
        cls, frame: pd.DataFrame, report_type: str = "standard"
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        row_count = int(len(frame.index))
        col_count = int(len(frame.columns))
        if row_count == 0:
            return [], [], [], []

        # Identify numeric and categorical columns
        numeric_cols = [
            c for c in frame.columns
            if pd.api.types.is_numeric_dtype(frame[c])
            and not str(c).lower().endswith("id")
            and frame[c].nunique() > 1
        ]
        categorical_cols = [
            c for c in frame.columns
            if (pd.api.types.is_object_dtype(frame[c]) or isinstance(frame[c].dtype, pd.CategoricalDtype))
            and frame[c].nunique() <= 30
        ]

        # 1. KPIs: Row count + top 3 numeric metrics
        kpis: list[ReportMetric] = [
            ReportMetric(
                id="record_count",
                name="Total Records",
                value=row_count,
                formatted_value=format_value(row_count, "count"),
                unit="count",
                description="Total observations in analyzed dataset",
                priority=1,
                category="volume",
            )
        ]

        for idx, col in enumerate(numeric_cols[:4], start=2):
            s = pd.to_numeric(frame[col], errors="coerce").dropna()
            if s.empty:
                continue
            mean_val = float(s.mean())
            clean_name = str(col).replace("_", " ").title()
            kpis.append(
                ReportMetric(
                    id=f"metric_{col}_mean",
                    name=f"Avg {clean_name}",
                    value=round(mean_val, 2),
                    formatted_value=format_value(mean_val),
                    unit="value",
                    description=f"Mean value across {clean_name}",
                    priority=idx,
                    category="numeric",
                )
            )

        # 2. Sections
        sections: list[ReportSection] = []

        # SECTION 1: Categorical Distributions
        dist_charts: list[ChartDefinition] = []
        for col in categorical_cols[:3]:
            clean_name = str(col).replace("_", " ").title()
            c = ChartBuilder.categorical_distribution(
                frame, str(col), f"Distribution by {clean_name}", f"gen_cat_{col}"
            )
            if c:
                dist_charts.append(c)

        rankings: list[ReportRanking] = []
        if categorical_cols and numeric_cols:
            primary_cat = categorical_cols[0]
            primary_num = numeric_cols[0]
            r = ChartBuilder.build_ranking(
                frame,
                primary_cat,
                primary_num,
                f"Top {str(primary_cat).replace('_', ' ').title()} by Total {str(primary_num).replace('_', ' ').title()}",
                f"gen_rank_{primary_cat}",
                agg="sum",
            )
            if r:
                rankings.append(r)

        if dist_charts or rankings:
            sections.append(
                ReportSection(
                    id="categorical_breakdown",
                    title="Segment & Dimension Breakdown",
                    description="Analysis of unique classes, categorical frequencies, and categorical performance.",
                    metrics=[kpis[0]],
                    charts=dist_charts,
                    rankings=rankings,
                )
            )

        # SECTION 2: Numeric Metrics & Spread
        num_charts: list[ChartDefinition] = []
        for col in numeric_cols[:2]:
            clean_name = str(col).replace("_", " ").title()
            c = ChartBuilder.numeric_histogram(
                frame, str(col), f"{clean_name} Distribution", f"gen_hist_{col}", bins=5
            )
            if c:
                num_charts.append(c)

        if num_charts:
            sections.append(
                ReportSection(
                    id="numeric_spread",
                    title="Numerical Value Distributions",
                    description="Histograms and concentration curves showing variable dispersion across records.",
                    metrics=[m for m in kpis if m.category == "numeric"],
                    charts=num_charts,
                )
            )

        # 3. Outlier / Anomaly Detection using standard deviations
        anomalies: list[ReportAnomaly] = []
        for col in numeric_cols[:2]:
            s = pd.to_numeric(frame[col], errors="coerce").dropna()
            if len(s) > 10 and s.std() > 0:
                mean = s.mean()
                std = s.std()
                high_threshold = mean + 3 * std
                outliers = s[s > high_threshold]
                if not outliers.empty:
                    clean_name = str(col).replace("_", " ").title()
                    anomalies.append(
                        ReportAnomaly(
                            id=f"gen_outlier_{col}",
                            metric=str(col),
                            label=f"Statistical Outliers in {clean_name}",
                            value=f"{len(outliers)} record(s)",
                            expected=f"<= {high_threshold:.1f}",
                            severity="medium",
                            reason=f"Records exceed 3 standard deviations above the mean for {clean_name}.",
                        )
                    )

        # 4. Recommendations
        recommendations: list[ReportRecommendation] = [
            ReportRecommendation(
                id="rec_gen_quality",
                title="Establish Data Standardization Rules",
                description="Automate schema validation during intake to maintain format consistency.",
                priority="medium",
                category="operational",
            )
        ]

        return kpis, sections, anomalies, recommendations
