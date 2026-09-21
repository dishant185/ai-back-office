"""AI Analyst session management.

Manages conversation sessions that link a dataset to a series of
analyst Q&A exchanges. Uses in-memory storage to avoid heavy
database overhead. Supports multi-turn contextual resolution.
"""
from __future__ import annotations

import datetime
import re
import uuid
from typing import Any

from app.ai.analyst import analyze_question
from app.ai.context_builder import build_context_from_dataset_id
from app.ai.conversation_context import resolve_conversational_references
from app.ai.validators import AnalystResponse


def resolve_followup_question(user_message: str, history: list[dict[str, Any]], context: dict[str, Any]) -> str:
    """Resolve pronouns and contextual references from previous turns using conversation_context."""
    resolved_query, _ = resolve_conversational_references(user_message, history, context)
    return resolved_query


class AnalystSession:
    """A single analyst conversation session."""

    def __init__(self, dataset_id: str, report_context: dict[str, Any] | None = None) -> None:
        self.session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.dataset_id = dataset_id
        self.report_context = report_context
        self.messages: list[dict[str, Any]] = []
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = self.created_at
        self._context_cache: dict[str, Any] | None = None

    def get_context(self) -> dict[str, Any]:
        """Load or return cached analytics context."""
        if self._context_cache is None:
            try:
                self._context_cache = build_context_from_dataset_id(
                    self.dataset_id,
                    report_context=self.report_context,
                )
            except FileNotFoundError:
                self._context_cache = {"error": "Dataset not found"}
        return self._context_cache

    async def send_message(self, user_message: str) -> AnalystResponse:
        """Process a user message and return the AI response."""
        context = self.get_context()
        resolved_question = resolve_followup_question(user_message, self.messages, context)

        self.messages.append({
            "role": "user",
            "content": user_message,
            "resolved_content": resolved_question if resolved_question != user_message else None,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

        response = await analyze_question(
            resolved_question,
            self.dataset_id,
            report_context=self.report_context,
            conversation_history=self.messages,
        )

        self.messages.append({
            "role": "assistant",
            "content": response.answer,
            "insights": response.insights,
            "recommendations": response.recommendations,
            "sources": response.sources,
            "limitations": response.limitations,
            "entity": response.entity,
            "dimension": response.dimension,
            "measure": response.measure,
            "ai_status": response.ai_status,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return response

    def to_dict(self) -> dict[str, Any]:
        """Serialise session for API response."""
        context = self.get_context()
        return {
            "session_id": self.session_id,
            "dataset_id": self.dataset_id,
            "profile": context.get("profile", "unknown"),
            "row_count": context.get("row_count", 0),
            "capabilities": context.get("capabilities", []),
            "metrics": context.get("metrics", {}),
            "dimensions": context.get("dimensions", {}),
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionStore:
    """In-memory session store. Simple, lightweight, no DB."""

    _sessions: dict[str, AnalystSession] = {}

    @classmethod
    def create(cls, dataset_id: str, report_context: dict[str, Any] | None = None) -> AnalystSession:
        session = AnalystSession(dataset_id, report_context)
        cls._sessions[session.session_id] = session
        # Limit stored sessions to prevent memory bloat
        if len(cls._sessions) > 100:
            oldest_key = next(iter(cls._sessions))
            del cls._sessions[oldest_key]
        return session

    @classmethod
    def get(cls, session_id: str) -> AnalystSession | None:
        return cls._sessions.get(session_id)

    @classmethod
    def list_sessions(cls) -> list[dict[str, Any]]:
        return [s.to_dict() for s in cls._sessions.values()]
