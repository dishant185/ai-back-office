from __future__ import annotations

import re


class ColumnNormalizer:
    """Normalize raw column names into a canonical, deterministic text form."""

    @staticmethod
    def normalize(value: str) -> str:
        if value is None:
            return ""

        text = str(value).strip()
        if not text:
            return ""

        text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
        text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
        text = text.replace("_", " ")
        text = text.replace("-", " ")
        text = text.replace("/", " ")
        text = re.sub(r"\s+", " ", text)
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def normalize_with_metadata(value: str) -> dict[str, str]:
        normalized = ColumnNormalizer.normalize(value)
        return {"original": value, "normalized": normalized}
