"""AI Analyst session and messaging endpoints."""
from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.service import AnalystSession, SessionStore
from app.core.deps import get_optional_user
from app.db.repositories.conversation_repository import ConversationRepository

router = APIRouter()


class CreateSessionRequest(BaseModel):
    dataset_id: str
    report_context: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    message: str


@router.post("/sessions")
async def create_analyst_session(
    payload: CreateSessionRequest,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Create a new analyst session linked to a dataset."""
    try:
        session = SessionStore.create(
            dataset_id=payload.dataset_id,
            report_context=payload.report_context,
        )
        account_id = str(current_user.get("account_id")) if current_user and current_user.get("account_id") else "account_default"
        user_id = str(current_user.get("id")) if current_user else "guest"

        # Persist conversation in MongoDB
        try:
            ConversationRepository().create_conversation(
                account_id=account_id,
                user_id=user_id,
                dataset_id=payload.dataset_id,
                title=f"Chat on {payload.dataset_id}",
                conversation_id=session.session_id,
            )
        except Exception:
            pass

        return session.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sessions/{session_id}")
async def get_analyst_session(session_id: str) -> dict[str, Any]:
    """Get an existing analyst session."""
    session = SessionStore.get(session_id)
    if not session:
        # Check MongoDB repository
        conv = ConversationRepository().get_by_id(session_id)
        if conv:
            return {
                "session_id": session_id,
                "dataset_id": conv.get("dataset_id"),
                "message_count": 0,
                "created_at": conv.get("created_at"),
            }
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.post("/sessions/{session_id}/messages")
async def send_analyst_message(
    session_id: str,
    payload: SendMessageRequest,
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Send a message to the AI analyst and get a grounded response."""
    session = SessionStore.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await session.send_message(user_msg)

    # Persist user message and assistant response in MongoDB
    try:
        repo = ConversationRepository()
        repo.add_message(
            conversation_id=session_id,
            role="user",
            content=user_msg,
        )
        repo.add_message(
            conversation_id=session_id,
            role="assistant",
            content=response.answer,
            metadata={"sources": response.sources},
        )
    except Exception:
        pass

    # Determine status
    if "unavailable" in [l.lower() for l in response.limitations]:
        status_val = "unavailable"
    elif "clarification" in response.answer.lower() and "?" in response.answer:
        status_val = "clarification"
    else:
        status_val = "verified"

    return {
        "status": status_val,
        "ai_status": response.ai_status,
        "answer": response.answer,
        "dataset_id": session.dataset_id,
        "sources": response.sources,
        "insights": response.insights,
        "recommendations": response.recommendations,
        "limitations": response.limitations,
    }
