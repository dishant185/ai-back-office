"""Context Manager for conversational follow-ups and entity inheritance.

Resolves pronouns ('its', 'their', 'them') and follow-up metrics from previous turns.
"""
from __future__ import annotations

import re
from typing import Any


class ContextManager:
    """Maintains and resolves conversational context across multiple turns."""

    @classmethod
    def resolve_followup(
        cls,
        question: str,
        history: list[dict[str, Any]],
    ) -> tuple[str, dict[str, Any]]:
        """Extract conversational context and resolve pronouns in question.
        
        Returns (resolved_question, context_hints).
        """
        q = question.strip()
        q_lower = q.lower()
        context_hints: dict[str, Any] = {}

        if not history:
            return q, context_hints

        # Find the last assistant message and its context
        last_assistant = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_assistant = msg
                break

        if not last_assistant:
            return q, context_hints

        # Extract last mentioned entity and dimension from previous result/sources
        last_entity = last_assistant.get("entity")
        last_dim = last_assistant.get("dimension")
        last_meas = last_assistant.get("measure")

        # If not explicitly on the message, attempt to extract from text or sources
        if not last_entity:
            sources = last_assistant.get("sources", [])
            for src in sources:
                if isinstance(src, dict) and "field" in src:
                    last_dim = src["field"]

        context_hints = {
            "last_entity": last_entity,
            "last_dimension": last_dim,
            "last_measure": last_meas,
        }

        # Check for pronouns: "its", "their", "it"
        pronoun_match = re.search(r"\b(its|their|this|that|it)\b", q_lower)
        if pronoun_match and last_entity:
            # Replace pronoun with specific entity
            resolved = re.sub(r"\b(its|their|this|that|it)\b", str(last_entity), q, flags=re.IGNORECASE)
            return resolved, context_hints

        return q, context_hints
