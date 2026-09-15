from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.data.loader import DataLoader


def test_csv_loader_reads_rows_and_columns(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.csv"
    frame = pd.DataFrame(
        {
            "customer": ["Alice", "Bob", "Charlie"],
            "sales": [100, 200, 300],
            "region": ["North", "South", None],
        }
    )
    frame.to_csv(sample_path, index=False)

    loader = DataLoader()
    data = loader.load_file(sample_path)

    assert data.shape == (3, 3)
    assert list(data.columns) == ["customer", "sales", "region"]


def test_loader_builds_summary_and_preview(tmp_path: Path) -> None:
    sample_path = tmp_path / "summary.csv"
    pd.DataFrame(
        {
            "customer": ["Alice", "Alice", "Charlie", "Charlie"],
            "sales": [100, 100, 300, 300],
            "region": ["North", "North", "West", None],
        }
    ).to_csv(sample_path, index=False)

    loader = DataLoader()
    inspection = loader.inspect_file(sample_path)

    assert inspection.summary.rows == 4
    assert inspection.summary.columns == 3
    assert inspection.summary.duplicate_rows == 1
    assert inspection.summary.missing_cells >= 1
    assert len(inspection.summary.preview) > 0
    assert len(inspection.summary.columns_meta) == 3
    assert inspection.column_names == ["customer", "sales", "region"]
