"""Account repository using MongoDB."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_accounts_collection


class AccountRepository:
    def __init__(self) -> None:
        self.collection = get_accounts_collection()

    def get_or_create_default_account(self, name: str = "Default Account") -> dict[str, Any]:
        doc = self.collection.find_one({"account_id": "acc_default"})
        if not doc:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            doc = {
                "account_id": "acc_default",
                "name": name,
                "plan": "standard",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            self.collection.insert_one(doc)
        return doc

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        return self.collection.find_one({"account_id": account_id})

    def create_account(self, name: str, plan: str = "standard") -> dict[str, Any]:
        account_id = f"acc_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "account_id": account_id,
            "name": name,
            "plan": plan,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        self.collection.insert_one(doc)
        return doc
