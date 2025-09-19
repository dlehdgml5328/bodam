"""Fire station API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["stations"])


class FavoriteRequest(BaseModel):
    pass


@router.get("/stations")
async def list_stations(
    page: int = 1,
    limit: int = 20,
    region: str | None = None,
    district: str | None = None,
    search: str | None = None,
) -> dict:
    return {
        "stations": [
            {
                "id": str(uuid.uuid4()),
                "name": "강남소방서",
                "region": region or "서울",
                "district": district or "강남구",
                "address": "서울 강남구 테헤란로",
            }
        ],
        "total": 1,
        "page": page,
        "limit": limit,
    }


@router.get("/stations/nearby")
async def nearby_stations(lat: float, lng: float, radius: float = 5000, limit: int = 10) -> dict:
    return {
        "stations": [
            {
                "id": str(uuid.uuid4()),
                "name": "강남소방서",
                "distance": 1234.5,
            }
        ]
    }


@router.get("/stations/{station_id}")
async def get_station(station_id: uuid.UUID) -> dict:
    return {
        "id": str(station_id),
        "name": "강남소방서",
        "recent_donations": [
            {
                "amount": 20000,
                "donor_name": "홍길동",
                "message": "응원합니다",
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        ],
    }


@router.get("/stations/{station_id}/rankings")
async def get_station_rankings(station_id: uuid.UUID, period: str = "all_time", limit: int = 10) -> dict:
    return {
        "rankings": [
            {
                "rank": 1,
                "user": {"name": "홍길동", "tier": 3},
                "total_amount": 500000,
                "donation_count": 12,
            }
        ],
        "period": period,
        "calculated_at": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/stations/{station_id}/incidents")
async def get_station_incidents(station_id: uuid.UUID, days: int = 7) -> dict:
    return {
        "incidents": [
            {
                "id": str(uuid.uuid4()),
                "title": "화재 발생",
                "summary": "소규모 화재",
                "source": "disaster_msg",
                "published_at": datetime.utcnow().isoformat() + "Z",
            }
        ]
    }


@router.post("/stations/{station_id}/favorites", status_code=status.HTTP_201_CREATED)
async def add_favorite(station_id: uuid.UUID, _: FavoriteRequest | None = None) -> dict:
    return {"message": "즐겨찾기에 추가되었습니다"}


@router.delete("/stations/{station_id}/favorites")
async def remove_favorite(station_id: uuid.UUID) -> dict:
    return {"message": "즐겨찾기가 제거되었습니다"}


__all__ = ["router"]
