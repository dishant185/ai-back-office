"""Dataset Schema repository using MongoDB."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_dataset_schemas_collection


class SchemaRepository:
    def __init__(self) -> None:
        self.collection = get_dataset_schemas_collection()

    def save_schema(
        self,
        dataset_id: str,
        account_id: str,
        columns: list[dict[str, Any]],
        quality_issues: list[str] | None = None,
    ) -> dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "dataset_id": dataset_id,
            "account_id": account_id,
            "columns": columns,
            "quality_issues": quality_issues or [],
            "updated_at": now,
        }
        self.collection.update_one(
            {"dataset_id": dataset_id},
            {"$set": doc, "$setOnInsert": {"id": f"sch_{uuid.uuid4().hex[:12]}", "created_at": now}},
            upsert=True,
        )
        return doc

    def get_schema(self, dataset_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"dataset_id": dataset_id}
        if account_id:
            query["account_id"] = account_id
        return self.collection.find_one(query)
