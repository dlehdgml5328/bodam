"""Group API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("")
async def list_groups() -> dict:
    return {"groups": []}


@router.post("")
async def create_group(payload: dict) -> dict:
    return {"group_id": str(uuid.uuid4()), "status": "created"}


__all__ = ["router"]
