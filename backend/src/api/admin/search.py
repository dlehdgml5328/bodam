"""Admin LLM search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/admin/search", tags=["admin"])


@router.get("")
async def search_admin_resources(q: str = Query(..., description="검색어")) -> dict:
    return {"results": [], "query": q}


__all__ = ["router"]
