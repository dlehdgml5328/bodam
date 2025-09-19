"""Collector for fire department station data."""

from __future__ import annotations

from datetime import datetime

import httpx

STATIONS_ENDPOINT = "https://example.com/fire-stations"


async def fetch_fire_station_snapshot() -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        await client.get(STATIONS_ENDPOINT)
    return [
        {
            "id": "station-1",
            "name": "강남소방서",
            "region": "서울",
            "district": "강남구",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
    ]


__all__ = ["fetch_fire_station_snapshot"]
