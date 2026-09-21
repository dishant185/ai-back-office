"""Tests for Multi-Turn AI Analyst Session and Context Resolution."""
from __future__ import annotations

import pytest
from app.ai.service import AnalystSession, resolve_followup_question, SessionStore


def test_resolve_followup_question():
    history = [
        {"role": "user", "content": "How many employees are in Bangalore?"},
        {"role": "assistant", "content": "There are 2,228 employees in Bangalore."},
    ]
    context = {"profile": "hr", "row_count": 4653}

    # 1. Pronoun follow up: "What percentage is that?"
    res1 = resolve_followup_question("What percentage is that?", history, context)
    assert "previous finding" in res1 or "reference" in res1.lower()

    # 2. Entity follow up: "What about Pune?"
    res2 = resolve_followup_question("What about Pune?", history, context)
    assert "Regarding Pune" in res2
    assert "Bangalore" in res2

    # 3. Direct question unchanged
    res3 = resolve_followup_question("What is total revenue?", history, context)
    assert res3 == "What is total revenue?"


def test_session_store():
    s1 = SessionStore.create("ds_test_123")
    assert s1.session_id.startswith("sess_")

    retrieved = SessionStore.get(s1.session_id)
    assert retrieved is not None
    assert retrieved.session_id == s1.session_id

    sessions = SessionStore.list_sessions()
    assert any(s["session_id"] == s1.session_id for s in sessions)
