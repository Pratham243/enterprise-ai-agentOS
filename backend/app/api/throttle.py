"""Per-endpoint request throttling with standard rate-limit headers.

Wraps the existing RateLimiter to inject RFC-style response headers
so API consumers can self-regulate:

    X-RateLimit-Limit     — max requests allowed in the window
    X-RateLimit-Remaining — requests left in the current window
    X-RateLimit-Reset     — seconds until the window resets

Usage:
    from backend.app.api.throttle import throttle

    @router.post("/agent/query")
    async def query(request: AgentQueryRequest,
                    _throttle=throttle("strict")):
        ...

Tiers:
    "strict"  — 10 requests / 60 seconds  (LLM-backed endpoints)
    "default" — 60 requests / 60 seconds  (standard endpoints)
    "relaxed" — 200 requests / 60 seconds (read-heavy / polling)
"""

import math
import time

from fastapi import Depends, Request, Response

from backend.app.exceptions import RateLimitError
from backend.app.rate_limiter import RateLimiter


_TIERS: dict[str, RateLimiter] = {
    "strict": RateLimiter(max_requests=10, window_seconds=60),
    "default": RateLimiter(max_requests=60, window_seconds=60),
    "relaxed": RateLimiter(max_requests=200, window_seconds=60),
}


def throttle(tier: str = "default"):
    """Return a FastAPI dependency that enforces a throttle tier."""
    limiter = _TIERS.get(tier)
    if limiter is None:
        raise ValueError(f"Unknown throttle tier: {tier}")

    async def _check(request: Request, response: Response):
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining = limiter.is_allowed(client_ip)

        response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(limiter.window_seconds)

        if not allowed:
            raise RateLimitError(retry_after=limiter.window_seconds)

    return Depends(_check)
