"""Live data API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/live", tags=["live"])


@router.get("/news")
async def live_news() -> dict:
    return {"items": []}


@router.get("/alerts")
async def live_alerts() -> dict:
    return {"alerts": []}


@router.get("/videos")
async def live_videos() -> dict:
    return {"videos": []}


__all__ = ["router"]
