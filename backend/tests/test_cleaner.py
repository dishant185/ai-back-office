from __future__ import annotations

import pandas as pd

from app.data.cleaner import DataCleaner


def test_cleaner_removes_empty_rows_and_trims_strings() -> None:
    frame = pd.DataFrame(
        {
            "customer": [" Alice ", "", "Bob", "  Charlie  "],
            "sales": [100, 200, None, 300],
            "region": [" North ", "South", "", "West"],
        }
    )

    cleaned = DataCleaner().clean(frame)

    assert cleaned.shape[0] == 4
    assert cleaned["customer"].iloc[0] == "Alice"
    assert pd.isna(cleaned["customer"].iloc[1])
    assert cleaned["region"].iloc[0] == "North"
    assert cleaned["region"].iloc[1] == "South"
    assert pd.isna(cleaned["region"].iloc[2])
    assert cleaned["sales"].isna().sum() == 1


def test_cleaner_standardizes_text_columns() -> None:
    frame = pd.DataFrame({"customer": ["ALICE", "bob", "CHARLIE"]})

    cleaned = DataCleaner().clean(frame)

    assert list(cleaned["customer"]) == ["Alice", "Bob", "Charlie"]
