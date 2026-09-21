"""Controlled DuckDB + Pandas analytical query executor.

Executes strictly parameterized, internally compiled analytics operations.
Does NOT accept arbitrary SQL strings from user or LLM.
"""
from __future__ import annotations

import logging
from typing import Any
import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Safe analytical query executor using DuckDB and Pandas."""

    def __init__(self, frame: pd.DataFrame, table_name: str = "dataset") -> None:
        self.frame = frame
        self.table_name = table_name
        self.con = duckdb.connect(database=":memory:")
        # Register the dataframe safely in DuckDB
        self.con.register(table_name, frame)

    def execute_count(self, filter_col: str | None = None, filter_val: Any = None) -> int:
        """Calculate total record count, optionally filtered."""
        if filter_col and filter_val is not None:
            # Clean column name for SQL quote
            safe_col = filter_col.replace('"', '""')
            query = f'SELECT COUNT(*) FROM {self.table_name} WHERE "{safe_col}" = ?'
            res = self.con.execute(query, [filter_val]).fetchone()
            return int(res[0]) if res else 0
        return len(self.frame)

    def execute_count_unique(self, dimension: str, filter_col: str | None = None, filter_val: Any = None) -> int:
        """Calculate unique count of a dimension."""
        safe_dim = dimension.replace('"', '""')
        if filter_col and filter_val is not None:
            safe_fcol = filter_col.replace('"', '""')
            query = f'SELECT COUNT(DISTINCT "{safe_dim}") FROM {self.table_name} WHERE "{safe_fcol}" = ?'
            res = self.con.execute(query, [filter_val]).fetchone()
        else:
            query = f'SELECT COUNT(DISTINCT "{safe_dim}") FROM {self.table_name}'
            res = self.con.execute(query).fetchone()
        return int(res[0]) if res else 0

    def execute_aggregation(
        self,
        measure: str,
        aggregation: str,  # SUM, AVG, MIN, MAX, MEDIAN
        filter_col: str | None = None,
        filter_val: Any = None,
    ) -> float | None:
        """Calculate aggregate of a measure."""
        agg = aggregation.upper()
        if agg not in ("SUM", "AVG", "AVERAGE", "MIN", "MINIMUM", "MAX", "MAXIMUM", "MEDIAN"):
            agg = "SUM"

        if agg in ("AVG", "AVERAGE"):
            sql_fn = "AVG"
        elif agg in ("MIN", "MINIMUM"):
            sql_fn = "MIN"
        elif agg in ("MAX", "MAXIMUM"):
            sql_fn = "MAX"
        elif agg == "MEDIAN":
            sql_fn = "MEDIAN"
        else:
            sql_fn = "SUM"

        safe_measure = measure.replace('"', '""')
        if filter_col and filter_val is not None:
            safe_fcol = filter_col.replace('"', '""')
            query = f'SELECT {sql_fn}("{safe_measure}") FROM {self.table_name} WHERE "{safe_fcol}" = ?'
            res = self.con.execute(query, [filter_val]).fetchone()
        else:
            query = f'SELECT {sql_fn}("{safe_measure}") FROM {self.table_name}'
            res = self.con.execute(query).fetchone()

        if res and res[0] is not None:
            return float(res[0])
        return None

    def execute_top_entity(
        self,
        dimension: str,
        measure: str | None = None,
        aggregation: str = "SUM",
        descending: bool = True,
        limit: int = 1,
        filter_col: str | None = None,
        filter_val: Any = None,
    ) -> list[dict[str, Any]]:
        """Get top N or bottom N entities by record count or measure sum/avg."""
        safe_dim = dimension.replace('"', '""')
        order = "DESC" if descending else "ASC"

        params: list[Any] = []
        where_clause = ""
        if filter_col and filter_val is not None:
            safe_fcol = filter_col.replace('"', '""')
            where_clause = f'WHERE "{safe_fcol}" = ?'
            params.append(filter_val)

        if measure:
            safe_measure = measure.replace('"', '""')
            agg_fn = "AVG" if aggregation.upper() in ("AVG", "AVERAGE") else "SUM"
            query = (
                f'SELECT "{safe_dim}" AS entity, {agg_fn}("{safe_measure}") AS metric_value '
                f'FROM {self.table_name} {where_clause} '
                f'GROUP BY "{safe_dim}" '
                f'HAVING "{safe_dim}" IS NOT NULL '
                f'ORDER BY metric_value {order} '
                f'LIMIT {int(limit)}'
            )
        else:
            query = (
                f'SELECT "{safe_dim}" AS entity, COUNT(*) AS metric_value '
                f'FROM {self.table_name} {where_clause} '
                f'GROUP BY "{safe_dim}" '
                f'HAVING "{safe_dim}" IS NOT NULL '
                f'ORDER BY metric_value {order} '
                f'LIMIT {int(limit)}'
            )

        df = self.con.execute(query, params).df()
        return df.to_dict(orient="records")

    def execute_distribution(
        self,
        dimension: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get frequency distribution and percentage share of a dimension."""
        safe_dim = dimension.replace('"', '""')
        total_rows = len(self.frame)

        query = (
            f'SELECT "{safe_dim}" AS item, COUNT(*) AS record_count '
            f'FROM {self.table_name} '
            f'GROUP BY "{safe_dim}" '
            f'ORDER BY record_count DESC '
            f'LIMIT {int(limit)}'
        )
        df = self.con.execute(query).df()
        records = []
        for _, row in df.iterrows():
            item_val = row["item"]
            cnt = int(row["record_count"])
            pct = (cnt / total_rows * 100) if total_rows > 0 else 0.0
            records.append({
                "item": str(item_val) if pd.notna(item_val) else "Unknown",
                "count": cnt,
                "percentage": round(pct, 2),
            })
        return records

    def execute_time_series(
        self,
        date_col: str,
        measure: str | None = None,
        granularity: str = "monthly",  # monthly, yearly
    ) -> list[dict[str, Any]]:
        """Group time series by month or year."""
        safe_date = date_col.replace('"', '""')
        date_format = "%Y-%m" if granularity == "monthly" else "%Y"

        if measure:
            safe_measure = measure.replace('"', '""')
            query = (
                f'SELECT strftime(TRY_CAST("{safe_date}" AS DATE), \'{date_format}\') AS period, '
                f'SUM("{safe_measure}") AS total_val, COUNT(*) AS txn_count '
                f'FROM {self.table_name} '
                f'WHERE TRY_CAST("{safe_date}" AS DATE) IS NOT NULL '
                f'GROUP BY period '
                f'ORDER BY period ASC'
            )
        else:
            query = (
                f'SELECT strftime(TRY_CAST("{safe_date}" AS DATE), \'{date_format}\') AS period, '
                f'COUNT(*) AS txn_count '
                f'FROM {self.table_name} '
                f'WHERE TRY_CAST("{safe_date}" AS DATE) IS NOT NULL '
                f'GROUP BY period '
                f'ORDER BY period ASC'
            )

        try:
            df = self.con.execute(query).df()
            return df.to_dict(orient="records")
        except Exception:
            return []

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass
