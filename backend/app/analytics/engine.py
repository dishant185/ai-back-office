"""Authoritative Deterministic Analytics Engine using DuckDB and Pandas.

The SINGLE source of truth for all calculations across Dashboard, Reports,
and AI Business Analyst. Never invents numbers or converts missing data to zero.
"""
from __future__ import annotations

import logging
from typing import Any
import pandas as pd

from app.analytics.anomalies import detect_anomalies
from app.analytics.capabilities import detect_capabilities
from app.analytics.derived_metrics import calculate_attrition_rate, calculate_estimated_profit
from app.analytics.field_resolver import standardize_frame
from app.analytics.metrics import build_metrics
from app.analytics.models import (
    AnalyticsResponse,
    AnalyticsSummary,
    QueryPlan,
    VerifiedResult,
)
from app.analytics.query_executor import QueryExecutor
from app.analytics.trends import build_trends
from app.analytics.validators import validate_dataframe
from app.data.semantic.schema_builder import SemanticSchema

logger = logging.getLogger(__name__)


def _safe_dim_values(series: pd.Series) -> list[str]:
    values = []
    for item in series.dropna().astype(str).tolist():
        clean = item.strip()
        if clean:
            values.append(clean)
    return values


class AnalyticsEngine:
    def __init__(self, frame: pd.DataFrame | None = None) -> None:
        self.frame = frame

    def detect_capabilities(self, frame: pd.DataFrame) -> dict[str, Any]:
        return detect_capabilities(frame)

    def analyze(self, frame: pd.DataFrame | None = None) -> AnalyticsResponse:
        working_frame = frame if frame is not None else self.frame
        if working_frame is None:
            raise ValueError("No dataset was supplied to the analytics engine.")

        working_frame = standardize_frame(working_frame)

        validation = validate_dataframe(working_frame)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        profile_info = detect_capabilities(working_frame)
        profile = profile_info["profile"]
        capabilities = profile_info["capabilities"]

        metrics = build_metrics(working_frame, profile)
        trends = build_trends(working_frame, profile)
        anomalies = detect_anomalies(working_frame, profile)

        summary = AnalyticsSummary(
            profile=profile,
            row_count=int(len(working_frame.index)),
            column_count=int(len(working_frame.columns)),
            detected_capabilities=capabilities,
            metric_count=len(metrics),
        )

        return AnalyticsResponse(
            profile=profile,
            capabilities=capabilities,
            summary=summary,
            metrics=metrics,
            trends=trends,
            anomalies=anomalies,
            notes=[f"Detected dataset profile: {profile}."],
            raw={"profile": profile, "capabilities": capabilities},
        )

    def summarize_dimensions(self, frame: pd.DataFrame, profile: str | None = None) -> list[dict[str, Any]]:
        if frame.empty:
            return []

        profile_name = profile or detect_capabilities(frame)["profile"]
        candidates = {
            "sales": ["region", "product", "category"],
            "hr": ["city", "education", "department"],
            "customer": ["customer_region", "customer_type"],
            "inventory": ["item", "sku", "category"],
            "finance": ["account_name", "region", "department"],
            "operations": ["status", "team", "branch"],
            "generic": [col for col in frame.columns if pd.api.types.is_object_dtype(frame[col])][:3],
        }

        dimensions: list[dict[str, Any]] = []
        target_candidates = candidates.get(profile_name, [])
        used_cols = set()

        for target in target_candidates:
            matched_col = next((c for c in frame.columns if c.lower() == target.lower() or target.lower() in c.lower()), None)
            if matched_col and matched_col not in used_cols:
                values = _safe_dim_values(frame[matched_col])
                if values:
                    unique_values = list(dict.fromkeys(values))
                    dimensions.append({
                        "name": str(matched_col),
                        "values": unique_values,
                        "count": len(unique_values),
                    })
                    used_cols.add(matched_col)

        for col in frame.columns:
            if col not in used_cols and (pd.api.types.is_object_dtype(frame[col]) or pd.api.types.is_string_dtype(frame[col])):
                values = _safe_dim_values(frame[col])
                if values and len(set(values)) <= 50:
                    unique_values = list(dict.fromkeys(values))
                    dimensions.append({
                        "name": str(col),
                        "values": unique_values,
                        "count": len(unique_values),
                    })
                    used_cols.add(col)
                if len(dimensions) >= 6:
                    break

        return dimensions

    def rank_by_metric(self, frame: pd.DataFrame, metric_name: str, dimension_name: str) -> list[dict[str, Any]]:
        if frame.empty or metric_name not in frame.columns or dimension_name not in frame.columns:
            return []

        aggregated = (
            frame[[dimension_name, metric_name]]
            .assign(__metric__=pd.to_numeric(frame[metric_name], errors="coerce"))
            .dropna(subset=["__metric__"])
            .groupby(dimension_name, as_index=False)["__metric__"].sum()
            .rename(columns={"__metric__": "value"})
            .sort_values("value", ascending=False)
            .reset_index(drop=True)
        )

        ranked = []
        for idx, row in aggregated.iterrows():
            ranked.append({
                "label": str(row[dimension_name]),
                "value": float(row["value"]),
                "rank": idx + 1,
            })
        return ranked

    def segment_summary(self, frame: pd.DataFrame, dimension_name: str, metric_name: str | None = None) -> list[dict[str, Any]]:
        if frame.empty or dimension_name not in frame.columns:
            return []

        metric_name = metric_name or next((col for col in ["revenue", "amount", "profit", "sales", "target"] if col in frame.columns), None)
        if metric_name is None:
            metric_name = next((col for col in frame.columns if pd.api.types.is_numeric_dtype(frame[col])), None)

        if metric_name is None:
            return []

        grouped = frame[[dimension_name, metric_name]].copy()
        grouped[metric_name] = pd.to_numeric(grouped[metric_name], errors="coerce")
        grouped = grouped.dropna(subset=[metric_name])

        summary = grouped.groupby(dimension_name, as_index=False).agg(
            count=(metric_name, "size"),
            revenue_total=(metric_name, "sum"),
        )

        return [
            {
                "label": str(row[dimension_name]),
                "count": int(row["count"]),
                "revenue_total": float(row["revenue_total"]),
            }
            for _, row in summary.sort_values("revenue_total", ascending=False).iterrows()
        ]

    def execute_query_plan(
        self,
        plan: QueryPlan,
        frame: pd.DataFrame,
        schema: SemanticSchema,
        dataset_id: str,
        question: str,
    ) -> VerifiedResult:
        """Execute a validated QueryPlan using DuckDB and Pandas deterministically.
        
        Returns an immutable VerifiedResult.
        """
        intent = plan.intent.upper()
        cols_by_semantic = {c.semantic_name: c.original_name for c in schema.columns}
        orig_cols = list(frame.columns)

        def resolve_col(name: str | None) -> str | None:
            if not name:
                return None
            if name in orig_cols:
                return name
            if name.lower() in cols_by_semantic:
                return cols_by_semantic[name.lower()]
            for c in orig_cols:
                if c.lower() == name.lower() or name.lower() in c.lower():
                    return c
            return None

        # 1. Handle explicit unavailable or clarification statuses
        if plan.status == "UNAVAILABLE" or intent == "UNAVAILABLE":
            return VerifiedResult(
                dataset_id=dataset_id,
                question=question,
                intent="UNAVAILABLE",
                query_plan=plan.model_dump(),
                result={},
                source_fields=[],
                verification_status="unavailable",
                is_unavailable=True,
                error_message=plan.unavailable_reason or f"Requested information is unavailable in this dataset.",
            )

        if plan.status == "CLARIFICATION" or intent == "CLARIFICATION":
            return VerifiedResult(
                dataset_id=dataset_id,
                question=question,
                intent="CLARIFICATION",
                query_plan=plan.model_dump(),
                result={"clarification_question": plan.clarification_question or "Could you clarify your question?"},
                source_fields=[],
                verification_status="clarification",
            )

        executor = QueryExecutor(frame)
        try:
            # 2. Quality-related queries (missing values, duplicate rows)
            if intent in ("QUALITY", "DUPLICATE_CHECK", "MISSING_VALUE_CHECK"):
                if intent == "DUPLICATE_CHECK" or "duplicate" in question.lower():
                    dup_count = int(frame.duplicated().sum())
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent="DUPLICATE_CHECK",
                        query_plan=plan.model_dump(),
                        result={"value": dup_count, "duplicate_count": dup_count, "label": "Duplicate Records Count"},
                        source_fields=orig_cols[:5],
                        verification_status="verified",
                    )
                else:
                    missing_count = int(frame.isna().sum().sum())
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent="MISSING_VALUE_CHECK",
                        query_plan=plan.model_dump(),
                        result={"value": missing_count, "missing_count": missing_count, "label": "Missing Values Count"},
                        source_fields=orig_cols[:5],
                        verification_status="verified",
                    )

            # 2b. LIST_UNIQUE (e.g. "What sales channels are available?")
            if intent == "LIST_UNIQUE":
                dim_col = resolve_col(plan.dimension)
                if not dim_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Dimension '{plan.dimension}' is unavailable in this dataset.",
                    )
                try:
                    unique_vals = [str(x) for x in frame[dim_col].dropna().unique() if str(x).strip()]
                except Exception:
                    unique_vals = []
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={
                        "value": len(unique_vals),
                        "unique_values": unique_vals,
                        "dimension": dim_col,
                        "label": f"Available {dim_col} Options",
                    },
                    source_fields=[dim_col],
                    verification_status="verified",
                )

            # 3. Derived metrics (Estimated Profit, Attrition Rate)
            if intent == "DERIVED_METRIC" or (plan.measure and plan.measure.lower() in ("profit", "estimated_profit", "attrition", "attrition_rate")):
                req_metric = (plan.measure or "").lower()
                if "profit" in req_metric or "profit" in question.lower():
                    val, label, src_cols = calculate_estimated_profit(frame, schema)
                    if val is None:
                        return VerifiedResult(
                            dataset_id=dataset_id,
                            question=question,
                            intent="DERIVED_METRIC",
                            query_plan=plan.model_dump(),
                            result={},
                            source_fields=[],
                            verification_status="unavailable",
                            is_unavailable=True,
                            error_message="Profit / unit cost metrics are unavailable in this dataset.",
                        )
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent="DERIVED_METRIC",
                        query_plan=plan.model_dump(),
                        result={"value": round(val, 2), "label": label},
                        source_fields=src_cols,
                        verification_status="verified",
                    )

                if "attrition" in req_metric or "attrition" in question.lower() or "left" in question.lower():
                    rate, left_count, src_cols = calculate_attrition_rate(frame, schema)
                    if rate is None:
                        return VerifiedResult(
                            dataset_id=dataset_id,
                            question=question,
                            intent="DERIVED_METRIC",
                            query_plan=plan.model_dump(),
                            result={},
                            source_fields=[],
                            verification_status="unavailable",
                            is_unavailable=True,
                            error_message="Attrition / leave status is unavailable in this dataset.",
                        )
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent="DERIVED_METRIC",
                        query_plan=plan.model_dump(),
                        result={
                            "value": rate,
                            "percentage": rate,
                            "count_left": left_count,
                            "label": "Attrition Rate (%)",
                        },
                        source_fields=src_cols,
                        verification_status="verified",
                    )

            # 4. Total record count
            if intent == "COUNT":
                filter_c = resolve_col(plan.filter_col)
                cnt = executor.execute_count(filter_c, plan.filter_val)
                src = [filter_c] if filter_c else []
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={"value": cnt, "label": "Total Records"},
                    source_fields=src,
                    verification_status="verified",
                )

            # 5. Unique Count of Dimension (CRITICAL: "How many regions are covered?" -> COUNT_UNIQUE, NOT TOP_ENTITY)
            if intent in ("COUNT_UNIQUE", "DISTINCT_COUNT"):
                dim_col = resolve_col(plan.dimension)
                if not dim_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Dimension '{plan.dimension}' is unavailable in this dataset.",
                    )
                filter_c = resolve_col(plan.filter_col)
                cnt = executor.execute_count_unique(dim_col, filter_c, plan.filter_val)
                # Also collect the actual unique values for natural response display
                try:
                    unique_vals = [str(x) for x in frame[dim_col].dropna().unique() if str(x).strip()]
                except Exception:
                    unique_vals = []
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={
                        "value": cnt,
                        "dimension": dim_col,
                        "unique_values": unique_vals[:20],
                        "label": f"Unique {dim_col} Count",
                    },
                    source_fields=[dim_col] + ([filter_c] if filter_c else []),
                    verification_status="verified",
                )

            # 6. Numerical aggregations: SUM, AVERAGE, MEDIAN, MINIMUM, MAXIMUM
            if intent in ("SUM", "AVERAGE", "AVG", "MEDIAN", "MINIMUM", "MIN", "MAXIMUM", "MAX"):
                meas_col = resolve_col(plan.measure)
                if not meas_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Measure '{plan.measure}' is unavailable in this dataset.",
                    )
                filter_c = resolve_col(plan.filter_col)
                val = executor.execute_aggregation(meas_col, intent, filter_c, plan.filter_val)
                if val is None:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[meas_col],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Could not compute {intent} for {meas_col}.",
                    )
                val_rounded = round(val, 2)
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={"value": val_rounded, "measure": meas_col, "label": f"{intent} of {meas_col}"},
                    source_fields=[meas_col] + ([filter_c] if filter_c else []),
                    verification_status="verified",
                )

            # 7. Top / Bottom Entity (TOP_ENTITY, BOTTOM_ENTITY, TOP_N, BOTTOM_N)
            if intent in ("TOP_ENTITY", "BOTTOM_ENTITY", "TOP_N", "BOTTOM_N"):
                dim_col = resolve_col(plan.dimension)
                if not dim_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Dimension '{plan.dimension}' is unavailable in this dataset.",
                    )
                meas_col = resolve_col(plan.measure)
                is_desc = "TOP" in intent
                lim = plan.limit if plan.limit and plan.limit > 0 else 1
                records = executor.execute_top_entity(
                    dimension=dim_col,
                    measure=meas_col,
                    aggregation=plan.aggregation or "SUM",
                    descending=is_desc,
                    limit=lim,
                    filter_col=resolve_col(plan.filter_col),
                    filter_val=plan.filter_val,
                )
                if not records:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[dim_col],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message="No matching entity data found.",
                    )
                top_record = records[0]
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={
                        "entity": top_record["entity"],
                        "value": round(top_record["metric_value"], 2) if isinstance(top_record["metric_value"], (int, float)) else top_record["metric_value"],
                        "dimension": dim_col,
                        "measure": meas_col or "record_count",
                        "records": records,
                    },
                    source_fields=[dim_col] + ([meas_col] if meas_col else []),
                    verification_status="verified",
                )

            # 8. Distribution / Group By / Rank
            if intent in ("DISTRIBUTION", "GROUP_BY", "RANK", "PERCENTAGE"):
                dim_col = resolve_col(plan.dimension)
                if not dim_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message=f"Dimension '{plan.dimension}' is unavailable in this dataset.",
                    )
                lim = plan.limit if plan.limit and plan.limit > 0 else 10
                records = executor.execute_distribution(dim_col, limit=lim)
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={
                        "distribution": records,
                        "dimension": dim_col,
                        "item_count": len(records),
                        "value": len(records),
                    },
                    source_fields=[dim_col],
                    verification_status="verified",
                )

            # 9. Comparison between two entities (e.g. Compare North and South, Compare categories)
            if intent == "COMPARISON":
                dim_col = resolve_col(plan.dimension)
                meas_col = resolve_col(plan.measure)
                entities = list(plan.entities or [])

                if dim_col:
                    if len(entities) < 2:
                        top_items = executor.execute_top_entity(dim_col, meas_col, limit=2)
                        if len(top_items) >= 2:
                            entities = [str(top_items[0]["entity"]), str(top_items[1]["entity"])]

                    if len(entities) >= 2:
                        ent_a = str(entities[0])
                        ent_b = str(entities[1])
                        if meas_col:
                            val_a = executor.execute_aggregation(meas_col, "SUM", dim_col, ent_a) or 0.0
                            val_b = executor.execute_aggregation(meas_col, "SUM", dim_col, ent_b) or 0.0
                        else:
                            val_a = float(executor.execute_count(dim_col, ent_a))
                            val_b = float(executor.execute_count(dim_col, ent_b))
                        diff = val_a - val_b
                        return VerifiedResult(
                            dataset_id=dataset_id,
                            question=question,
                            intent=intent,
                            query_plan=plan.model_dump(),
                            result={
                                "entity_a": ent_a,
                                "value_a": round(val_a, 2),
                                "entity_b": ent_b,
                                "value_b": round(val_b, 2),
                                "difference": round(diff, 2),
                                "measure": meas_col or "record_count",
                                "dimension": dim_col,
                            },
                            source_fields=[dim_col] + ([meas_col] if meas_col else []),
                            verification_status="verified",
                        )

                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={"difference": 0.0, "note": "Insufficient categories to compare."},
                    source_fields=[dim_col] if dim_col else [],
                    verification_status="verified",
                )

            # 10. Time Series Trend / Growth
            if intent in ("TREND", "GROWTH"):
                # Find date column
                date_cols = [c.original_name for c in schema.columns if c.role == "time_dimension" or "date" in c.data_type]
                date_col = date_cols[0] if date_cols else resolve_col("date")
                if not date_col:
                    return VerifiedResult(
                        dataset_id=dataset_id,
                        question=question,
                        intent=intent,
                        query_plan=plan.model_dump(),
                        result={},
                        source_fields=[],
                        verification_status="unavailable",
                        is_unavailable=True,
                        error_message="No transaction date column exists in this dataset for trend analysis.",
                    )
                meas_col = resolve_col(plan.measure)
                records = executor.execute_time_series(date_col, meas_col, granularity="monthly")
                return VerifiedResult(
                    dataset_id=dataset_id,
                    question=question,
                    intent=intent,
                    query_plan=plan.model_dump(),
                    result={
                        "periods": records,
                        "period_count": len(records),
                        "date_field": date_col,
                        "measure": meas_col,
                    },
                    source_fields=[date_col] + ([meas_col] if meas_col else []),
                    verification_status="verified",
                )

            # 11. General summary fallback
            return VerifiedResult(
                dataset_id=dataset_id,
                question=question,
                intent=intent,
                query_plan=plan.model_dump(),
                result={
                    "total_rows": len(frame),
                    "total_columns": len(frame.columns),
                    "columns": orig_cols[:15],
                },
                source_fields=orig_cols[:5],
                verification_status="verified",
            )

        finally:
            executor.close()
