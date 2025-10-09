"""Cache key helpers for fire station related queries."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
import uuid
from typing import Any


def _hash_payload(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def slugify_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = normalized.replace(":", "-")
    normalized = re.sub(r"[\\/\s]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "unknown"


def list_stations_key(
    *,
    region: str | None,
    district: str | None,
    search: str | None,
    limit: int,
    offset: int,
) -> str:
    region_token = slugify_token(region) if region else "all"
    district_token = slugify_token(district) if district else "all"
    payload = {
        "region": region or "",
        "district": district or "",
        "search": search or "",
        "limit": limit,
        "offset": offset,
    }
    return f"cache:stations:list:{region_token}:{district_token}:{_hash_payload(payload)}"


def nearby_stations_key(
    *,
    latitude: float,
    longitude: float,
    radius_meters: float,
    limit: int,
    precision: int = 6,
) -> str:
    geohash = f"{latitude:.{precision}f}:{longitude:.{precision}f}"
    radius_bucket = int(math.ceil(radius_meters / 100.0) * 100)
    payload = {
        "geo": geohash,
        "radius": radius_bucket,
        "limit": limit,
    }
    return f"cache:stations:nearby:{geohash}:{radius_bucket}:{_hash_payload(payload)}"


def emergency_status_key(
    *,
    region: str | None,
    priority: str | None,
    limit: int,
) -> str:
    payload = {
        "region": region or "",
        "priority": priority or "",
        "limit": limit,
    }
    region_token = slugify_token(region) if region else "all"
    priority_token = slugify_token(priority) if priority else "all"
    return f"cache:emergencies:{region_token}:{priority_token}:{_hash_payload(payload)}"


def semantic_query_key(
    query_text: str,
    *,
    region: str | None = None,
    station_id: uuid.UUID | None = None,
) -> str:
    base = f"semantic:q:{_hash_payload({'q': query_text})}"
    suffix_parts: list[str] = []
    if region:
        suffix_parts.append(f"region={slugify_token(region)}")
    if station_id:
        suffix_parts.append(f"station={station_id}")
    if suffix_parts:
        return f"{base}:{':'.join(suffix_parts)}"
    return base


__all__ = [
    "list_stations_key",
    "nearby_stations_key",
    "emergency_status_key",
    "semantic_query_key",
    "slugify_token",
]
