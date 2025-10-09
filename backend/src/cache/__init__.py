"""Cache helpers package."""

from .clients import close_clients, get_cache_client, get_semantic_client
from .fire_station import (
    build_emergency_key,
    build_list_key,
    build_nearby_key,
    cache_payload,
    fetch_cached_payload,
    invalidate_after_station_update,
    invalidate_emergency_cache_for_region,
)
from .settings import CacheSettings, get_cache_settings

__all__ = [
    "CacheSettings",
    "get_cache_settings",
    "get_cache_client",
    "get_semantic_client",
    "close_clients",
    "build_list_key",
    "build_nearby_key",
    "build_emergency_key",
    "cache_payload",
    "fetch_cached_payload",
    "invalidate_after_station_update",
    "invalidate_emergency_cache_for_region",
]
