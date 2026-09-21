"""Safety Validator for prompt injection and input sanitation."""
from __future__ import annotations

import re


class SafetyValidator:
    """Detects adversarial inputs, prompt injection attempts, and data exfiltration patterns."""

    PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?prior\s+instructions",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"system\s*:\s*you\s+are",
        r"bypass\s+safety",
        r"dump\s+database",
        r"print\s+api\s+key",
    ]

    @classmethod
    def is_safe(cls, user_input: str) -> bool:
        for pat in cls.PATTERNS:
            if re.search(pat, user_input, re.IGNORECASE):
                return False
        return True
