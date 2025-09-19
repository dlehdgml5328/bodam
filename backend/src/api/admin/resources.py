"""Admin resource management endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/resources", tags=["admin"])


@router.get("")
async def list_resources() -> dict:
    return {"resources": []}


__all__ = ["router"]
