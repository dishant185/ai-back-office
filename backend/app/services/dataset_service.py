from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.data.cleaner import DataCleaner
from app.data.loader import DataLoader
from app.data.profiler import DataProfiler
from app.data.validator import DataValidator


class DatasetService:
    def process_file(self, file_path: str | Path) -> tuple[pd.DataFrame, dict[str, object]]:
        loader = DataLoader()
        cleaner = DataCleaner()
        validator = DataValidator()
        profiler = DataProfiler()

        frame = loader.load_file(file_path)
        cleaned = cleaner.clean(frame)
        validation = validator.validate(cleaned)
        inspection = loader.inspect_file(cleaned)
        profile = profiler.profile(cleaned)
        insights = profiler.insights(cleaned, validation)
        audit = profiler.audit(cleaned)

        payload = {
            "summary": inspection.summary.model_dump(),
            "validation": validation.model_dump(),
            "profile": profile.model_dump(),
            "insights": insights.model_dump(),
            "audit": audit.model_dump(),
        }

        return cleaned, payload
