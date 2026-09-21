"""Dataset Knowledge Repository for AI Back-Office Copilot.

Manages persistence, caching, and retrieval of Dataset Knowledge documents in MongoDB,
strictly enforcing multi-tenant isolation (tenant_id, account_id).
"""
from __future__ import annotations

from typing import Any
from app.db.mongodb import get_database


class DatasetKnowledgeRepository:
    """Repository for storing and querying DatasetKnowledge documents in MongoDB."""

    COLLECTION_NAME = "dataset_knowledge"

    def __init__(self) -> None:
        self.db = get_database()

    def save_knowledge(self, knowledge_dict: dict[str, Any]) -> str:
        """Upsert a dataset knowledge document keyed by (tenant_id, dataset_id, dataset_version)."""
        dataset_id = knowledge_dict.get("dataset_id")
        account_id = knowledge_dict.get("account_id", "account_default")
        tenant_id = knowledge_dict.get("tenant_id") or account_id
        version = knowledge_dict.get("dataset_version", 1)

        filter_query = {
            "dataset_id": dataset_id,
            "account_id": account_id,
            "dataset_version": version,
        }
        update_doc = {"$set": knowledge_dict}

        res = self.db[self.COLLECTION_NAME].update_one(filter_query, update_doc, upsert=True)
        return str(res.upserted_id or dataset_id)

    def get_knowledge(
        self,
        dataset_id: str,
        account_id: str = "account_default",
        dataset_version: int | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve dataset knowledge document matching tenant and dataset."""
        query: dict[str, Any] = {
            "dataset_id": dataset_id,
        }
        if account_id:
            query["account_id"] = account_id
        if dataset_version is not None:
            query["dataset_version"] = dataset_version

        # Sort by version desc to get latest if version not specified
        doc = self.db[self.COLLECTION_NAME].find_one(query, sort=[("dataset_version", -1)])
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def list_knowledge_for_account(self, account_id: str) -> list[dict[str, Any]]:
        """List all dataset knowledge documents for an account."""
        cursor = self.db[self.COLLECTION_NAME].find({"account_id": account_id})
        results = []
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    def delete_knowledge(self, dataset_id: str, account_id: str) -> int:
        """Delete knowledge documents upon dataset deletion."""
        res = self.db[self.COLLECTION_NAME].delete_many({
            "dataset_id": dataset_id,
            "account_id": account_id,
        })
        return res.deleted_count
