"""Graph database connector."""

from __future__ import annotations

import os
from dataclasses import dataclass

import asyncpg


@dataclass
class GraphSettings:
    dsn: str = os.getenv("GRAPH_DB_DSN", "postgresql://bodam:bodam@db:5432/bodam")


class GraphClient:
    def __init__(self, settings: GraphSettings | None = None) -> None:
        self._settings = settings or GraphSettings()
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._settings.dsn)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def query(self, cypher: str, *args) -> list[asyncpg.Record]:
        if self._pool is None:
            raise RuntimeError("GraphClient not connected")
        async with self._pool.acquire() as connection:
            return await connection.fetch(cypher, *args)


__all__ = ["GraphClient", "GraphSettings"]
