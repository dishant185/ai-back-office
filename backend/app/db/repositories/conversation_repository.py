"""Conversation and Message repository using MongoDB with strict multi-tenant account isolation."""
from __future__ import annotations

import datetime
import uuid
from typing import Any
from app.db.database import get_conversations_collection, get_messages_collection


class ConversationRepository:
    def __init__(self) -> None:
        self.conv_collection = get_conversations_collection()
        self.msg_collection = get_messages_collection()

    def create_conversation(
        self,
        account_id: str,
        user_id: str,
        dataset_id: str | None = None,
        title: str = "New Analysis",
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "conversation_id": conv_id,
            "session_id": conv_id,  # compatibility alias
            "account_id": account_id,
            "user_id": user_id,
            "dataset_id": dataset_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        self.conv_collection.insert_one(doc)
        return doc

    def get_conversation(self, conversation_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"$or": [{"conversation_id": conversation_id}, {"session_id": conversation_id}]}
        if account_id:
            query["account_id"] = account_id
        return self.conv_collection.find_one(query)

    def get_by_id(self, conversation_id: str, account_id: str | None = None) -> dict[str, Any] | None:
        return self.get_conversation(conversation_id=conversation_id, account_id=account_id)


    def list_conversations(self, account_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return list(
            self.conv_collection.find({"account_id": account_id})
            .sort("updated_at", -1)
            .limit(limit)
        )

    def add_message(
        self,
        conversation_id: str,
        account_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        query_plan: dict[str, Any] | None = None,
        verified_result: dict[str, Any] | None = None,
        sources: list[dict[str, Any]] | None = None,
        limitations: list[str] | None = None,
        insights: list[str] | None = None,
        recommendations: list[str] | None = None,
    ) -> dict[str, Any]:
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc = {
            "message_id": msg_id,
            "conversation_id": conversation_id,
            "account_id": account_id,
            "role": role,
            "content": content,
            "intent": intent,
            "query_plan": query_plan,
            "verified_result": verified_result,
            "sources": sources or [],
            "limitations": limitations or [],
            "insights": insights or [],
            "recommendations": recommendations or [],
            "created_at": now,
        }
        self.msg_collection.insert_one(doc)

        # Update conversation updated_at
        self.conv_collection.update_one(
            {"$or": [{"conversation_id": conversation_id}, {"session_id": conversation_id}]},
            {"$set": {"updated_at": now}},
        )
        return doc

    def get_messages(self, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return list(
            self.msg_collection.find({"conversation_id": conversation_id})
            .sort("created_at", 1)
            .limit(limit)
        )
