"""Redis client factories for cache layers."""

from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as redis

from .settings import CacheSettings, get_cache_settings

logger = logging.getLogger(__name__)

_cache_client: Optional[redis.Redis] = None
_semantic_client: Optional[redis.Redis] = None


async def _create_client(url: str) -> redis.Redis:
    """Create a Redis asyncio client."""
    client = await redis.from_url(url, encoding="utf-8", decode_responses=False)
    logger.debug("Initialised Redis client for %s", url)
    return client


async def get_cache_client(settings: CacheSettings | None = None) -> redis.Redis:
    """Return the shared client for the standard cache."""
    global _cache_client
    settings = settings or get_cache_settings()
    if _cache_client is None:
        _cache_client = await _create_client(settings.cache_url)
    return _cache_client


async def get_semantic_client(settings: CacheSettings | None = None) -> redis.Redis:
    """Return the shared client for the semantic cache."""
    global _semantic_client
    settings = settings or get_cache_settings()
    if _semantic_client is None:
        _semantic_client = await _create_client(settings.semantic_url)
    return _semantic_client


async def close_clients() -> None:
    """Close both Redis clients."""
    global _cache_client, _semantic_client
    if _cache_client is not None:
        await _cache_client.close()
        _cache_client = None
    if _semantic_client is not None:
        await _semantic_client.close()
        _semantic_client = None


__all__ = ["get_cache_client", "get_semantic_client", "close_clients"]
