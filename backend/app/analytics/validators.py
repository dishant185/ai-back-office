from __future__ import annotations

import pandas as pd


def validate_dataframe(frame: pd.DataFrame) -> dict[str, object]:
    errors: list[str] = []

    if frame is None:
        errors.append("No dataset was provided.")
        return {"valid": False, "errors": errors}

    if frame.empty:
        errors.append("Dataset is empty.")

    if not isinstance(frame, pd.DataFrame):
        errors.append("Dataset must be a pandas DataFrame.")

    return {"valid": not errors, "errors": errors}
