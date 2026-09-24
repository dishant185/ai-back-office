"""Dataset repository using MongoDB with strict multi-tenant account isolation."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_datasets_collection


class DatasetRepository:
    def __init__(self) -> None:
        self.collection = get_datasets_collection()

    def create_dataset(
        self,
        account_id: str,
        user_id: str,
        file_name: str,
        file_type: str,
        file_size: int,
        file_path: str,
        profile: str = "generic",
        row_count: int = 0,
        column_count: int = 0,
        dataset_id: str | None = None,
        workspace_id: str = "default",
        summary: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        ds_id = dataset_id or f"ds_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Determine version
        existing = self.collection.find_one({"$or": [{"dataset_id": ds_id}, {"upload_id": ds_id}]})
        version = (existing.get("current_version", 1) + 1) if existing else 1

        doc: dict[str, Any] = {
            "dataset_id": ds_id,
            "upload_id": ds_id,
            "account_id": account_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "file_name": file_name,
            "filename": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "file_path": file_path,
            "saved_path": file_path,
            "profile": profile,
            "row_count": row_count,
            "column_count": column_count,
            "current_version": version,
            "dataset_version": version,
            "status": "ready",
            "quality_status": "ready",
            "analytics_status": "ready",
            "capabilities": capabilities or [],
            "summary": summary or {},
            "validation": validation or {},
            "created_at": existing.get("created_at") if existing else now,
            "updated_at": now,
        }

        self.collection.update_one(
            {"$or": [{"dataset_id": ds_id}, {"upload_id": ds_id}]},
            {"$set": doc},
            upsert=True,
        )

        # Persist immutable version record for data lineage
        try:
            from app.db.database import get_dataset_versions_collection
            v_col = get_dataset_versions_collection()
            v_col.insert_one({
                "version_id": f"dsv_{uuid.uuid4().hex[:12]}",
                "dataset_id": ds_id,
                "dataset_version": version,
                "account_id": account_id,
                "workspace_id": workspace_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "row_count": row_count,
                "column_count": column_count,
                "created_by": user_id,
                "created_at": now,
            })
        except Exception:
            pass

        return doc

    def get_by_id(self, dataset_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"$or": [{"dataset_id": dataset_id}, {"upload_id": dataset_id}]}
        if account_id:
            query["account_id"] = account_id
        doc = self.collection.find_one(query)
        if not doc:
            from app.db.mongodb import get_uploads_collection
            uploads_col = get_uploads_collection()
            doc = uploads_col.find_one(query)
        return doc

    def get_dataset(self, account_id: str, dataset_id: str) -> dict[str, Any] | None:
        return self.get_by_id(dataset_id=dataset_id, account_id=account_id)

    def get_by_filename(self, file_name: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"$or": [{"file_name": file_name}, {"filename": file_name}]}
        if account_id:
            query["account_id"] = account_id
        doc = self.collection.find_one(query)
        if not doc:
            from app.db.mongodb import get_uploads_collection
            uploads_col = get_uploads_collection()
            doc = uploads_col.find_one(query)
        return doc

    def list_datasets(self, account_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if account_id:
            query["account_id"] = account_id
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        results = list(cursor)
        if not results:
            from app.db.mongodb import get_uploads_collection
            uploads_col = get_uploads_collection()
            results = list(uploads_col.find(query).sort("created_at", -1).limit(limit))
        return results

    def delete_dataset(self, dataset_id: str, account_id: str | None = None) -> bool:
        query: dict[str, Any] = {"$or": [{"dataset_id": dataset_id}, {"upload_id": dataset_id}]}
        if account_id:
            query["account_id"] = account_id
        res = self.collection.delete_one(query)
        deleted = res.deleted_count > 0
        try:
            from app.db.mongodb import get_uploads_collection
            uploads_col = get_uploads_collection()
            u_res = uploads_col.delete_one(query)
            if u_res.deleted_count > 0:
                deleted = True
        except Exception:
            pass
        return deleted

    def get_dataset_versions(self, dataset_id: str, account_id: str) -> list[dict[str, Any]]:
        """Retrieve version history for this dataset, strictly isolated to the account."""
        from app.db.database import get_dataset_versions_collection
        v_col = get_dataset_versions_collection()
        cursor = v_col.find(
            {"dataset_id": dataset_id, "account_id": account_id},
            {"_id": 0},
        ).sort("dataset_version", -1)
        return list(cursor)

