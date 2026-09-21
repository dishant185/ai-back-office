"""Parses external LLM response strings and strips extraneous formatting."""
from __future__ import annotations

import re


class ResponseParser:
    """Cleans and sanitizes raw model output strings."""

    @classmethod
    def clean_text(cls, raw: str) -> str:
        text = raw.strip()
        # Strip internal thought tags if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Strip markdown code blocks if the entire response was wrapped in ```
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1]).strip()
        return text
