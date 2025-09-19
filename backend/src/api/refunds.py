"""Refund API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

router = APIRouter(prefix="/refunds", tags=["refunds"])


@router.get("")
async def list_refunds() -> dict:
    return {"refunds": []}


@router.post("/{refund_id}/approve")
async def approve_refund(refund_id: uuid.UUID) -> dict:
    return {"refund_id": str(refund_id), "status": "approved"}


__all__ = ["router"]
