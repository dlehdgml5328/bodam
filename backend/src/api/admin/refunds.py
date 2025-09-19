"""Admin refund management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

router = APIRouter(prefix="/admin/refunds", tags=["admin"])


@router.get("")
async def list_pending_refunds() -> dict:
    return {"refunds": []}


@router.post("/{refund_id}/decision")
async def decide_refund(refund_id: uuid.UUID, payload: dict) -> dict:
    return {"refund_id": str(refund_id), "decision": payload.get("decision", "pending")}


__all__ = ["router"]
