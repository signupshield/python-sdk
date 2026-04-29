from __future__ import annotations

from typing import Optional


class SignupShieldError(Exception):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status: int, body: dict) -> None:
        self.status = status
        self.code: Optional[str] = (body.get("error") or {}).get("code")
        msg = (body.get("error") or {}).get("message") or f"SignupShield API error (HTTP {status})"
        super().__init__(msg)


class SignupShieldRateLimitError(SignupShieldError):
    """Raised after exhausting retries on HTTP 429."""

    def __init__(self, body: dict, retry_after: float) -> None:
        super().__init__(429, body)
        self.retry_after = retry_after


class SignupShieldTimeoutError(Exception):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, timeout: float) -> None:
        super().__init__(f"SignupShield request timed out after {timeout}s")
        self.timeout = timeout
