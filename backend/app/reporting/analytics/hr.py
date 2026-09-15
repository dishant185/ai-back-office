from __future__ import annotations

from typing import Any
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


def _safe_numeric_series(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[col], errors="coerce").dropna()


def _binary_flag_series(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    s = frame[col].dropna()
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").dropna()
    # If text like 'Yes'/'No'
    s_lower = s.astype(str).str.strip().str.lower()
    mapping = {"yes": 1, "y": 1, "true": 1, "1": 1, "1.0": 1, "left": 1, "resigned": 1}
    return s_lower.map(lambda x: mapping.get(x, 0))


class HRAnalytics:
    """Computes comprehensive metrics, sections, anomalies, and recommendations for HR data."""

    @classmethod
    def analyze(
        cls,
        frame: pd.DataFrame,
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        employee_count = int(len(frame.index))
        if employee_count == 0:
            return [], [], [], []

        age_series = _safe_numeric_series(frame, "age")
        joining_series = _safe_numeric_series(frame, "joining_year")
        leave_series = _binary_flag_series(frame, "leave_or_not")
        bench_series = _binary_flag_series(frame, "ever_benched")
        exp_series = _safe_numeric_series(frame, "experience_in_current_domain")

        # 1. Core KPIs
        avg_age = float(age_series.mean()) if not age_series.empty else None
        avg_joining_year = float(joining_series.mean()) if not joining_series.empty else None

        employees_left = int(leave_series.sum()) if not leave_series.empty else None
        employees_retained = (employee_count - employees_left) if employees_left is not None else None
        attrition_rate = (
            float((employees_left / employee_count) * 100)
            if employees_left is not None and employee_count > 0
            else None
        )

        avg_exp = float(exp_series.mean()) if not exp_series.empty else None
        benched_count = int(bench_series.sum()) if not bench_series.empty else None
        benched_pct = (
            float((benched_count / employee_count) * 100)
            if benched_count is not None and employee_count > 0
            else None
        )

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="employee_count",
                name="Total Workforce",
                value=employee_count,
                formatted_value=format_value(employee_count, "people"),
                unit="people",
                description="Total active and historical workforce records",
                priority=1,
                category="headcount",
                status="neutral",
            ),
            ReportMetric(
                id="attrition_rate",
                name="Attrition Rate",
                value=round(attrition_rate, 2) if attrition_rate is not None else None,
                formatted_value=format_value(attrition_rate, "percent"),
                unit="percent",
                description="Proportion of employees who have left the organization",
                priority=2,
                category="retention",
                status="warning" if (attrition_rate or 0) > 20 else "positive",
                available=attrition_rate is not None,
            ),
            ReportMetric(
                id="average_age",
                name="Average Age",
                value=round(avg_age, 1) if avg_age is not None else None,
                formatted_value=format_value(avg_age, "years"),
                unit="years",
                description="Mean age across employee demographics",
                priority=3,
                category="demographics",
                status="neutral",
                available=avg_age is not None,
                unavailability_reason="Age field missing or not numeric" if avg_age is None else None,
            ),
            ReportMetric(
                id="avg_experience",
                name="Avg Domain Experience",
                value=round(avg_exp, 1) if avg_exp is not None else None,
                formatted_value=format_value(avg_exp, "years"),
                unit="years",
                description="Average tenure within current technical domain",
                priority=4,
                category="experience",
                status="neutral",
                available=avg_exp is not None,
            ),
            ReportMetric(
                id="employees_left",
                name="Employees Departed",
                value=employees_left,
                formatted_value=format_value(employees_left, "people"),
                unit="people",
                description="Total confirmed employee departures",
                priority=5,
                category="retention",
                status="warning" if (employees_left or 0) > 0 else "neutral",
                available=employees_left is not None,
            ),
            ReportMetric(
                id="employees_retained",
                name="Active Retained",
                value=employees_retained,
                formatted_value=format_value(employees_retained, "people"),
                unit="people",
                description="Active retained talent pool",
                priority=6,
                category="retention",
                status="positive",
                available=employees_retained is not None,
            ),
        ]

        # 2. Sections
        sections: list[ReportSection] = []

        # SECTION A: Workforce Demographics
        demographics_charts: list[ChartDefinition] = []
        if "education" in frame.columns:
            chart = ChartBuilder.categorical_distribution(
                frame, "education", "Workforce by Education Level", "hr_edu_dist"
            )
            if chart:
                demographics_charts.append(chart)

        if "gender" in frame.columns:
            chart = ChartBuilder.categorical_distribution(
                frame, "gender", "Gender Diversity Breakdown", "hr_gender_dist"
            )
            if chart:
                demographics_charts.append(chart)

        if "age" in frame.columns:
            chart = ChartBuilder.numeric_histogram(
                frame, "age", "Age Bracket Distribution", "hr_age_dist", bins=5, unit="people"
            )
            if chart:
                demographics_charts.append(chart)

        demographics_rankings: list[ReportRanking] = []
        if "city" in frame.columns:
            ranking = ChartBuilder.build_ranking(
                frame, "city", "city", "Headcount Distribution by City", "hr_city_rank", agg="count", unit="people"
            )
            if ranking:
                demographics_rankings.append(ranking)

        sections.append(
            ReportSection(
                id="workforce_demographics",
                title="Workforce Composition & Demographics",
                description="Comprehensive view of employee education levels, age cohorts, gender parity, and regional hubs.",
                metrics=[m for m in kpis if m.id in ("employee_count", "average_age", "avg_experience")],
                charts=demographics_charts,
                rankings=demographics_rankings,
                callout=f"The organization spans {len(frame['city'].unique()) if 'city' in frame.columns else 'multiple'} primary locations with an average workforce age of {avg_age:.1f} years." if avg_age else None,
            )
        )

        # SECTION B: Attrition Dynamics (if attrition data present)
        if attrition_rate is not None:
            attrition_charts: list[ChartDefinition] = []
            if "city" in frame.columns:
                c = ChartBuilder.rate_by_category(
                    frame, "city", "leave_or_not", "Attrition Rate by City (%)", "hr_attrition_city"
                )
                if c:
                    attrition_charts.append(c)

            if "payment_tier" in frame.columns:
                c = ChartBuilder.rate_by_category(
                    frame, "payment_tier", "leave_or_not", "Attrition Rate by Payment Tier (%)", "hr_attrition_tier"
                )
                if c:
                    attrition_charts.append(c)

            if "education" in frame.columns:
                c = ChartBuilder.rate_by_category(
                    frame, "education", "leave_or_not", "Attrition Rate by Education (%)", "hr_attrition_edu"
                )
                if c:
                    attrition_charts.append(c)

            sections.append(
                ReportSection(
                    id="attrition_retention",
                    title="Attrition & Retention Dynamics",
                    description="Detailed risk evaluation tracking turnover rates across compensation bands, educational backgrounds, and office locations.",
                    metrics=[m for m in kpis if m.id in ("attrition_rate", "employees_left", "employees_retained")],
                    charts=attrition_charts,
                    callout=f"Current organization-wide attrition rate stands at {attrition_rate:.1f}%, indicating critical retention pressure points in specific segments.",
                )
            )

        # SECTION C: Bench & Domain Experience
        if "experience_in_current_domain" in frame.columns or "ever_benched" in frame.columns:
            talent_charts: list[ChartDefinition] = []
            if "experience_in_current_domain" in frame.columns:
                c = ChartBuilder.categorical_distribution(
                    frame, "experience_in_current_domain", "Years in Current Domain", "hr_exp_dist"
                )
                if c:
                    talent_charts.append(c)

            if "ever_benched" in frame.columns:
                c = ChartBuilder.categorical_distribution(
                    frame, "ever_benched", "Bench History (Ever Benched)", "hr_bench_dist"
                )
                if c:
                    talent_charts.append(c)

            bench_metrics = []
            if benched_pct is not None:
                bench_metrics.append(
                    ReportMetric(
                        id="benched_pct",
                        name="Ever Benched Rate",
                        value=round(benched_pct, 1),
                        formatted_value=format_value(benched_pct, "percent"),
                        unit="percent",
                        description="Percentage of workforce with bench deployment history",
                        priority=7,
                        category="utilization",
                    )
                )

            sections.append(
                ReportSection(
                    id="talent_utilization",
                    title="Domain Experience & Resource Utilization",
                    description="Evaluation of staff experience distribution and talent bench deployment cycles.",
                    metrics=bench_metrics,
                    charts=talent_charts,
                )
            )

        # 3. Anomalies
        anomalies: list[ReportAnomaly] = []
        if attrition_rate and attrition_rate > 25.0:
            anomalies.append(
                ReportAnomaly(
                    id="hr_high_attrition",
                    metric="attrition_rate",
                    label="Elevated Workforce Attrition",
                    value=f"{attrition_rate:.1f}%",
                    expected="< 15.0%",
                    severity="high",
                    reason="Organization attrition rate exceeds industry target thresholds, signaling flight risk.",
                )
            )

        # Check for highest attrition city
        if "city" in frame.columns and "leave_or_not" in frame.columns:
            city_rates = frame.groupby("city")["leave_or_not"].mean() * 100
            for city_name, rate in city_rates.items():
                if rate > 40.0:
                    anomalies.append(
                        ReportAnomaly(
                            id=f"hr_city_attrition_{city_name}",
                            metric="city_attrition",
                            label=f"Spike in {city_name} Attrition",
                            value=f"{rate:.1f}%",
                            expected="< 25.0%",
                            severity="medium",
                            reason=f"Employees based in {city_name} exhibit significantly higher departure probabilities.",
                        )
                    )

        # 4. Recommendations
        recommendations: list[ReportRecommendation] = []
        if attrition_rate and attrition_rate > 20.0:
            recommendations.append(
                ReportRecommendation(
                    id="rec_retention_intervention",
                    title="Implement Targeted Retention Programs",
                    description="Conduct exit interviews and salary parity checks across highest-churn payment tiers and urban offices.",
                    priority="high",
                    category="retention",
                )
            )

        if benched_pct and benched_pct > 10.0:
            recommendations.append(
                ReportRecommendation(
                    id="rec_bench_reallocation",
                    title="Accelerate Bench-to-Billable Pipeline",
                    description="Establish proactive re-skilling tracks for unallocated personnel to prevent engagement decay.",
                    priority="medium",
                    category="optimization",
                )
            )

        recommendations.append(
            ReportRecommendation(
                id="rec_mid_level_nurturing",
                title="Develop Mid-Tenure Leadership Paths",
                description="Provide structured technical career progression for professionals with 2–5 years domain experience.",
                priority="low",
                category="operational",
            )
        )

        return kpis, sections, anomalies, recommendations
