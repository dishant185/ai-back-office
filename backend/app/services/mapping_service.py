from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.data.loader import DataLoader
from app.data.mapping.matcher import ColumnMatcher
from app.data.mapping.normalizer import ColumnNormalizer
from app.data.mapping.validator import MappingValidator


class MappingService:
    def __init__(self) -> None:
        self.matcher = ColumnMatcher()

    def suggest(self, columns: list[str]) -> list[dict[str, object]]:
        # Use batch match_columns for deduplication (prevents duplicate targets)
        raw_suggestions = self.matcher.match_columns(columns)
        suggestions: list[dict[str, object]] = []
        for column, suggestion in zip(columns, raw_suggestions):
            suggestions.append(
                {
                    "source": suggestion["source"],
                    "normalized": ColumnNormalizer.normalize(column),
                    "suggested_target": suggestion["suggested_target"],
                    "confidence": int(suggestion["confidence"]),
                    "status": suggestion["status"],
                    "reason": suggestion["reason"],
                }
            )
        return suggestions

    def validate(self, mappings: list[dict[str, object]]) -> dict[str, object]:
        return MappingValidator.validate(mappings)

    def apply_mapping(self, upload_id: str | None, mappings: list[dict[str, object]]) -> dict[str, object]:
        if not upload_id:
            return {
                "success": False,
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "preview": [],
                "mapping_summary": {"original_columns": 0, "standardized_fields": 0, "mapped": 0, "unmapped": 0, "conflicts": 0},
                "standardized": {"rows": [], "columns": []},
                "audit": {"status": "missing_upload_id", "errors": ["Upload reference is missing."]},
            }

        doc = None
        source_path = Path(settings.upload_dir) / upload_id
        if not source_path.exists():
            from app.db.repositories.dataset_repository import DatasetRepository
            doc = DatasetRepository().get_by_id(upload_id)
            if doc and (doc.get("file_path") or doc.get("saved_path")):
                p = Path(doc.get("file_path") or doc.get("saved_path"))
                if p.exists():
                    source_path = p

            if not source_path.exists():
                for d in [Path("data/uploads"), Path("../data/uploads")]:
                    if d.exists():
                        for f in d.glob("*.*"):
                            if upload_id in f.name:
                                source_path = f
                                break
                        if source_path.exists():
                            break

        if not source_path.exists():
            if not doc:
                from app.db.repositories.dataset_repository import DatasetRepository
                doc = DatasetRepository().get_by_id(upload_id)
            if doc and doc.get("summary", {}).get("preview"):
                dataframe = pd.DataFrame(doc["summary"]["preview"])
            else:
                return {
                    "success": False,
                    "row_count": 0,
                    "column_count": 0,
                    "columns": [],
                    "preview": [],
                    "mapping_summary": {"original_columns": 0, "standardized_fields": 0, "mapped": 0, "unmapped": 0, "conflicts": 0},
                    "standardized": {"rows": [], "columns": []},
                    "audit": {"status": "not_found", "errors": [f"Dataset {upload_id} was not found."]},
                }
        else:
            dataframe = DataLoader().load_file(source_path)

        rename_map = {
            str(item.get("source")): str(item.get("target"))
            for item in mappings
            if item.get("target") and not bool(item.get("ignored", False)) and item.get("source") in dataframe.columns
        }

        standardized = dataframe.rename(columns=rename_map).copy()
        preview = self._serialize_preview(standardized)

        mapping_summary = {
            "original_columns": int(len(dataframe.columns)),
            "standardized_fields": int(len(standardized.columns)),
            "mapped": int(len(rename_map)),
            "unmapped": int(len(dataframe.columns) - len(rename_map)),
            "conflicts": 0,
        }

        return {
            "success": True,
            "row_count": int(len(standardized.index)),
            "column_count": int(len(standardized.columns)),
            "columns": [str(column) for column in standardized.columns],
            "preview": preview,
            "mapping_summary": mapping_summary,
            "standardized": {"rows": preview, "columns": [str(column) for column in standardized.columns]},
            "audit": {
                "status": "processed",
                "source_row_count": int(len(dataframe.index)),
                "standardized_row_count": int(len(standardized.index)),
                "preview_row_count": len(preview),
                "errors": [],
            },
        }

    @staticmethod
    def _serialize_preview(frame: pd.DataFrame, limit: int = 10) -> list[dict[str, object]]:
        preview = frame.head(limit).copy()
        preview = preview.where(pd.notna(preview), None)
        records: list[dict[str, object]] = []
        for row in preview.to_dict(orient="records"):
            normalized: dict[str, object] = {}
            for key, value in row.items():
                normalized[str(key)] = MappingService._json_safe_value(value)
            records.append(normalized)
        return records

    @staticmethod
    def _json_safe_value(value: object) -> object:
        if pd.isna(value):
            return None
        if hasattr(value, "to_pydatetime"):
            try:
                return value.to_pydatetime().isoformat()
            except Exception:
                return str(value)
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list, tuple)):
            try:
                value = value.item()
            except Exception:
                pass
        if isinstance(value, (int, float, str, bool)) or value is None:
            return value
        if isinstance(value, (list, tuple)):
            return [MappingService._json_safe_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): MappingService._json_safe_value(item) for key, item in value.items()}
        return str(value)
