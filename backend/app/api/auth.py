"""JWT authentication — optional security layer for API endpoints.

When JWT_SECRET_KEY is configured, protected endpoints require a valid
Bearer token. When it's empty (development), authentication is bypassed
so the API works without any setup.

Usage:
    from backend.app.api.auth import get_current_user

    @router.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        return {"user": user}
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.config import settings
from backend.app.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT token."""
    try:
        from jose import jwt
    except ImportError:
        raise ImportError("Install python-jose: pip install python-jose[cryptography]")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI dependency that extracts the current user from a JWT.

    When JWT_SECRET_KEY is not configured, returns a default dev user
    so the API works without authentication during development.
    """
    if not settings.jwt_secret_key:
        return {"sub": "dev-user", "role": "admin"}

    if credentials is None:
        raise AuthenticationError("Missing authorization header")

    return _decode_token(credentials.credentials)
