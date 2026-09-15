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


def _num(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[col], errors="coerce").dropna()


class FinanceAnalytics:
    """Computes financial reporting metrics for budgets, expenses, and ledger entries."""

    @classmethod
    def analyze(
        cls, frame: pd.DataFrame
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        expense_series = _num(frame, "expense")
        budget_series = _num(frame, "budget")
        rev_series = _num(frame, "revenue")

        total_expense = float(expense_series.sum()) if not expense_series.empty else None
        total_budget = float(budget_series.sum()) if not budget_series.empty else None
        total_rev = float(rev_series.sum()) if not rev_series.empty else None

        burn_pct = (
            (total_expense / total_budget * 100)
            if total_expense is not None and total_budget and total_budget > 0
            else None
        )

        kpis: list[ReportMetric] = [
            ReportMetric(
                id="total_expense",
                name="Total Expenditures",
                value=round(total_expense, 2) if total_expense is not None else None,
                formatted_value=format_value(total_expense, "currency"),
                unit="currency",
                description="Cumulative corporate expenditure across accounts",
                priority=1,
                category="financial",
                available=total_expense is not None,
            ),
            ReportMetric(
                id="total_budget",
                name="Allocated Budget",
                value=round(total_budget, 2) if total_budget is not None else None,
                formatted_value=format_value(total_budget, "currency"),
                unit="currency",
                description="Approved expenditure ceiling",
                priority=2,
                category="financial",
                available=total_budget is not None,
            ),
            ReportMetric(
                id="budget_utilization",
                name="Budget Utilization",
                value=round(burn_pct, 1) if burn_pct is not None else None,
                formatted_value=format_value(burn_pct, "percent"),
                unit="percent",
                description="Percentage of allocated budget consumed to date",
                priority=3,
                category="financial",
                status="warning" if (burn_pct or 0) > 90 else "positive",
                available=burn_pct is not None,
            ),
        ]

        sections: list[ReportSection] = []
        charts: list[ChartDefinition] = []
        if "category" in frame.columns and total_expense is not None:
            c = ChartBuilder.group_metric_comparison(
                frame, "category", "expense", "Expenditures by Cost Center", "fin_cost_center", agg="sum", unit="currency"
            )
            if c:
                charts.append(c)

        sections.append(
            ReportSection(
                id="financial_overview",
                title="Financial Governance & Budgetary Tracking",
                description="Monitoring of cost centers, expenditure distribution, and variance against authorized caps.",
                metrics=kpis,
                charts=charts,
            )
        )

        anomalies: list[ReportAnomaly] = []
        if burn_pct and burn_pct > 100.0:
            anomalies.append(
                ReportAnomaly(
                    id="fin_overbudget",
                    metric="budget_utilization",
                    label="Budget Overrun Detected",
                    value=f"{burn_pct:.1f}%",
                    expected="<= 100.0%",
                    severity="high",
                    reason="Operating expenses have eclipsed total allocated budgetary provisions.",
                )
            )

        recommendations = [
            ReportRecommendation(
                id="rec_fin_audit",
                title="Freeze Discretionary Spend",
                description="Rebalance cost allocations for accounts exceeding 85% run-rate projection.",
                priority="high",
                category="financial",
            )
        ]

        return kpis, sections, anomalies, recommendations
