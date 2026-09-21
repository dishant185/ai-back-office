"""Multi-Turn Conversation Context & Pronoun Reference Resolver.

Resolves conversational follow-up references such as:
- 'Which one has the most?' -> refers to the previously queried dimension (e.g. region)
- 'What about East?' -> checks East within the previous dimension context
- 'Compare them' -> compares the top 2 entities discussed in recent turns
- 'How much revenue did it generate?' -> resolves 'it' to the current focus entity
- 'The first one', 'the second one', 'that product', 'that region'
"""
from __future__ import annotations

import re
from typing import Any


class ConversationTurn:
    """Represents a single conversation exchange."""
    def __init__(
        self,
        user_message: str,
        assistant_answer: str,
        focus_dimension: str | None = None,
        focus_entities: list[str] | None = None,
        focus_metric: str | None = None,
    ):
        self.user_message = user_message
        self.assistant_answer = assistant_answer
        self.focus_dimension = focus_dimension
        self.focus_entities = focus_entities or []
        self.focus_metric = focus_metric


class ContextualState:
    """Active conversational state containing dimensions, entities, and metrics."""
    def __init__(
        self,
        focus_dimension: str | None,
        focus_entities: list[str],
        focus_metric: str | None,
        last_metric_value: Any = None,
    ):
        self.focus_dimension = focus_dimension
        self.focus_entities = focus_entities
        self.mentioned_entities = focus_entities
        self.focus_metric = focus_metric
        self.last_metric_value = last_metric_value

    def __iter__(self):
        return iter((self.focus_dimension, self.focus_entities, self.focus_metric))


def extract_contextual_state(
    user_message_or_history: str | list[dict[str, Any]],
    assistant_answer: str = "",
    context: dict[str, Any] | None = None,
) -> ContextualState:
    """Extract the active dimension, entities, and metrics from a conversation turn or message history."""
    if isinstance(user_message_or_history, list):
        history = user_message_or_history
        last_user = next((m.get("content", "") for m in reversed(history) if m.get("role") == "user"), "")
        last_asst_msg = next((m for m in reversed(history) if m.get("role") == "assistant"), {})
        user_message = last_user
        assistant_answer = last_asst_msg.get("content", "")
        # Check metrics dict in assistant message if present
        msg_metrics = last_asst_msg.get("metrics", {})
        metric_val = list(msg_metrics.values())[-1] if msg_metrics else None
    else:
        user_message = user_message_or_history
        metric_val = None

    dimensions = context.get("dimensions", {}) if context else {}
    metrics = context.get("metrics", {}) if context else {}

    u_lower = user_message.lower()
    a_lower = assistant_answer.lower()

    # 1. Detect focus dimension
    focus_dim = None
    for dim_name in dimensions.keys():
        d_clean = dim_name.lower()
        if d_clean in u_lower or d_clean in a_lower:
            focus_dim = dim_name
            break

    if not focus_dim:
        # Check standard candidates
        for cand in ["region", "city", "product", "category", "department", "education", "state"]:
            if cand in u_lower:
                matched_dim = next((d for d in dimensions if cand in d.lower()), cand)
                focus_dim = matched_dim
                break

    # 2. Detect focus entities from dimension values or text
    focus_entities: list[str] = []
    if focus_dim and focus_dim in dimensions:
        dim_data = dimensions[focus_dim]
        for ent_name in dim_data.keys():
            if ent_name.lower() in u_lower or ent_name.lower() in a_lower:
                if ent_name not in focus_entities:
                    focus_entities.append(ent_name)

    # If no entities detected from dimension, extract named capitalized words from messages
    if not focus_entities:
        for text in (user_message, assistant_answer):
            words = re.findall(r"\b[A-Z][a-z]{2,}\b", text)
            for w in words:
                if w not in [
                    "Show", "Tell", "What", "Which", "Where", "When", "Compare",
                    "Regarding", "Total", "Average", "Here", "There", "The", "And"
                ]:
                    if w not in focus_entities:
                        focus_entities.append(w)

    # 3. Detect focus metric
    focus_metric = None
    for m_name in metrics.keys():
        if m_name.replace("_", " ") in u_lower:
            focus_metric = m_name
            break
    if not focus_metric:
        if any(w in u_lower for w in ["revenue", "sales"]):
            focus_metric = "total_revenue"
        elif any(w in u_lower for w in ["profit", "margin"]):
            focus_metric = "total_profit"
        elif any(w in u_lower for w in ["employee", "headcount", "people"]):
            focus_metric = "employee_count"
        elif any(w in u_lower for w in ["attrition", "turnover"]):
            focus_metric = "attrition_rate"

    return ContextualState(focus_dim, focus_entities, focus_metric, metric_val)


