"""Validates that LLM responses do not leak internal prompts or system metadata."""
from __future__ import annotations

import re


class ResponseValidator:
    """Detects information leaks or invalid responses."""

    LEAK_PATTERNS = [
        r"SYSTEM\s*PROMPT",
        r"query_plan",
        r"verified_result",
        r"You are the AI Business Analyst inside",
        r"never calculate business numbers yourself",
    ]

    @classmethod
    def contains_leak(cls, text: str) -> bool:
        for pat in cls.LEAK_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False
