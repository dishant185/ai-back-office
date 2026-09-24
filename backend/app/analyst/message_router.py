"""Three-Level Message Router for Hybrid AI Business Analyst.

Classifies incoming user messages into:
  - PATH_A_FAST_DETERMINISTIC: Instant in-memory deterministic queries (COUNT, SUM, AVG, simple Top-N).
  - PATH_B_NLP_SEMANTIC: Natural language questions needing entity/synonym extraction and semantic resolution.
  - PATH_C_LLM_CONVERSATION: Qualitative explanation, causation, recommendations, and complex reasoning.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel

from app.data.semantic.schema_builder import SemanticSchema


class RoutingDecision(BaseModel):
    path: str  # "PATH_A_FAST_DETERMINISTIC", "PATH_B_NLP_SEMANTIC", "PATH_C_LLM_CONVERSATION"
    intent: str
    confidence: float = 1.0
    reason: str = ""


class MessageRouter:
    """Routes user messages to the optimal analytical or conversational path."""

    @classmethod
    def route(
        cls,
        question: str,
        schema: SemanticSchema,
        context_hints: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        q = question.strip()
        q_lower = q.lower()

        # 1. Path C: Qualitative, Causal, Recommendation, or Complex Reasoning Inquiries
        causal_pattern = r"\b(why|how come|reason for|root cause|causal|explain why)\b"
        rec_pattern = r"\b(what should|recommend|recommendation|advice|suggest|actionable|next step)\b"
        expl_pattern = r"\b(explain\b(?!.*how many|.*how much)|synthesize|interpret|qualitative|deep dive)\b"

        if re.search(causal_pattern, q_lower) and not re.search(r"\b(how many|how much)\b", q_lower):
            return RoutingDecision(
                path="PATH_C_LLM_CONVERSATION",
                intent="CAUSAL_EXPLANATION",
                confidence=0.92,
                reason="Question asks for causal explanation or qualitative rationale.",
            )

        if re.search(rec_pattern, q_lower):
            return RoutingDecision(
                path="PATH_C_LLM_CONVERSATION",
                intent="RECOMMENDATION",
                confidence=0.90,
                reason="Question requests operational or strategic recommendations.",
            )

        if re.search(expl_pattern, q_lower):
            return RoutingDecision(
                path="PATH_C_LLM_CONVERSATION",
                intent="EXPLANATION",
                confidence=0.88,
                reason="Question requests conceptual or methodological explanation.",
            )

        # 2. Check query plan for deterministic resolution
        from app.analyst.query_planner import QueryPlanner
        plan = QueryPlanner.plan(q, schema, context_hints)

        deterministic_intents = {
            "COUNT", "COUNT_UNIQUE", "SUM", "AVERAGE", "MEDIAN",
            "MINIMUM", "MAXIMUM", "DERIVED_METRIC", "LIST_UNIQUE",
            "TOP_ENTITY", "BOTTOM_ENTITY", "SHARE", "COMPARISON",
            "ANOMALY", "MISSING_DATA_AUDIT", "QUALITY", "DUPLICATE_CHECK", "SCHEMA"
        }

        if plan.status == "READY" and plan.intent in deterministic_intents:
            # Concise queries without conversational explanations go straight to Path A (Fast Deterministic)
            is_simple_question = len(q.split()) <= 10 and not re.search(r"\b(why|how come|recommend|advice|suggest|explain|interpret)\b", q_lower)
            if is_simple_question:
                return RoutingDecision(
                    path="PATH_A_FAST_DETERMINISTIC",
                    intent=plan.intent,
                    confidence=plan.confidence,
                    reason=f"Direct deterministic {plan.intent} query with verified schema mapping.",
                )
            else:
                return RoutingDecision(
                    path="PATH_B_NLP_SEMANTIC",
                    intent=plan.intent,
                    confidence=plan.confidence,
                    reason="Natural language question resolved to deterministic analytics plan.",
                )

        # 3. Path B: NLP / Semantic Resolution (Default for all other inquiries)
        return RoutingDecision(
            path="PATH_B_NLP_SEMANTIC",
            intent=plan.intent if plan else "SEMANTIC_ANALYTICS",
            confidence=plan.confidence if plan else 0.85,
            reason="Natural language requires entity extraction, synonym mapping, or context resolution.",
        )
