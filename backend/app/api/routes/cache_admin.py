"""Cache administration endpoints.

GET  /cache/stats  — view hit/miss rates and cache size
POST /cache/clear  — flush all or a specific namespace
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from backend.app.api.rbac import require_role
from backend.app.services.cache import app_cache

router = APIRouter(prefix="/cache", tags=["Cache"])


class ClearRequest(BaseModel):
    namespace: str | None = Field(default=None, max_length=100)


class ClearResponse(BaseModel):
    cleared: int


@router.get("/stats")
async def cache_stats() -> dict:
    """Return cache statistics (size, hits, misses, hit rate)."""
    return app_cache.stats()


@router.post("/clear", response_model=ClearResponse)
async def clear_cache(
    request: ClearRequest,
    user: dict = Depends(require_role("admin")),
) -> ClearResponse:
    """Clear all cached entries, or only a specific namespace."""
    count = app_cache.clear(request.namespace)
    return ClearResponse(cleared=count)
