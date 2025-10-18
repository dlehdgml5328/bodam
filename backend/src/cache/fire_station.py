"""Fire station specific cache helpers."""

from __future__ import annotations

import logging
from typing import Any

from src.models.fire_station import FireStation

from . import keys, semantic, standard
from .keys import slugify_token
from .settings import get_cache_settings

logger = logging.getLogger(__name__)


def build_list_key(
    *,
    region: str | None,
    district: str | None,
    search: str | None,
    limit: int,
    offset: int,
) -> str:
    return keys.list_stations_key(
        region=region,
        district=district,
        search=search,
        limit=limit,
        offset=offset,
    )


def build_nearby_key(
    *,
    latitude: float,
    longitude: float,
    radius_meters: float,
    limit: int,
) -> str:
    return keys.nearby_stations_key(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit,
    )


def build_emergency_key(
    *,
    region: str | None,
    priority: str | None,
    limit: int,
) -> str:
    return keys.emergency_status_key(
        region=region,
        priority=priority,
        limit=limit,
    )


async def cache_payload(
    key: str,
    payload: Any,
    *,
    ttl_seconds: int | None = None,
) -> None:
    """Store a JSON serialisable payload in the standard cache."""
    await standard.set_json(key, payload, ttl_seconds=ttl_seconds)


async def fetch_cached_payload(key: str) -> Any | None:
    return await standard.get_json(key)


async def invalidate_after_station_update(station: FireStation) -> None:
    """Invalidate cache entries related to a fire station update."""
    settings = get_cache_settings()

    standard_patterns = [
        "cache:stations:list:*",
        "cache:stations:nearby:*",
    ]
    if station.region:
        region_token = slugify_token(station.region)
        standard_patterns.append(f"cache:emergencies:{region_token}:*")
    else:
        standard_patterns.append("cache:emergencies:*")

    for pattern in standard_patterns:
        await standard.delete_pattern(pattern)

    await semantic.soft_invalidate_queries(
        station_id=station.id,
        region=station.region,
        ttl_seconds=min(120, settings.default_semantic_ttl_seconds),
    )
    logger.debug(
        "Triggered cache invalidation for station %s (%s)",
        station.id,
        station.name,
    )


async def invalidate_emergency_cache_for_region(region: str | None) -> None:
    pattern = (
        "cache:emergencies:*"
        if region is None
        else f"cache:emergencies:{slugify_token(region)}:*"
    )
    await standard.delete_pattern(pattern)


__all__ = [
    "build_list_key",
    "build_nearby_key",
    "build_emergency_key",
    "cache_payload",
    "fetch_cached_payload",
    "invalidate_after_station_update",
    "invalidate_emergency_cache_for_region",
]
