"""Web push subscription API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/webpush", tags=["webpush"])


@router.post("/subscribe")
async def subscribe(payload: dict) -> dict:
    return {"status": "subscribed"}


@router.post("/unsubscribe")
async def unsubscribe(payload: dict) -> dict:
    return {"status": "unsubscribed"}


__all__ = ["router"]
