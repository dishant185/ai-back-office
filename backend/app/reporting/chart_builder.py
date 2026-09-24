from __future__ import annotations

from typing import Any
import pandas as pd
from app.reporting.formatter import format_value
from app.reporting.models import ChartDefinition, RankingItem, ReportRanking


class ChartBuilder:
    """Utility to generate rich chart and ranking specifications from DataFrame slices."""

    @classmethod
    def categorical_distribution(
        cls,
        frame: pd.DataFrame,
        category_col: str,
        title: str,
        chart_id: str,
        max_categories: int = 8,
        donut_threshold: int = 6,
    ) -> ChartDefinition | None:
        if category_col not in frame.columns:
            return None

        counts = frame[category_col].dropna().value_counts()
        if counts.empty:
            return None

        total = counts.sum()
        top_counts = counts.head(max_categories)

        data: list[dict[str, Any]] = []
        for cat, cnt in top_counts.items():
            pct = (cnt / total * 100) if total > 0 else 0
            data.append({
                "label": str(cat),
                "value": int(cnt),
                "percentage": round(pct, 1),
            })

        # Donut if <= 6 categories, otherwise bar chart
        chart_type = "donut" if len(data) <= donut_threshold else "bar"

        return ChartDefinition(
            id=chart_id,
            title=title,
            chart_type=chart_type,
            data=data,
            x_key="label",
            y_key="value",
            unit="count",
        )

    @classmethod
    def group_metric_comparison(
        cls,
        frame: pd.DataFrame,
        group_col: str,
        metric_col: str,
        title: str,
        chart_id: str,
        agg: str = "mean",  # mean, sum, count
        chart_type: str = "bar",
        max_groups: int = 10,
        unit: str | None = None,
    ) -> ChartDefinition | None:
        if group_col not in frame.columns or metric_col not in frame.columns:
            return None

        clean_sub = frame[[group_col, metric_col]].dropna().copy()
        clean_sub[metric_col] = pd.to_numeric(clean_sub[metric_col], errors="coerce")
        clean_sub = clean_sub.dropna()

        if clean_sub.empty:
            return None

        if agg == "sum":
            grouped = clean_sub.groupby(group_col)[metric_col].sum()
        elif agg == "count":
            grouped = clean_sub.groupby(group_col)[metric_col].count()
        else:
            grouped = clean_sub.groupby(group_col)[metric_col].mean()

        grouped = grouped.sort_values(ascending=False).head(max_groups)

        data = [
            {"label": str(grp), "value": round(float(val), 2)}
            for grp, val in grouped.items()
        ]

        return ChartDefinition(
            id=chart_id,
            title=title,
            chart_type=chart_type,
            data=data,
            x_key="label",
            y_key="value",
            unit=unit,
        )

    @classmethod
    def ranking_bar(
        cls,
        frame: pd.DataFrame,
        group_col: str,
        metric_col: str,
        title: str,
        chart_id: str,
        max_groups: int = 8,
    ) -> ChartDefinition | None:
        return cls.group_metric_comparison(
            frame=frame,
            group_col=group_col,
            metric_col=metric_col,
            title=title,
            chart_id=chart_id,
            agg="sum",
            max_groups=max_groups,
        )

    @classmethod
    def rate_by_category(
        cls,
        frame: pd.DataFrame,
        category_col: str,
        flag_col: str,
        title: str,
        chart_id: str,
        chart_type: str = "bar",
    ) -> ChartDefinition | None:
        """Calculates percentage rate of a binary 0/1 flag grouped by category."""
        if category_col not in frame.columns or flag_col not in frame.columns:
            return None

        clean_sub = frame[[category_col, flag_col]].dropna().copy()
        clean_sub[flag_col] = pd.to_numeric(clean_sub[flag_col], errors="coerce")
        clean_sub = clean_sub.dropna()

        if clean_sub.empty:
            return None

        rates = clean_sub.groupby(category_col)[flag_col].mean() * 100
        rates = rates.sort_values(ascending=False)

        data = [
            {"label": str(cat), "value": round(float(rate), 2)}
            for cat, rate in rates.items()
        ]

        return ChartDefinition(
            id=chart_id,
            title=title,
            chart_type=chart_type,
            data=data,
            x_key="label",
            y_key="value",
            unit="percent",
        )

    @classmethod
    def time_series(
        cls,
        frame: pd.DataFrame,
        date_col: str,
        metric_col: str,
        title: str,
        chart_id: str,
        agg: str = "count",
        chart_type: str = "line",
        unit: str | None = None,
    ) -> ChartDefinition | None:
        if date_col not in frame.columns:
            return None

        sub = frame.dropna(subset=[date_col]).copy()
        if sub.empty:
            return None

        if agg == "count" or metric_col not in frame.columns:
            grouped = sub.groupby(date_col).size()
        else:
            sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
            grouped = sub.groupby(date_col)[metric_col].sum()

        grouped = grouped.sort_index()

        data = [
            {"label": str(dt), "value": round(float(val), 2)}
            for dt, val in grouped.items()
        ]

        return ChartDefinition(
            id=chart_id,
            title=title,
            chart_type=chart_type,
            data=data,
            x_key="label",
            y_key="value",
            unit=unit,
        )

    @classmethod
    def numeric_histogram(
        cls,
        frame: pd.DataFrame,
        numeric_col: str,
        title: str,
        chart_id: str,
        bins: int = 5,
        unit: str | None = None,
    ) -> ChartDefinition | None:
        if numeric_col not in frame.columns:
            return None

        series = pd.to_numeric(frame[numeric_col], errors="coerce").dropna()
        if series.empty or series.nunique() <= 1:
            return None

        try:
            binned = pd.cut(series, bins=bins, precision=1)
            counts = binned.value_counts().sort_index()
            data = [
                {
                    "label": f"{int(round(interval.left))}-{int(round(interval.right))}",
                    "value": int(cnt),
                }
                for interval, cnt in counts.items()
            ]

            return ChartDefinition(
                id=chart_id,
                title=title,
                chart_type="bar",
                data=data,
                x_key="label",
                y_key="value",
                unit=unit or "count",
            )
        except Exception:
            return None

    @classmethod
    def build_ranking(
        cls,
        frame: pd.DataFrame,
        dim_col: str,
        metric_col: str,
        title: str,
        ranking_id: str,
        agg: str = "sum",  # sum, count, mean
        top_n: int = 5,
        unit: str | None = None,
    ) -> ReportRanking | None:
        if dim_col not in frame.columns:
            return None

        sub = frame.dropna(subset=[dim_col]).copy()
        if agg == "count" or metric_col not in frame.columns:
            grouped = sub[dim_col].value_counts().head(top_n)
            total = len(sub)
        else:
            sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
            sub = sub.dropna(subset=[metric_col])
            if sub.empty:
                return None
            if agg == "mean":
                grouped = sub.groupby(dim_col)[metric_col].mean().sort_values(ascending=False).head(top_n)
                total = None
            else:
                grouped = sub.groupby(dim_col)[metric_col].sum().sort_values(ascending=False).head(top_n)
                total = sub[metric_col].sum()

        items: list[RankingItem] = []
        for idx, (label, val) in enumerate(grouped.items(), start=1):
            pct = (val / total * 100) if total and total > 0 else None
            items.append(
                RankingItem(
                    rank=idx,
                    label=str(label),
                    value=round(float(val), 2),
                    formatted_value=format_value(val, unit),
                    pct_of_total=round(pct, 1) if pct is not None else None,
                )
            )

        return ReportRanking(
            id=ranking_id,
            title=title,
            dimension=dim_col,
            metric=metric_col,
            items=items,
        )
