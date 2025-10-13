"""Service helpers for news and breaking incident feeds stored in Redis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

import redis.asyncio as redis

from src.cache.clients import get_cache_client

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VideoNewsRecord:
    """Structured representation of a news item suited for video or rich media."""

    id: str
    title: str
    summary: str | None
    article_url: str | None
    video_url: str | None
    thumbnail_url: str | None
    category: str | None
    occurred_at: datetime | None
    status: str | None
    views: int | None
    likes: int | None
    metadata: dict[str, Any] | None


@dataclass(slots=True)
class BreakingNewsRecord:
    """Structured representation of a breaking-news ticker item."""

    id: str
    title: str
    timestamp: datetime | None
    link: str | None
    is_breaking: bool
    source: str | None
    metadata: dict[str, Any] | None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class NewsService:
    """High-level service to retrieve news and incident feeds from Redis."""

    VIDEO_KEY = "news:videos"
    BREAKING_KEY = "news:breaking"

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis_client = redis_client

    async def _get_client(self) -> redis.Redis:
        if self._redis_client is None:
            self._redis_client = await get_cache_client()
        return self._redis_client

    async def fetch_videos(self, limit: int = 10) -> list[VideoNewsRecord]:
        """Fetch recent video news entries from Redis."""
        redis_client = await self._get_client()
        raw_items: Sequence[bytes] = await redis_client.lrange(self.VIDEO_KEY, 0, max(0, limit - 1))
        records: list[VideoNewsRecord] = []
        for raw in raw_items:
            if not raw:
                continue
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.warning("[NewsService] Skipping invalid video payload: %s", exc)
                continue

            record = self._parse_video_record(payload)
            if record is not None:
                records.append(record)

        return records

    async def fetch_breaking(self, limit: int = 20) -> list[BreakingNewsRecord]:
        """Fetch breaking-news ticker items stored in Redis."""
        redis_client = await self._get_client()
        raw_items: Sequence[bytes] = await redis_client.lrange(self.BREAKING_KEY, 0, max(0, limit - 1))
        records: list[BreakingNewsRecord] = []
        for raw in raw_items:
            if not raw:
                continue
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.warning("[NewsService] Skipping invalid breaking payload: %s", exc)
                continue

            record = self._parse_breaking_record(payload)
            if record is not None:
                records.append(record)

        return records

    @staticmethod
    def _parse_video_record(data: dict[str, Any] | None) -> VideoNewsRecord | None:
        if not isinstance(data, dict):
            return None

        record_id = str(data.get("id") or data.get("incident_id") or data.get("slug") or "")
        if not record_id:
            logger.debug("[NewsService] video payload missing id: %s", data)
            return None

        occurred_at = (
            _parse_datetime(data.get("occurred_at"))
            or _parse_datetime(data.get("published_at"))
            or _parse_datetime(data.get("updated_at"))
        )

        metadata = data.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None

        return VideoNewsRecord(
            id=record_id,
            title=str(data.get("title") or "제목 없는 소식"),
            summary=data.get("summary") or data.get("description"),
            article_url=data.get("article_url"),
            video_url=data.get("video_url"),
            thumbnail_url=data.get("thumbnail_url"),
            category=(data.get("category") or data.get("tag") or "").strip() or None,
            occurred_at=occurred_at,
            status=data.get("status"),
            views=_safe_int(data.get("views")),
            likes=_safe_int(data.get("likes")),
            metadata=metadata,
        )

    @staticmethod
    def _parse_breaking_record(data: dict[str, Any] | None) -> BreakingNewsRecord | None:
        if not isinstance(data, dict):
            return None

        record_id = str(data.get("id") or data.get("incident_id") or data.get("slug") or "")
        if not record_id:
            logger.debug("[NewsService] breaking payload missing id: %s", data)
            return None

        metadata = data.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None

        return BreakingNewsRecord(
            id=record_id,
            title=str(data.get("title") or "제목 없는 속보"),
            timestamp=_parse_datetime(data.get("timestamp"))
            or _parse_datetime(data.get("occurred_at"))
            or _parse_datetime(data.get("published_at")),
            link=data.get("link") or data.get("article_url"),
            is_breaking=bool(data.get("is_breaking", True)),
            source=data.get("source"),
            metadata=metadata,
        )


__all__ = ["NewsService", "VideoNewsRecord", "BreakingNewsRecord"]
