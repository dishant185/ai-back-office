from __future__ import annotations

from typing import Any

import pandas as pd

from app.schemas.upload import ValidationError, ValidationResult, ValidationWarning


class DataValidator:
    """Run conservative, business-agnostic validation checks on tabular data."""

    def validate(self, frame: pd.DataFrame) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationWarning] = []

        if frame.empty:
            errors.append(
                ValidationError(code="EMPTY_DATASET", message="The dataset is empty and cannot be processed.")
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        total_rows = int(frame.shape[0])
        total_columns = int(frame.shape[1])

        if total_columns == 0:
            errors.append(
                ValidationError(code="NO_COLUMNS", message="The dataset does not contain any columns.")
            )

        if total_rows == 0:
            errors.append(
                ValidationError(code="NO_ROWS", message="The dataset does not contain any rows.")
            )

        missing_values = frame.isna().sum().sum()
        if missing_values > 0:
            warnings.append(
                ValidationWarning(
                    code="MISSING_VALUES",
                    message=f"Dataset contains {missing_values} missing value(s).",
                )
            )

        duplicate_rows = int(frame.duplicated(subset=list(frame.columns)).sum())
        if duplicate_rows > 0:
            warnings.append(
                ValidationWarning(
                    code="DUPLICATE_ROWS",
                    message=f"Dataset contains {duplicate_rows} duplicate row(s).",
                )
            )

        for column_name in frame.columns:
            series = frame[column_name]
            missing_count = int(series.isna().sum())
            if missing_count > 0:
                warnings.append(
                    ValidationWarning(
                        code="MISSING_COLUMN_VALUES",
                        column=str(column_name),
                        message=f"Column '{column_name}' contains {missing_count} missing value(s).",
                    )
                )

            if series.empty:
                warnings.append(
                    ValidationWarning(
                        code="EMPTY_COLUMN",
                        column=str(column_name),
                        message=f"Column '{column_name}' is empty.",
                    )
                )

        valid = not errors and not any(
            warning.code in {"MISSING_VALUES", "DUPLICATE_ROWS", "MISSING_COLUMN_VALUES", "EMPTY_COLUMN"}
            for warning in warnings
        )

        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
