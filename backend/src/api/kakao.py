"""Kakao notification API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/kakao", tags=["kakao"])


@router.post("/send")
async def send_kakao_notification(payload: dict) -> dict:
    return {"status": "queued", "recipient": payload.get("to")}


__all__ = ["router"]
