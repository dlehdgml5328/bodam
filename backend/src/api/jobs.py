"""Job trigger API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/rankings/build")
async def trigger_ranking_build() -> dict:
    return {"status": "queued"}


__all__ = ["router"]
