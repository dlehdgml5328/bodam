"""Fire station API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.fire_station import EmergencyPriority, LiveStatus, StationStatus
from src.services.fire_station_service import EmergencyStatusRecord, FireStationService

router = APIRouter(tags=["stations"])


class FavoriteRequest(BaseModel):
    pass


class StationLocation(BaseModel):
    lat: float | None
    lng: float | None


class FireStationSummary(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    phone: str
    region: str
    district: str
    status: StationStatus
    total_received: Decimal
    donor_count: int
    location: StationLocation


class ActiveIncidentResponse(BaseModel):
    id: uuid.UUID
    title: str
    started_at: datetime | None


class EmergencyStationResponse(BaseModel):
    station: FireStationSummary
    status: LiveStatus
    status_label: str
    priority: EmergencyPriority
    summary: str | None
    updated_at: datetime
    active_incidents: list[ActiveIncidentResponse]


class EmergencyStationsResponse(BaseModel):
    as_of: datetime
    stations: list[EmergencyStationResponse]


_LIVE_STATUS_LABELS: dict[LiveStatus, str] = {
    LiveStatus.DISPATCHING: "출동 중",
    LiveStatus.SUPPRESSING: "진압 중",
    LiveStatus.STANDBY: "대기 중",
    LiveStatus.MAINTENANCE: "점검 중",
}


def _build_label(status: LiveStatus, explicit_label: str | None) -> str:
    if explicit_label:
        return explicit_label
    return _LIVE_STATUS_LABELS.get(status, status.value.replace("_", " ").title())


def _to_response_item(record: EmergencyStatusRecord) -> EmergencyStationResponse | None:
    status_snapshot = record.status
    station = status_snapshot.station
    if station is None:
        return None

    lat, lng = (None, None)
    if record.coordinates:
        lat, lng = record.coordinates

    incident_items: list[ActiveIncidentResponse] = []
    for active_incident in status_snapshot.active_incidents:
        incident = active_incident.incident
        if incident is None:
            continue
        incident_items.append(
            ActiveIncidentResponse(
                id=incident.id,
                title=incident.title,
                started_at=active_incident.started_at,
            )
        )

    return EmergencyStationResponse(
        station=FireStationSummary(
            id=station.id,
            name=station.name,
            address=station.address,
            phone=station.phone,
            region=station.region,
            district=station.district,
            status=station.status,
            total_received=station.total_received,
            donor_count=station.donor_count,
            location=StationLocation(lat=lat, lng=lng),
        ),
        status=status_snapshot.status,
        status_label=_build_label(status_snapshot.status, status_snapshot.status_label),
        priority=status_snapshot.priority,
        summary=status_snapshot.summary,
        updated_at=status_snapshot.updated_at,
        active_incidents=incident_items,
    )


@router.get("/emergency-stations", response_model=EmergencyStationsResponse)
async def list_emergency_stations(
    region: str | None = None,
    priority: Literal["high", "medium", "low"] | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> EmergencyStationsResponse:
    if limit <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_LIMIT")
    limit = min(limit, 200)

    priority_enum: EmergencyPriority | None = None
    if priority is not None:
        try:
            priority_enum = EmergencyPriority(priority)
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PRIORITY"
            ) from exc

    service = FireStationService(session)
    records = await service.get_emergency_statuses(
        region=region, priority=priority_enum, limit=limit
    )

    payload: list[EmergencyStationResponse] = []
    for record in records:
        item = _to_response_item(record)
        if item is not None:
            payload.append(item)

    return EmergencyStationsResponse(
        as_of=datetime.now(timezone.utc),
        stations=payload,
    )


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
