"""Extended health endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/readyz")
async def readyz() -> dict:
    return {"status": "ready"}


__all__ = ["router"]
