import pytest
from app.ai.conversation_context import resolve_conversational_references, extract_contextual_state

def test_extract_contextual_state_from_messages():
    history = [
        {"role": "user", "content": "How are sales in the North and South regions?"},
        {
            "role": "assistant",
            "content": "North generated 1200 sales and South generated 850 sales.",
            "metrics": {"North_sales": 1200, "South_sales": 850}
        }
    ]
    state = extract_contextual_state(history)
    assert "North" in state.mentioned_entities
    assert "South" in state.mentioned_entities
    assert state.last_metric_value in [1200, 850]

def test_resolve_which_one_has_the_most():
    history = [
        {"role": "user", "content": "Tell me about regions"},
        {
            "role": "assistant",
            "content": "We tracked East and West regions.",
            "metrics": {"East": 100, "West": 500}
        }
    ]
    resolved, explanation = resolve_conversational_references("Which one has the most?", history)
    assert "highest" in resolved.lower() or "most" in resolved.lower()
    assert "East" in resolved or "West" in resolved

def test_resolve_what_about_entity():
    history = [
        {"role": "user", "content": "How is Mumbai performing?"},
        {"role": "assistant", "content": "Mumbai has 500 active orders."}
    ]
    resolved, explanation = resolve_conversational_references("What about Pune?", history)
    assert "Regarding Pune" in resolved

def test_resolve_compare_them():
    history = [
        {"role": "user", "content": "Show me North and South performance"},
        {"role": "assistant", "content": "North had 400 sales, South had 350 sales."}
    ]
    resolved, explanation = resolve_conversational_references("Compare them", history)
    assert "Compare" in resolved
    assert "North" in resolved
    assert "South" in resolved

def test_resolve_what_percentage_is_that():
    history = [
        {"role": "user", "content": "What is the return rate?"},
        {"role": "assistant", "content": "Returns count is 45 out of 500 total orders."}
    ]
    resolved, explanation = resolve_conversational_references("What percentage is that?", history)
    assert "percentage" in resolved.lower()
