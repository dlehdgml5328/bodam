"""Geocoding proxy API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/search")
async def geocode(address: str) -> dict:
    return {"address": address, "location": {"lat": 37.5665, "lng": 126.978}}


__all__ = ["router"]
