"""Reusable pagination utilities for list endpoints.

Usage:
    from backend.app.api.pagination import PaginatedResponse, PaginationParams

    @router.get("/items", response_model=PaginatedResponse)
    async def list_items(params: PaginationParams = Depends()):
        ...
"""

import math
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """FastAPI dependency for extracting page/page_size from query params."""

    def __init__(
        self,
        page: int = Query(1, ge=1, le=10000, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope for paginated list responses."""

    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int) -> "PaginatedResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, math.ceil(total / page_size)),
        )
