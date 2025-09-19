"""Admin LLM search service."""

from __future__ import annotations

from typing import Iterable

from src.integrations.graph import GraphClient


class LLMSearchService:
    def __init__(self, graph_client: GraphClient) -> None:
        self._graph_client = graph_client

    async def search(self, query: str) -> Iterable[dict]:
        await self._graph_client.connect()
        records = await self._graph_client.query("SELECT * FROM graph_search($1)", query)
        await self._graph_client.close()
        return [dict(record) for record in records]


__all__ = ["LLMSearchService"]
