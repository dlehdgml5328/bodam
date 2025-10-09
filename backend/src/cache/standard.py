"""Standard Redis cache helpers."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Sequence

import redis.asyncio as redis

from .clients import get_cache_client
from .settings import CacheSettings, get_cache_settings

logger = logging.getLogger(__name__)


async def get_json(
    key: str, *, client: redis.Redis | None = None
) -> Any | None:
    client = client or await get_cache_client()
    data = await client.get(key)
    if data is None:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logger.warning("Failed to decode JSON cache entry for key %s", key)
        return None


async def set_json(
    key: str,
    value: Any,
    *,
    ttl_seconds: int | None = None,
    client: redis.Redis | None = None,
    settings: CacheSettings | None = None,
) -> None:
    client = client or await get_cache_client()
    settings = settings or get_cache_settings()
    ttl_seconds = ttl_seconds or settings.default_cache_ttl_seconds
    payload = json.dumps(value, default=str, separators=(",", ":"))
    await client.set(key, payload, ex=ttl_seconds)
    logger.debug("Cached key %s for %s seconds", key, ttl_seconds)


async def delete_pattern(
    pattern: str,
    *,
    client: redis.Redis | None = None,
) -> int:
    """Delete all cache entries matching a pattern."""
    client = client or await get_cache_client()
    deleted = 0
    async for key in client.scan_iter(match=pattern):
        await client.delete(key)
        deleted += 1
    if deleted:
        logger.info("Deleted %s cache keys with pattern %s", deleted, pattern)
    return deleted


async def delete_keys(
    keys: Iterable[str],
    *,
    client: redis.Redis | None = None,
) -> int:
    client = client or await get_cache_client()
    key_list = list(keys)
    if not key_list:
        return 0
    deleted = await client.delete(*key_list)
    if deleted:
        logger.info("Deleted %s cache keys", deleted)
    return int(deleted)


async def shorten_ttl_for_keys(
    pattern: str,
    *,
    ttl_seconds: int,
    client: redis.Redis | None = None,
) -> int:
    """Reduce TTL for keys matching pattern (used for soft invalidation)."""
    client = client or await get_cache_client()
    updated = 0
    async for key in client.scan_iter(match=pattern):
        current_ttl = await client.ttl(key)
        if current_ttl == -2:
            continue  # key missing
        if current_ttl == -1 or current_ttl > ttl_seconds:
            await client.expire(key, ttl_seconds)
            updated += 1
    if updated:
        logger.debug(
            "Soft invalidated %s keys (pattern=%s, ttl=%s)",
            updated,
            pattern,
            ttl_seconds,
        )
    return updated


async def read_keys(pattern: str, *, client: redis.Redis | None = None) -> Sequence[str]:
    client = client or await get_cache_client()
    return [key async for key in client.scan_iter(match=pattern)]


__all__ = [
    "get_json",
    "set_json",
    "delete_pattern",
    "delete_keys",
    "shorten_ttl_for_keys",
    "read_keys",
]
