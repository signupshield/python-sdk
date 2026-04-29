from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from .exceptions import SignupShieldError, SignupShieldRateLimitError, SignupShieldTimeoutError
from .types import BatchParams, BatchResult, ScoreParams, ScoreResult

DEFAULT_BASE_URL = "https://api.signupshield.dev"
DEFAULT_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 3


class SignupShield:
    """Synchronous SignupShield client.

    Example::

        client = SignupShield(api_key=os.environ["SIGNUPSHIELD_API_KEY"])
        result = client.score(email="jane@example.com", ip="8.8.8.8")
        if result.risk == "high":
            raise ValueError("Signup blocked")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise ValueError("signupshield: api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "User-Agent": "signupshield-python/1.4.0",
            },
            timeout=self._timeout,
        )

    def score(self, email: str, ip: Optional[str] = None) -> ScoreResult:
        """Score a single email + optional IP pair."""
        body: dict[str, Any] = {"email": email}
        if ip is not None:
            body["ip"] = ip
        data = self._post("/v1/score", body)
        return ScoreResult.from_dict(data)

    def batch(self, params: BatchParams) -> BatchResult:
        """Score up to 100 email + IP pairs in one request."""
        body: dict[str, Any] = {
            "items": [
                {"email": p.email, **({} if p.ip is None else {"ip": p.ip})}
                for p in params.items
            ]
        }
        data = self._post("/v1/batch", body)
        return BatchResult.from_dict(data)

    def _post(self, path: str, body: dict[str, Any], attempt: int = 0) -> dict[str, Any]:
        try:
            res = self._http.post(path, json=body)
        except httpx.TimeoutException as exc:
            raise SignupShieldTimeoutError(self._timeout) from exc

        if res.status_code == 429 and attempt < self._max_retries:
            try:
                retry_after = float(res.headers.get("Retry-After", 1))
            except (ValueError, TypeError):
                retry_after = 1.0
            if attempt == self._max_retries - 1:
                try:
                    err_body = res.json()
                except Exception:
                    err_body = {}
                raise SignupShieldRateLimitError(err_body, retry_after)
            time.sleep(retry_after)
            return self._post(path, body, attempt + 1)

        if res.status_code >= 500 and attempt < self._max_retries:
            time.sleep(2**attempt * 0.2)
            return self._post(path, body, attempt + 1)

        if not res.is_success:
            try:
                err_body = res.json()
            except Exception:
                err_body = {}
            raise SignupShieldError(res.status_code, err_body)

        return res.json()  # type: ignore[no-any-return]

    def __enter__(self) -> "SignupShield":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()
