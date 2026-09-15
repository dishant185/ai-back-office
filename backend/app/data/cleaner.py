from __future__ import annotations

import pandas as pd


class DataCleaner:
    """Apply conservative, reversible text and row cleanup to tabular datasets."""

    def clean(self, frame: pd.DataFrame) -> pd.DataFrame:
        cleaned = frame.copy()

        for column in cleaned.columns:
            if pd.api.types.is_object_dtype(cleaned[column]) or pd.api.types.is_string_dtype(cleaned[column]):
                cleaned[column] = cleaned[column].map(self._clean_text_value)
                cleaned[column] = cleaned[column].apply(self._normalize_text)

        cleaned = cleaned.replace(r"^\s*$", pd.NA, regex=True)
        cleaned = cleaned.dropna(axis=0, how="all").reset_index(drop=True)

        return cleaned

    def _clean_text_value(self, value: object) -> object:
        if pd.isna(value):
            return value
        if isinstance(value, str):
            return value.strip()
        return value

    def _normalize_text(self, value: object) -> object:
        if pd.isna(value):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            return normalized[:1].upper() + normalized[1:].lower() if normalized else normalized
        return value
