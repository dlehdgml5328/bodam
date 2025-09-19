"""Together AI client wrapper."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from src.services.ai_service import AnalysisResult, TogetherAIClient


@dataclass
class TogetherAISettings:
    api_key: str
    model: str = "llama-3.3-70b-instruct"
    base_url: str = "https://api.together.xyz"

    @classmethod
    def from_env(cls) -> "TogetherAISettings":
        api_key = os.getenv("TOGETHER_AI_API_KEY", "test_key")
        model = os.getenv("TOGETHER_AI_MODEL", cls.model)
        base_url = os.getenv("TOGETHER_AI_BASE_URL", cls.base_url)
        return cls(api_key=api_key, model=model, base_url=base_url)


class TogetherAIHttpClient(TogetherAIClient):
    def __init__(self, settings: TogetherAISettings | None = None) -> None:
        self._settings = settings or TogetherAISettings.from_env()
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url,
            headers={"Authorization": f"Bearer {self._settings.api_key}"},
            timeout=15,
        )

    async def analyze_news(
        self,
        *,
        title: str,
        content: str,
        source: str,
    ) -> AnalysisResult:
        # In production, call Together AI inference endpoint. Here we mock the response.
        summary = content[:140] + "..." if len(content) > 140 else content
        keywords = [word for word in title.split()[:3]]
        relevance_score = 80
        embedding = [0.0] * 10
        return AnalysisResult(
            summary=summary,
            keywords=keywords,
            relevance_score=relevance_score,
            embedding=embedding,
        )

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["TogetherAIHttpClient", "TogetherAISettings"]
