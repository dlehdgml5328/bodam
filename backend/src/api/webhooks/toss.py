"""Toss Payments webhook endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter(prefix="/webhooks/toss", tags=["webhooks"])


@router.post("/payment")
async def handle_toss_webhook(
    payload: dict,
    x_toss_signature: str | None = Header(default=None),
) -> dict:
    if x_toss_signature is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")

    # TODO: verify signature and update donation status
    event_type = payload.get("eventType", "unknown")
    return {"received": True, "event_type": event_type}


__all__ = ["router"]
