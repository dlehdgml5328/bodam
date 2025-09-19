"""Redis Streams event bus wrapper."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass
class EventBusSettings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    stream_name: str = os.getenv("EVENT_STREAM", "bodam-events")


class EventBus:
    def __init__(self, settings: EventBusSettings | None = None) -> None:
        self._settings = settings or EventBusSettings()
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = await redis.from_url(self._settings.redis_url)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    async def publish(self, event_type: str, payload: dict) -> str:
        if self._redis is None:
            raise RuntimeError("EventBus not connected")
        data = json.dumps({"type": event_type, "payload": payload})
        return await self._redis.xadd(self._settings.stream_name, {"data": data})


__all__ = ["EventBus", "EventBusSettings"]
