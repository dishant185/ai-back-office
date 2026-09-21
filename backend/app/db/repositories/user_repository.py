"""User repository using MongoDB."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_users_collection


class UserRepository:
    def __init__(self) -> None:
        self.collection = get_users_collection()

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self.collection.find_one({"email": email.strip().lower()})

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.collection.find_one({"$or": [{"id": user_id}, {"user_id": user_id}, {"_id": user_id}]})

    def create_user(
        self,
        account_id: str,
        email: str,
        hashed_password: str,
        name: str = "",
        role: str = "member",
    ) -> dict[str, Any]:
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "id": user_id,
            "user_id": user_id,
            "account_id": account_id,
            "email": email.strip().lower(),
            "hashed_password": hashed_password,
            "name": name,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        self.collection.insert_one(doc)
        return doc
