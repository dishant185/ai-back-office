from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

from app.schemas.upload import ColumnProfile, ColumnSchema, DatasetAudit, DatasetInsights, DatasetProfile, ValidationResult


class DataProfiler:
    """Build a generic, deterministic column profile and dataset insights for uploaded data."""

    def profile(self, frame: pd.DataFrame) -> DatasetProfile:
        columns: list[ColumnProfile] = []

        for column_name in frame.columns:
            series = frame[column_name]
            missing = int(series.isna().sum())
            non_null = int(series.notna().sum())
            unique = int(series.nunique(dropna=True))
            sample_values = [self._coerce_value(value) for value in series.dropna().head(3).tolist()]

            min_val = None
            max_val = None
            try:
                if not series.dropna().empty:
                    min_val = self._summary_value(series.min())
                    max_val = self._summary_value(series.max())
            except Exception:
                try:
                    s_str = series.dropna().astype(str)
                    min_val = self._summary_value(s_str.min())
                    max_val = self._summary_value(s_str.max())
                except Exception:
                    min_val = None
                    max_val = None

            columns.append(
                ColumnProfile(
                    name=str(column_name),
                    dtype=str(series.dtype),
                    missing=missing,
                    non_null=non_null,
                    unique=unique,
                    min_value=min_val,
                    max_value=max_val,
                    sample_values=sample_values,
                )
            )

        return DatasetProfile(columns=columns)

    def insights(self, frame: pd.DataFrame, validation: ValidationResult | None = None) -> DatasetInsights:
        schema = [
            ColumnSchema(
                name=str(column_name),
                dtype=str(frame[column_name].dtype),
                nullable=bool(frame[column_name].isna().sum() >= 0),
                inferred_type=self._infer_type(frame[column_name]),
                missing_ratio=float(frame[column_name].isna().mean()) if len(frame) else 0.0,
            )
            for column_name in frame.columns
        ]

        issue_messages: list[str] = []
        if validation is not None:
            issue_messages.extend(item.message for item in validation.errors)
            issue_messages.extend(item.message for item in validation.warnings)

        missing_ratio = float(frame.isna().sum().sum() / (frame.size or 1))
        quality_score = round(max(0.0, 100.0 - (missing_ratio * 100.0) - (len(issue_messages) * 8.0)), 2)

        status = "processed" if not validation or not validation.errors else "needs_review"

        return DatasetInsights(
            quality_score=quality_score,
            status=status,
            schema=schema,
            issues=issue_messages,
        )

    def audit(self, frame: pd.DataFrame) -> DatasetAudit:
        checksum_input = frame.to_csv(index=False).encode("utf-8")
        digest = hashlib.sha256(checksum_input).hexdigest()
        return DatasetAudit(
            status="processed",
            row_count=int(frame.shape[0]),
            column_count=int(frame.shape[1]),
            checksum=f"sha256:{digest}",
        )

    def _infer_type(self, series: pd.Series) -> str:
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        return "string"

    def _summary_value(self, value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return value
        return str(value)

    def _coerce_value(self, value: Any) -> Any:
        if pd.isna(value):
            return None
        return str(value)