def resolve_conversational_references(
    current_message: str,
    history: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Resolve pronouns and relative references into an explicit canonical query.

    Parameters
    ----------
    current_message:
        User's prompt (e.g. 'Which one has the most?', 'Compare them', 'How much revenue did it generate?').
    history:
        List of preceding message objects with roles and content.
    context:
        Active dataset canonical analytics.

    Returns
    -------
    (resolved_query_string, extracted_context_metadata)
    """
    if not history:
        return current_message, {}

    cleaned = current_message.strip()
    c_lower = cleaned.lower()

    # Find last user and assistant messages
    last_assistant_msg = next((m for m in reversed(history) if m.get("role") == "assistant"), None)
    last_user_msg = next((m for m in reversed(history) if m.get("role") == "user"), None)

    last_user_text = last_user_msg.get("content", "") if last_user_msg else ""
    last_asst_text = last_assistant_msg.get("content", "") if last_assistant_msg else ""

    focus_dim, focus_entities, focus_metric = extract_contextual_state(last_user_text, last_asst_text, context)

    # 1. "What percentage is that?", "What percent is this?"
    if re.search(r"\b(what\s+percentage\s+is\s+(that|this|it)|what\s+percent)\b", c_lower):
        if last_assistant_msg:
            return f"{cleaned} (Reference previous finding: '{last_assistant_msg.get('content', '')[:100]}')", {
                "resolved_from": "percentage_reference"
            }

    # 2. "What about its <metric>?" (e.g. "What about its quantity?")
    match_its_metric = re.search(r"^(?:what|how)\s+about\s+(?:its|their)\s+([A-Za-z0-9_\s]+)\??$", c_lower)
    if match_its_metric and focus_entities:
        target_metric = match_its_metric.group(1).strip()
        primary_entity = focus_entities[0]
        resolved = f"What is the total {target_metric} for {primary_entity}?"
        return resolved, {
            "resolved_from": "its_metric",
            "last_entity": primary_entity,
            "entity": primary_entity,
            "last_dimension": focus_dim,
            "focus_dimension": focus_dim,
            "metric": target_metric,
        }

    # 2b. "What about <Entity>?", "How about <Entity>?"
    match_about = re.search(r"^(what|how)\s+about\s+([A-Za-z0-9\s]+)\??$", c_lower)
    if match_about:
        cand_ent = match_about.group(2).strip()
        if not cand_ent.lower().startswith(("it", "its", "their")):
            entity = cand_ent.title()
            dim_target = focus_dim or "dimension"
            ref_context = f"in the context of: {last_user_text}" if last_user_text else f"in {dim_target}"
            resolved = f"Regarding {entity}, {ref_context}"
            return resolved, {"resolved_from": "what_about", "entity": entity, "last_entity": entity, "focus_dimension": dim_target, "last_dimension": dim_target}

    # 3. "Which one has the most / highest / lowest?"
    if re.search(r"\bwhich\s+(one|of\s+them)\s+(has|had|is)\s+(the\s+)?(most|highest|top|leading|best|lowest|least)\b", c_lower) or c_lower in [
        "which one has the most?", "which one has the highest?", "which is top?", "which is largest?"
    ]:
        dim_target = focus_dim or "category"
        if focus_entities:
            resolved = f"Which {dim_target} has the most records between {', '.join(focus_entities)}?"
        else:
            resolved = f"Which {dim_target} has the most records?"
        return resolved, {"resolved_from": "which_one", "focus_dimension": dim_target, "entities": focus_entities}

    # 3. "Compare them", "Compare both"
    if re.search(r"\bcompare\s+(them|both|the\s+two|these)\b", c_lower) or c_lower in ["compare them", "compare them.", "compare both"]:
        dimensions = context.get("dimensions", {}) if context else {}
        if len(focus_entities) >= 2:
            resolved = f"Compare {focus_entities[0]} and {focus_entities[1]}"
            return resolved, {"resolved_from": "compare_them", "entities": focus_entities[:2]}
        elif len(focus_entities) == 1:
            primary = focus_entities[0]
            for d_name, d_dict in dimensions.items():
                if primary in d_dict or any(k.lower() == primary.lower() for k in d_dict):
                    runner_up = next((k for k in d_dict if k.lower() != primary.lower()), None)
                    if runner_up:
                        resolved = f"Compare {primary} and {runner_up}"
                        return resolved, {"resolved_from": "compare_them", "entities": [primary, runner_up]}
        if focus_dim and focus_dim in dimensions and len(dimensions[focus_dim]) >= 2:
            top2 = list(dimensions[focus_dim].keys())[:2]
            resolved = f"Compare {top2[0]} and {top2[1]}"
            return resolved, {"resolved_from": "compare_them", "entities": top2}
        elif dimensions:
            first_dim = next(iter(dimensions.values()))
            if len(first_dim) >= 2:
                top2 = list(first_dim.keys())[:2]
                resolved = f"Compare {top2[0]} and {top2[1]}"
                return resolved, {"resolved_from": "compare_them", "entities": top2}

    # 4. "How much revenue did it generate?", "How many employees are in that city?"
    match_pronoun = re.search(r"\b(it|that|this|that\s+(region|city|product|category|department))\b", c_lower)
    if match_pronoun and focus_entities:
        primary_entity = focus_entities[0]
        # Replace 'it' or 'that' with the entity
        replaced = re.sub(r"\b(it|that|this)\b", primary_entity, cleaned, flags=re.I)
        return replaced, {"resolved_from": "pronoun_replacement", "entity": primary_entity}

    # 5. "Give me a summary", "Give me a detailed analysis" -> inherit active dimension if applicable
    if ("summary" in c_lower or "detailed analysis" in c_lower) and focus_dim and "dataset" not in c_lower:
        resolved = f"{cleaned} for {focus_dim}"
        return resolved, {"resolved_from": "dimension_context", "focus_dimension": focus_dim}

    return current_message, {"focus_dimension": focus_dim, "focus_entities": focus_entities}
