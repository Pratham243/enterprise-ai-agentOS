"""Rate limiter — sliding window counter per client IP.

Protects the API from abuse by capping how many requests a client
can make within a time window. Different limits can be applied to
different route groups (e.g. stricter for LLM-backed endpoints).

Usage:
    from backend.app.rate_limiter import RateLimiter, rate_limit

    limiter = RateLimiter(max_requests=60, window_seconds=60)

    @router.post("/agent/query")
    async def query(req: Request, _=Depends(rate_limit(limiter))):
        ...
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Depends, Request

from backend.app.exceptions import RateLimitError


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]

    def reset(self) -> None:
        """Clear all tracked requests (useful for testing)."""
        with self._lock:
            self._requests.clear()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """Check if a request is allowed. Returns (allowed, remaining)."""
        now = time.monotonic()
        with self._lock:
            self._cleanup(key, now)
            count = len(self._requests[key])
            remaining = max(0, self.max_requests - count)
            if count >= self.max_requests:
                return False, 0
            self._requests[key].append(now)
            return True, remaining - 1


# Pre-configured limiters for different route groups
default_limiter = RateLimiter(max_requests=60, window_seconds=60)
strict_limiter = RateLimiter(max_requests=10, window_seconds=60)


def rate_limit(limiter: RateLimiter | None = None):
    """FastAPI dependency that enforces rate limiting."""
    _limiter = limiter or default_limiter

    async def _check(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining = _limiter.is_allowed(client_ip)

        if not allowed:
            raise RateLimitError(retry_after=_limiter.window_seconds)

    return Depends(_check)
