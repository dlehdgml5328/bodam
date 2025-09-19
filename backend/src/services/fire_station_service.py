"""Service helpers for fire station queries and updates."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Sequence

from geoalchemy2 import functions as geo_func
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fire_station import FireStation

logger = logging.getLogger(__name__)


class FireStationNotFoundError(Exception):
    """Raised when a requested fire station is missing."""


class FireStationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_stations(
        self,
        *,
        region: str | None = None,
        district: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[FireStation], int]:
        query: Select[tuple[FireStation]] = select(FireStation)
        count_query: Select[tuple[int]] = select(func.count(FireStation.id))

        if region:
            query = query.where(FireStation.region == region)
            count_query = count_query.where(FireStation.region == region)
        if district:
            query = query.where(FireStation.district == district)
            count_query = count_query.where(FireStation.district == district)
        if search:
            like_pattern = f"%{search}%"
            query = query.where(FireStation.name.ilike(like_pattern))
            count_query = count_query.where(FireStation.name.ilike(like_pattern))

        result = await self._session.execute(
            query.order_by(FireStation.name.asc()).offset(offset).limit(limit)
        )
        stations = list(result.scalars())
        total = await self._session.scalar(count_query)
        return stations, int(total or 0)

    async def get_station(self, station_id: uuid.UUID) -> FireStation:
        station = await self._session.get(FireStation, station_id)
        if station is None:
            raise FireStationNotFoundError(str(station_id))
        return station

    async def nearby_stations(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000,
        limit: int = 10,
    ) -> Sequence[tuple[FireStation, float]]:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        distance = func.ST_DistanceSphere(FireStation.location, point).label("distance")
        query = (
            select(FireStation, distance)
            .where(geo_func.ST_DWithin(FireStation.location, point, radius_meters))
            .order_by(distance.asc())
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.all())

    async def update_totals(
        self,
        station_id: uuid.UUID,
        *,
        donor_count: int | None = None,
        total_received: Decimal | None = None,
    ) -> FireStation:
        station = await self.get_station(station_id)
        if donor_count is not None:
            station.donor_count = donor_count
        if total_received is not None:
            station.total_received = total_received
        await self._session.flush()
        return station


__all__ = ["FireStationService", "FireStationNotFoundError"]
