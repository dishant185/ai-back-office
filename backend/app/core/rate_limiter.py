"""In-memory rate limiter for authentication endpoints.

Prevents credential brute-forcing by tracking failed login attempts per (IP, email).
"""
from __future__ import annotations

import logging
import threading
import time
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class LoginRateLimiter:
    """Thread-safe rate limiter tracking failed login attempts."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,  # 15 minutes
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[tuple[str, str], list[float]] = {}
        self._lock = threading.Lock()

    def _get_key(self, ip: str, email: str) -> tuple[str, str]:
        return (ip.strip().lower(), email.strip().lower())

    def check_rate_limit(self, ip: str, email: str) -> None:
        """Check if (ip, email) is locked out. Raises HTTP 429 if limit exceeded."""
        key = self._get_key(ip, email)
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._failures.get(key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._failures[key] = valid_timestamps

            if len(valid_timestamps) >= self.max_attempts:
                logger.warning(
                    "Brute-force lockout triggered for IP '%s', email '%s' (%d failed attempts in %ds).",
                    ip,
                    email,
                    len(valid_timestamps),
                    self.window_seconds,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again later.",
                )

    def record_failure(self, ip: str, email: str) -> None:
        """Record a failed login attempt."""
        key = self._get_key(ip, email)
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._failures.get(key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]
            valid_timestamps.append(now)
            self._failures[key] = valid_timestamps

    def record_success(self, ip: str, email: str) -> None:
        """Clear failure history upon successful authentication."""
        key = self._get_key(ip, email)
        with self._lock:
            self._failures.pop(key, None)

    def reset(self) -> None:
        """Reset all rate limiter states (useful for testing)."""
        with self._lock:
            self._failures.clear()


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=900)


def extract_client_ip(request: Request) -> str:
    """Extract client IP respecting X-Forwarded-For if available."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
