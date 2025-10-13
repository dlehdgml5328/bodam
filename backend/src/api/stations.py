"""Fire station API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.connection import get_session
from src.models.donation import Donation
from src.models.fire_station import EmergencyPriority, LiveStatus, StationStatus
from src.services.fire_station_service import (
    EmergencyStatusRecord,
    FireStationNotFoundError,
    FireStationService,
)

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


class StationsListResponse(BaseModel):
    stations: list[FireStationSummary]
    total: int
    page: int
    limit: int


class NearbyStation(BaseModel):
    station: FireStationSummary
    distance: float


class NearbyStationsResponse(BaseModel):
    stations: list[NearbyStation]


class RecentDonationItem(BaseModel):
    amount: Decimal
    donor_name: str
    message: str | None
    created_at: datetime


class StationDetailResponse(BaseModel):
    station: FireStationSummary
    station_code: str
    recent_donations: list[RecentDonationItem]


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


def _extract_coordinates(station: Any) -> tuple[float | None, float | None]:
    if station.location is None:
        return (None, None)
    try:
        point = to_shape(station.location)
        return float(point.y), float(point.x)
    except Exception:  # pragma: no cover - defensive guard
        return (None, None)


def _map_station_summary(station: Any) -> FireStationSummary:
    lat, lng = _extract_coordinates(station)
    return FireStationSummary(
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
    )


def _resolve_donor_name(donation: Donation) -> str:
    if donation.is_anonymous:
        return "익명"
    if donation.donor_display_name:
        return donation.donor_display_name
    user = donation.user
    if user and user.name:
        return user.name
    return "알 수 없음"


@router.get("/stations", response_model=StationsListResponse)
async def list_stations(
    page: int = 1,
    limit: int = 20,
    region: str | None = None,
    district: str | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> StationsListResponse:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PAGE")
    if limit < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_LIMIT")

    sanitized_limit = min(limit, 200)
    offset = (page - 1) * sanitized_limit

    service = FireStationService(session)
    stations, total = await service.list_stations(
        region=region,
        district=district,
        search=search,
        limit=sanitized_limit,
        offset=offset,
    )

    return StationsListResponse(
        stations=[_map_station_summary(station) for station in stations],
        total=total,
        page=page,
        limit=sanitized_limit,
    )


@router.get("/stations/nearby", response_model=NearbyStationsResponse)
async def nearby_stations(
    lat: float,
    lng: float,
    radius: float = 5000,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> NearbyStationsResponse:
    if limit < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_LIMIT")
    sanitized_limit = min(limit, 50)
    sanitized_radius = max(100.0, min(radius, 50000.0))

    service = FireStationService(session)
    rows = await service.nearby_stations(
        latitude=lat,
        longitude=lng,
        radius_meters=sanitized_radius,
        limit=sanitized_limit,
    )
    payload: list[NearbyStation] = []
    for station, distance in rows:
        payload.append(
            NearbyStation(
                station=_map_station_summary(station),
                distance=float(distance) if distance is not None else 0.0,
            )
        )
    return NearbyStationsResponse(stations=payload)


@router.get("/stations/{station_id}", response_model=StationDetailResponse)
async def get_station(
    station_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> StationDetailResponse:
    service = FireStationService(session)
    try:
        station = await service.get_station(station_id)
    except FireStationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="STATION_NOT_FOUND") from exc

    recent_stmt = (
        select(Donation)
        .where(Donation.fire_station_id == station_id)
        .order_by(Donation.created_at.desc())
        .limit(5)
        .options(selectinload(Donation.user))
    )
    recent_result = await session.execute(recent_stmt)
    recent_donations = [
        RecentDonationItem(
            amount=donation.amount,
            donor_name=_resolve_donor_name(donation),
            message=donation.message,
            created_at=donation.created_at,
        )
        for donation in recent_result.scalars()
    ]

    return StationDetailResponse(
        station=_map_station_summary(station),
        station_code=station.station_code,
        recent_donations=recent_donations,
    )


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
