"""Report Query Builder.

Produces structured analytical queries (QueryPlan) and executes them deterministically
via the shared AnalyticsEngine to produce authoritative VerifiedResults.
The Report Engine NEVER calculates numbers independently.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

from app.analytics.engine import AnalyticsEngine
from app.analytics.models import QueryPlan, VerifiedResult
from app.data.semantic.schema_builder import SemanticSchema, build_semantic_schema


class ReportQueryBuilder:
    """Builds and executes structured queries for reports via the Analytics Engine."""

    def __init__(self, frame: pd.DataFrame, dataset_id: str, schema: SemanticSchema | None = None) -> None:
        self.frame = frame
        self.dataset_id = dataset_id
        self.schema = schema or build_semantic_schema(frame)
        self.engine = AnalyticsEngine(frame)

    def execute_kpi_query(
        self,
        intent: str,
        measure: str | None = None,
        dimension: str | None = None,
        aggregation: str | None = "SUM",
        filter_col: str | None = None,
        filter_val: Any = None,
        question: str = "Calculate KPI",
    ) -> VerifiedResult:
        """Executes a KPI query through AnalyticsEngine and returns a VerifiedResult."""
        plan = QueryPlan(
            status="READY",
            intent=intent,
            measure=measure,
            dimension=dimension,
            aggregation=aggregation,
            filter_col=filter_col,
            filter_val=filter_val,
        )
        return self.engine.execute_query_plan(
            plan=plan,
            frame=self.frame,
            schema=self.schema,
            dataset_id=self.dataset_id,
            question=question,
        )

    def execute_grouped_query(
        self,
        dimension: str,
        measure: str | None = None,
        aggregation: str = "SUM",
        sort: str = "DESC",
        limit: int = 10,
        filter_col: str | None = None,
        filter_val: Any = None,
        question: str = "Grouped summary",
    ) -> VerifiedResult:
        """Executes a grouped aggregate / ranking query through AnalyticsEngine."""
        intent = "GROUP_BY" if measure else "COUNT_UNIQUE"
        plan = QueryPlan(
            status="READY",
            intent=intent,
            dimension=dimension,
            measure=measure,
            aggregation=aggregation,
            sort=sort,
            limit=limit,
            filter_col=filter_col,
            filter_val=filter_val,
        )
        return self.engine.execute_query_plan(
            plan=plan,
            frame=self.frame,
            schema=self.schema,
            dataset_id=self.dataset_id,
            question=question,
        )

    def apply_filters(self, filters: dict[str, Any] | None) -> pd.DataFrame:
        """Filters the working DataFrame deterministically before building report queries."""
        if not filters:
            return self.frame

        filtered = self.frame.copy()
        for key, val in filters.items():
            if val is None or val == "" or val == "all":
                continue

            # Find matching column
            matched_col = next((c for c in filtered.columns if c.lower() == key.lower()), None)
            if matched_col is not None:
                if isinstance(val, (list, tuple)):
                    filtered = filtered[filtered[matched_col].isin(val)]
                else:
                    filtered = filtered[filtered[matched_col].astype(str) == str(val)]
            elif key == "date_range" and isinstance(val, dict):
                # Handle start_date / end_date
                date_col = next(
                    (c for c in filtered.columns if "date" in c.lower() or c.lower() in ("transaction_date", "order_date")),
                    None,
                )
                if date_col:
                    try:
                        dt_series = pd.to_datetime(filtered[date_col], errors="coerce")
                        if val.get("start"):
                            filtered = filtered[dt_series >= pd.to_datetime(val["start"])]
                        if val.get("end"):
                            filtered = filtered[dt_series <= pd.to_datetime(val["end"])]
                    except Exception:
                        pass

        return filtered
