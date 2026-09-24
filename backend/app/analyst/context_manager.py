"""Context Manager for conversational follow-ups, memory, and entity inheritance.

Maintains structured conversation state:
  - focus_dimension (e.g. Region, Product_ID)
  - focus_measure (e.g. sales_amount, revenue, quantity)
  - focus_entities (e.g. ['North', 'East'])
  - focus_ranking (e.g. ['North', 'East', 'West', 'South'])
  - last_intent
  - last_result
  - last_query_plan

Resolves conversational follow-ups:
  - "How much?" -> "What is the {focus_measure} of {focus_entity}?"
  - "What about the second one?" -> "Which is the second-highest {focus_dimension} by {focus_measure}?"
  - "What about the third one?" -> "Which is the third-highest {focus_dimension} by {focus_measure}?"
  - "What about East?" -> "What is the {focus_measure} of East?"
  - "Compare it with South" -> "Compare {focus_entity} and South {focus_measure}"
  - "What's the difference?" -> "What is the difference in {focus_measure} between {focus_entity_A} and {focus_entity_B}?"
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class StructuredConversationState(BaseModel):
    focus_dimension: str | None = None
    focus_measure: str | None = None
    focus_entities: list[str] = Field(default_factory=list)
    focus_ranking: list[str] = Field(default_factory=list)
    last_intent: str | None = None
    last_result_value: Any = None
    last_query_plan: dict[str, Any] | None = None


class ContextManager:
    """Maintains and resolves conversational context across multiple turns."""

    ORDINAL_MAP = {
        "first": 1, "1st": 1,
        "second": 2, "2nd": 2,
        "third": 3, "3rd": 3,
        "fourth": 4, "4th": 4,
        "fifth": 5, "5th": 5,
        "sixth": 6, "6th": 6,
        "seventh": 7, "7th": 7,
        "eighth": 8, "8th": 8,
        "ninth": 9, "9th": 9,
        "tenth": 10, "10th": 10,
    }

    @classmethod
    def extract_state(cls, history: list[dict[str, Any]]) -> StructuredConversationState:
        """Extract structured multi-turn state from history."""
        state = StructuredConversationState()
        if not history:
            return state

        # Iterate in reverse to find the most recent assistant message with context
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                # Dimension & Measure
                if not state.focus_dimension and msg.get("dimension"):
                    state.focus_dimension = msg.get("dimension")
                if not state.focus_measure and msg.get("measure"):
                    state.focus_measure = msg.get("measure")

                # Entities
                ent = msg.get("entity")
                if ent and str(ent) not in state.focus_entities:
                    state.focus_entities.append(str(ent))

                # Extract ranking items from text if present (e.g. "1. Item 1099...", "2. Item 1092...")
                text = msg.get("content") or msg.get("answer") or ""
                ranking_matches = re.findall(r"(?:^|\n)\s*(\d+)\.\s+([A-Za-z0-9_\s-]+?)(?:\s+[—–-]\s+|\s+at\s+|\s+:|\s+\$)", text)
                if ranking_matches and not state.focus_ranking:
                    state.focus_ranking = [m[1].strip() for m in ranking_matches]

                # Sources
                sources = msg.get("sources", [])
                for src in sources:
                    if isinstance(src, dict):
                        if not state.focus_dimension and src.get("field"):
                            state.focus_dimension = src.get("field")
                        if not state.focus_measure and src.get("metric"):
                            state.focus_measure = src.get("metric")

            elif msg.get("role") == "user":
                # Check user question for entities like North, South, East, West or item IDs
                u_text = msg.get("content", "")
                for region in ["North", "South", "East", "West"]:
                    if region.lower() in u_text.lower() and region not in state.focus_entities:
                        state.focus_entities.append(region)

        return state

    @classmethod
    def resolve_followup(
        cls,
        question: str,
        history: list[dict[str, Any]],
    ) -> tuple[str, dict[str, Any]]:
        """Extract conversational context and resolve pronouns or ellipsis inquiries in question.

        Returns (resolved_question, context_hints).
        """
        q = question.strip()
        q_lower = q.lower().rstrip("?")
        state = cls.extract_state(history)

        context_hints: dict[str, Any] = {
            "last_dimension": state.focus_dimension,
            "last_measure": state.focus_measure,
            "last_entity": state.focus_entities[0] if state.focus_entities else None,
            "focus_entities": state.focus_entities,
            "focus_ranking": state.focus_ranking,
        }

        if not history:
            return q, context_hints

        last_entity = state.focus_entities[0] if state.focus_entities else None
        second_entity = state.focus_entities[1] if len(state.focus_entities) > 1 else None
        dim = state.focus_dimension or "dimension"
        meas = state.focus_measure or "revenue"

        # 1. "How much?" / "How much did it generate?" / "How much did they make?"
        if re.search(r"^(how much(\s+(did\s+it\s+(generate|make)|is\s+that|was\s+that))?|what is its (revenue|sales|value))\??$", q_lower):
            if last_entity:
                resolved = f"How much {meas} did {last_entity} generate?"
                return resolved, context_hints

        # 2. "What about the second one?" / "What about the third one?" / "Show me the 2nd one"
        m_ordinal = re.search(r"\b(?:what\s+about|show\s+me|tell\s+me\s+about)?\s*the\s+(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+(?:one|entity|item|region|product)\b", q_lower)
        if m_ordinal:
            ord_word = m_ordinal.group(1).lower()
            rank_num = cls.ORDINAL_MAP.get(ord_word, 2)
            # If ranking list already known
            if state.focus_ranking and len(state.focus_ranking) >= rank_num:
                target_entity = state.focus_ranking[rank_num - 1]
                resolved = f"What is the {meas} of {target_entity}?"
                context_hints["rank"] = rank_num
                context_hints["last_entity"] = target_entity
                return resolved, context_hints
            else:
                resolved = f"Which is the {ord_word}-highest {dim} by {meas}?"
                context_hints["rank"] = rank_num
                return resolved, context_hints

        # 3. "What about <Entity>?" (e.g. "What about East?", "What about South?", "What about Item 1092?")
        m_what_about = re.search(r"^(?:what|how)\s+about\s+([A-Za-z0-9_\s-]+)\??$", q_lower)
        if m_what_about:
            cand = m_what_about.group(1).strip()
            if not any(w in cand.lower() for w in ["it", "this", "that", "them", "second", "third", "first", "fourth", "fifth"]):
                entity_title = cand.title()
                resolved = f"What is the {meas} of {entity_title}?"
                context_hints["last_entity"] = entity_title
                return resolved, context_hints

        # 4. "Compare it with South" / "Compare that with South" / "Compare with South"
        m_compare_with = re.search(r"\bcompare\s+(?:it\s+with|that\s+with|with)\s+([A-Za-z0-9_\s-]+)\b", q_lower)
        if m_compare_with and last_entity:
            target_cand = m_compare_with.group(1).strip().title()
            resolved = f"Compare {last_entity} and {target_cand} {meas}"
            context_hints["entities"] = [last_entity, target_cand]
            return resolved, context_hints

        # 5. "How much ahead of South?" / "How much ahead?" / "What's the difference?"
        if re.search(r"\b(how much ahead|what('s|\s+is)\s+the difference|difference between them)\b", q_lower):
            m_ahead_target = re.search(r"\bhow much ahead of\s+([A-Za-z0-9_\s-]+)\b", q_lower)
            if m_ahead_target and last_entity:
                target_cand = m_ahead_target.group(1).strip().title()
                resolved = f"What is the difference between {last_entity} and {target_cand} {meas}?"
                context_hints["entities"] = [last_entity, target_cand]
                return resolved, context_hints
            elif last_entity and second_entity:
                resolved = f"What is the difference between {last_entity} and {second_entity} {meas}?"
                context_hints["entities"] = [last_entity, second_entity]
                return resolved, context_hints

        # 6. Standard pronoun replacement ("it", "its", "their", "that", "this", "them")
        pronoun_match = re.search(r"\b(its|their|this|that|it|them)\b", q_lower)
        if pronoun_match and last_entity:
            resolved = re.sub(r"\b(its|their|this|that|it|them)\b", str(last_entity), q, flags=re.IGNORECASE)
            return resolved, context_hints

        return q, context_hints
