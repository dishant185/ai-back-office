from __future__ import annotations

import pandas as pd

from app.data.validator import DataValidator


def test_validator_flags_missing_and_duplicate_rows() -> None:
    frame = pd.DataFrame(
        {
            "customer": ["Alice", "Alice", "Charlie", None],
            "sales": [100, 100, 300, None],
            "region": ["North", "North", "West", "South"],
        }
    )

    result = DataValidator().validate(frame)

    assert result.valid is False
    assert any(issue.code == "DUPLICATE_ROWS" for issue in result.warnings)
    assert any(issue.code == "MISSING_VALUES" for issue in result.warnings)


def test_validator_accepts_clean_dataset() -> None:
    frame = pd.DataFrame(
        {
            "customer": ["Alice", "Bob", "Charlie"],
            "sales": [100, 200, 300],
        }
    )

    result = DataValidator().validate(frame)

    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_validator_flags_empty_dataset() -> None:
    frame = pd.DataFrame()

    result = DataValidator().validate(frame)

    assert result.valid is False
    assert any(issue.code == "EMPTY_DATASET" for issue in result.errors)
