"""Tenant data migration script to ensure all existing documents are strictly isolated."""
from __future__ import annotations

import datetime
import logging
from typing import Any

from app.db.database import (
    get_accounts_collection,
    get_database,
    get_mappings_collection,
    get_reports_collection,
    get_uploads_collection,
    get_users_collection,
)

logger = logging.getLogger(__name__)


def migrate_tenant_data() -> None:
    """Migrate legacy un-scoped or default-scoped records to strict multi-tenant ownership."""
    try:
        users_col = get_users_collection()
        accounts_col = get_accounts_collection()
        uploads_col = get_uploads_collection()
        reports_col = get_reports_collection()
        mappings_col = get_mappings_collection()
        db = get_database()
        raw_uploads = db["uploads"]

        user_account_map: dict[str, str] = {}
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Ensure all users have explicit account_id and workspace_id
        for user in users_col.find():
            user_id = str(user.get("id") or user.get("user_id") or "")
            if not user_id:
                continue

            acc_id = user.get("account_id")
            if not acc_id or acc_id == "account_default":
                acc_id = f"acc_{user_id[4:] if user_id.startswith('usr_') else user_id}"
                users_col.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"account_id": acc_id, "workspace_id": "default", "user_id": user_id}},
                )
            user_account_map[user_id] = acc_id

            # Ensure account document exists
            accounts_col.update_one(
                {"account_id": acc_id},
                {
                    "$set": {
                        "account_id": acc_id,
                        "name": user.get("organization") or f"{user.get('name', 'User')}'s Workspace",
                        "owner_user_id": user_id,
                        "updated_at": now_iso,
                    },
                    "$setOnInsert": {
                        "created_at": now_iso,
                        "is_active": True,
                        "plan": "standard",
                    },
                },
                upsert=True,
            )

        # 2. Backfill uploads (both in uploads and datasets collections)
        for user_id, acc_id in user_account_map.items():
            uploads_col.update_many(
                {"user_id": user_id, "$or": [{"account_id": {"$exists": False}}, {"account_id": "account_default"}]},
                {"$set": {"account_id": acc_id, "workspace_id": "default"}},
            )
            raw_uploads.update_many(
                {"user_id": user_id, "$or": [{"account_id": {"$exists": False}}, {"account_id": "account_default"}]},
                {"$set": {"account_id": acc_id, "workspace_id": "default"}},
            )

        # 3. Backfill reports
        for user_id, acc_id in user_account_map.items():
            reports_col.update_many(
                {"user_id": user_id, "$or": [{"account_id": {"$exists": False}}, {"account_id": "account_default"}]},
                {"$set": {"account_id": acc_id, "workspace_id": "default"}},
            )

        # 4. Backfill mappings
        for user_id, acc_id in user_account_map.items():
            mappings_col.update_many(
                {"user_id": user_id, "$or": [{"account_id": {"$exists": False}}, {"account_id": "account_default"}]},
                {"$set": {"account_id": acc_id, "workspace_id": "default"}},
            )

        # 5. Sync raw uploads into datasets collection if needed
        for doc in raw_uploads.find():
            ds_id = doc.get("upload_id") or doc.get("dataset_id")
            if ds_id and not uploads_col.find_one({"$or": [{"dataset_id": ds_id}, {"upload_id": ds_id}]}):
                cleaned_doc = dict(doc)
                cleaned_doc.pop("_id", None)
                cleaned_doc["dataset_id"] = ds_id
                uploads_col.insert_one(cleaned_doc)

        logger.info("Multi-tenant data migration completed successfully for %d users.", len(user_account_map))
    except Exception as exc:
        logger.warning("Could not complete tenant data migration: %s", exc)


if __name__ == "__main__":
    migrate_tenant_data()
