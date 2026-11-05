"""Shared test fixtures."""

import pytest

from backend.app.api.throttle import _TIERS
from backend.app.rate_limiter import default_limiter, strict_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Clear all rate-limiter state before each test."""
    default_limiter.reset()
    strict_limiter.reset()
    for limiter in _TIERS.values():
        limiter.reset()
    yield
