from __future__ import annotations

import pandas as pd

from app.data.cleaner import DataCleaner
from app.data.loader import DataLoader
from app.data.validator import DataValidator


def test_day13_pipeline_returns_summary_and_validation() -> None:
    frame = pd.DataFrame(
        {
            "customer": [" Alice ", "Alice", "Charlie", ""],
            "sales": [100, 100, 300, 400],
            "region": ["North", "North", "West", "East"],
        }
    )

    cleaned = DataCleaner().clean(frame)
    validation = DataValidator().validate(cleaned)
    inspection = DataLoader().inspect_file(pd.DataFrame(cleaned))

    assert inspection.summary.rows == 4
    assert validation.valid is False
    assert any(item.code == "DUPLICATE_ROWS" for item in validation.warnings)
    assert inspection.summary.columns == 3
