"""AI Analyst session and messaging endpoints with strict multi-tenant authorization."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.service import SessionStore
from app.core.deps import AuthorizedScope, get_authorized_scope
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.dataset_repository import DatasetRepository

router = APIRouter()


class CreateSessionRequest(BaseModel):
    dataset_id: str
    report_context: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    message: str


@router.get("/sessions")
def list_analyst_sessions(
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> list[dict[str, Any]]:
    """List analyst sessions belonging strictly to the authenticated tenant."""
    repo = ConversationRepository()
    conversations = repo.list_conversations(account_id=scope.account_id)
    return [
        {
            "session_id": c.get("session_id") or c.get("conversation_id"),
            "dataset_id": c.get("dataset_id"),
            "title": c.get("title", "Analysis Session"),
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
        }
        for c in conversations
    ]


@router.post("/sessions")
async def create_analyst_session(
    payload: CreateSessionRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Create a new analyst session strictly linked to an authorized dataset."""
    # Verify dataset ownership
    dataset_repo = DatasetRepository()
    ds = dataset_repo.get_by_id(payload.dataset_id, account_id=scope.account_id)
    if not ds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or unauthorized.",
        )

    try:
        session = SessionStore.create(
            dataset_id=payload.dataset_id,
            report_context=payload.report_context,
        )

        # Persist conversation in MongoDB
        try:
            ConversationRepository().create_conversation(
                account_id=scope.account_id,
                user_id=scope.user_id,
                dataset_id=payload.dataset_id,
                title=f"Chat on {ds.get('filename') or ds.get('file_name') or payload.dataset_id}",
                conversation_id=session.session_id,
            )
        except Exception:
            pass

        return session.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/sessions/{session_id}")
async def get_analyst_session(
    session_id: str,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Get an existing analyst session strictly scoped to the tenant."""
    conv_repo = ConversationRepository()
    conv = conv_repo.get_conversation(session_id, account_id=scope.account_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    session = SessionStore.get(session_id)
    if session:
        return session.to_dict()

    return {
        "session_id": session_id,
        "dataset_id": conv.get("dataset_id"),
        "message_count": len(conv_repo.get_messages(session_id)),
        "created_at": conv.get("created_at"),
    }


@router.post("/sessions/{session_id}/messages")
async def send_analyst_message(
    session_id: str,
    payload: SendMessageRequest,
    scope: AuthorizedScope = Depends(get_authorized_scope),
) -> dict[str, Any]:
    """Send a message to the AI analyst and get a grounded response strictly scoped to tenant."""
    conv_repo = ConversationRepository()
    conv = conv_repo.get_conversation(session_id, account_id=scope.account_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    session = SessionStore.get(session_id)
    if not session:
        # Rehydrate session if available
        ds_id = conv.get("dataset_id")
        if ds_id:
            session = SessionStore.create(dataset_id=ds_id)
            session.session_id = session_id
            SessionStore._sessions[session_id] = session
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session expired or not found.")

    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    response = await session.send_message(user_msg)

    # Persist user message and assistant response in MongoDB with account_id
    try:
        conv_repo.add_message(
            conversation_id=session_id,
            account_id=scope.account_id,
            role="user",
            content=user_msg,
        )
        conv_repo.add_message(
            conversation_id=session_id,
            account_id=scope.account_id,
            role="assistant",
            content=response.answer,
            sources=response.sources,
            limitations=response.limitations,
            insights=response.insights,
            recommendations=response.recommendations,
        )
    except Exception:
        pass

    # Determine status
    if any("rejected" in l.lower() or "safety" in l.lower() for l in response.limitations) or "could not be verified" in response.answer.lower():
        status_val = "rejected"
    elif "unavailable" in [l.lower() for l in response.limitations]:
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
