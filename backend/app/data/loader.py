from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.data.models import ColumnSummary, DatasetInspectionResult, DatasetSummary


class DataLoader:
    """Load and inspect CSV/Excel files in a deterministic, business-agnostic way."""

    def __init__(self) -> None:
        self.supported_extensions = {"csv", "xlsx", "xls"}

    def load_file(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        suffix = path.suffix.lower().lstrip(".")

        if suffix not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {suffix}")

        if suffix == "csv":
            return pd.read_csv(path)

        return pd.read_excel(path)

    def inspect_file(self, file_path: str | Path | pd.DataFrame) -> DatasetInspectionResult:
        frame = self.load_file(file_path) if isinstance(file_path, (str, Path)) else file_path

        preview = frame.head(5).to_dict(orient="records")
        column_names = list(frame.columns)

        summary = DatasetSummary(
            rows=int(frame.shape[0]),
            columns=int(frame.shape[1]),
            missing_cells=int(frame.isna().sum().sum()),
            duplicate_rows=int(frame.duplicated(subset=list(frame.columns)).sum()),
            preview=preview,
            columns_meta=[
                ColumnSummary(
                    name=str(column),
                    dtype=str(frame[column].dtype),
                    missing=int(frame[column].isna().sum()),
                    missing_percentage=float((frame[column].isna().mean() * 100) if len(frame) else 0.0),
                    status=self._column_status(frame[column]),
                )
                for column in frame.columns
            ],
        )

        return DatasetInspectionResult(
            summary=summary,
            sample_rows=preview,
            column_names=column_names,
        )

    def _column_status(self, series: pd.Series) -> str:
        missing_ratio = series.isna().mean()
        if missing_ratio > 0.3:
            return "warning"
        if missing_ratio > 0.1:
            return "review"
        return "good"
