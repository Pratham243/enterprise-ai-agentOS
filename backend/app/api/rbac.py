"""Role-Based Access Control — restrict endpoints by user role.

Defines three roles with a clear hierarchy:

    admin > analyst > viewer

Use `require_role()` as a FastAPI dependency to gate endpoints:

    @router.delete("/data")
    async def delete_data(user: dict = Depends(require_role("admin"))):
        ...

In development (JWT_SECRET_KEY unset), the default dev user is admin
so all endpoints remain accessible without tokens.
"""

from enum import IntEnum
from typing import Callable

from fastapi import Depends

from backend.app.api.auth import get_current_user
from backend.app.exceptions import AuthorizationError


class Role(IntEnum):
    """Role hierarchy — higher value means more permissions."""

    VIEWER = 10
    ANALYST = 20
    ADMIN = 30


ROLE_MAP: dict[str, Role] = {
    "viewer": Role.VIEWER,
    "analyst": Role.ANALYST,
    "admin": Role.ADMIN,
}


def _get_role_level(role_name: str) -> Role:
    """Look up the numeric level for a role string."""
    role = ROLE_MAP.get(role_name.lower())
    if role is None:
        raise AuthorizationError(f"Unknown role: {role_name}")
    return role


def require_role(minimum_role: str) -> Callable:
    """Return a FastAPI dependency that enforces a minimum role.

    The user's JWT (or dev-mode default) must carry a `role` field
    whose level is >= the minimum role requested.
    """
    min_level = _get_role_level(minimum_role)

    async def _check_role(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        user_level = ROLE_MAP.get(user_role.lower())

        if user_level is None:
            raise AuthorizationError("No valid role assigned to this user")

        if user_level < min_level:
            raise AuthorizationError(
                f"Role '{user_role}' does not have access. "
                f"Minimum required: {minimum_role}"
            )

        return user

    return _check_role
