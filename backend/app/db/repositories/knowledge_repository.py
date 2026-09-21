"""Dataset Knowledge package repository using MongoDB."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_dataset_knowledge_collection


class KnowledgeRepository:
    def __init__(self) -> None:
        self.collection = get_dataset_knowledge_collection()

    def save_knowledge(
        self,
        dataset_id: str,
        account_id: str,
        package: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "dataset_id": dataset_id,
            "account_id": account_id,
            "package": package,
            "updated_at": now,
        }
        self.collection.update_one(
            {"dataset_id": dataset_id},
            {"$set": doc, "$setOnInsert": {"id": f"knw_{uuid.uuid4().hex[:12]}", "created_at": now}},
            upsert=True,
        )
        return doc

    def get_knowledge(self, dataset_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"dataset_id": dataset_id}
        if account_id:
            query["account_id"] = account_id
        return self.collection.find_one(query)
