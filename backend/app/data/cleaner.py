from __future__ import annotations

import pandas as pd
from app.data.universal_cleaner import UniversalDataCleaner, CleaningAuditSummary, CleaningPreview


class DataCleaner:
    """Apply conservative, reversible text and row cleanup to tabular datasets.
    
    Maintains backward compatibility while delegating to UniversalDataCleaner.
    """

    def __init__(self) -> None:
        self.last_audit: CleaningAuditSummary | None = None

    def clean(self, frame: pd.DataFrame) -> pd.DataFrame:
        cleaned_df, audit = UniversalDataCleaner.clean(
            frame,
            actions=[
                "trim_whitespace",
                "normalize_nulls",
                "standardize_casing",
                "parse_currencies",
                "parse_percentages",
                "normalize_booleans",
            ],
        )
        self.last_audit = audit
        return cleaned_df

    def preview_issues(self, frame: pd.DataFrame, dataset_id: str = "dataset") -> CleaningPreview:
        return UniversalDataCleaner.preview_issues(frame, dataset_id=dataset_id)
