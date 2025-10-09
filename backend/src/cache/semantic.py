"""Helpers for semantic cache maintenance."""

from __future__ import annotations

import logging
import uuid
from typing import Iterable

import redis.asyncio as redis

from .clients import get_semantic_client
from .keys import slugify_token
from .settings import CacheSettings, get_cache_settings

logger = logging.getLogger(__name__)


async def shorten_ttl(
    pattern: str,
    *,
    ttl_seconds: int,
    client: redis.Redis | None = None,
) -> int:
    """Reduce TTL for semantic cache entries matching a pattern."""
    client = client or await get_semantic_client()
    updated = 0
    async for key in client.scan_iter(match=pattern):
        current_ttl = await client.ttl(key)
        if current_ttl == -2:
            continue
        if current_ttl == -1 or current_ttl > ttl_seconds:
            await client.expire(key, ttl_seconds)
            updated += 1
    if updated:
        logger.debug(
            "Soft invalidated %s semantic cache keys (pattern=%s, ttl=%s)",
            updated,
            pattern,
            ttl_seconds,
        )
    return updated


async def soft_invalidate_queries(
    *,
    station_id: uuid.UUID | None = None,
    region: str | None = None,
    ttl_seconds: int | None = None,
    client: redis.Redis | None = None,
    settings: CacheSettings | None = None,
) -> int:
    """Shorten TTL for semantic queries related to a station/region."""
    client = client or await get_semantic_client()
    settings = settings or get_cache_settings()
    ttl_seconds = ttl_seconds or max(
        60, min(settings.default_semantic_ttl_seconds, 600)
    )

    patterns: list[str] = []
    if station_id:
        patterns.append(f"semantic:q:*:station={station_id}*")
    if region:
        patterns.append(f"semantic:q:*:region={slugify_token(region)}*")
    # Fallback to everything if nothing matched previously
    if not patterns:
        patterns.append("semantic:q:*")

    total_updated = 0
    for pattern in patterns:
        total_updated += await shorten_ttl(
            pattern, ttl_seconds=ttl_seconds, client=client
        )

    if total_updated == 0 and "semantic:q:*" not in patterns:
        total_updated = await shorten_ttl(
            "semantic:q:*", ttl_seconds=ttl_seconds, client=client
        )
    return total_updated


async def delete_patterns(
    patterns: Iterable[str],
    *,
    client: redis.Redis | None = None,
) -> int:
    client = client or await get_semantic_client()
    deleted = 0
    for pattern in patterns:
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
            deleted += 1
    if deleted:
        logger.info("Deleted %s semantic cache keys", deleted)
    return deleted


__all__ = ["soft_invalidate_queries", "shorten_ttl", "delete_patterns"]
