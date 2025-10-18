"""Pagination utilities for database queries."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response with calculated fields."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


async def paginate_query(
    session: AsyncSession,
    query: Select[tuple[T]],
    pagination: PaginationParams,
) -> PaginatedResponse[T]:
    """Paginate a SQLAlchemy query."""
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated items
    paginated_query = query.offset(pagination.offset).limit(pagination.size)
    items_result = await session.execute(paginated_query)
    items = [row[0] for row in items_result.all()]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""

    cursor: str | None = Field(default=None, description="Cursor for next page")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    direction: str = Field(default="next", regex="^(next|prev)$", description="Pagination direction")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response wrapper."""

    items: list[T]
    next_cursor: str | None
    prev_cursor: str | None
    has_next: bool
    has_prev: bool
    size: int

    @classmethod
    def create(
        cls,
        items: list[T],
        next_cursor: str | None,
        prev_cursor: str | None,
        size: int,
    ) -> "CursorPaginatedResponse[T]":
        """Create cursor paginated response."""
        return cls(
            items=items,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=next_cursor is not None,
            has_prev=prev_cursor is not None,
            size=size,
        )