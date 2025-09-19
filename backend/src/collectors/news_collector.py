"""External news collector stub."""

from __future__ import annotations

from datetime import datetime

import httpx

NEWS_ENDPOINT = "https://example.com/news"


async def fetch_latest_news(limit: int = 10) -> list[dict]:
    # Placeholder implementation; in production integrate with real feeds.
    async with httpx.AsyncClient(timeout=10) as client:
        await client.get(NEWS_ENDPOINT)
    return [
        {
            "title": "서울 강남구 화재",
            "content": "강남구 소재 상가에서 화재가 발생했습니다.",
            "source": "naver_news",
            "url": "https://news.example.com/article",
            "published_at": datetime.utcnow().isoformat() + "Z",
        }
        for _ in range(limit)
    ]


__all__ = ["fetch_latest_news"]
