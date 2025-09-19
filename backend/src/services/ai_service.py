"""AI analysis service orchestrating Together AI summarisation."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.news_content import ContentStatus, NewsContent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisResult:
    summary: str
    keywords: list[str]
    relevance_score: int
    embedding: list[float]


class TogetherAIClient(Protocol):
    async def analyze_news(
        self,
        *,
        title: str,
        content: str,
        source: str,
    ) -> AnalysisResult: ...


class AIAnalysisService:
    def __init__(self, session: AsyncSession, ai_client: TogetherAIClient) -> None:
        self._session = session
        self._ai_client = ai_client

    async def analyze_news_items(
        self,
        *,
        source: str,
        items: Iterable[dict],
    ) -> tuple[str, list[NewsContent]]:
        job_id = uuid.uuid4()
        stored_items: list[NewsContent] = []
        for item in items:
            analysis = await self._ai_client.analyze_news(
                title=item.get("title", ""),
                content=item.get("content", ""),
                source=source,
            )
            status = self._status_from_score(analysis.relevance_score)
            published_at = item.get("published_at")
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at)
            if not isinstance(published_at, datetime):
                published_at = datetime.now(timezone.utc)

            news = NewsContent(
                analysis_job_id=job_id,
                title=item.get("title", ""),
                content=item.get("content", ""),
                source=source,
                source_url=item.get("url", ""),
                published_at=published_at,
                embedding=analysis.embedding,
                relevance_score=analysis.relevance_score,
                summary=analysis.summary,
                keywords=analysis.keywords,
                status=status,
            )
            self._session.add(news)
            stored_items.append(news)

        await self._session.flush()
        logger.info("Stored %d analyzed news items", len(stored_items))
        return str(job_id), stored_items

    async def get_analysis_results(self, job_id: str) -> dict:
        job_uuid = uuid.UUID(job_id)
        result = await self._session.execute(
            select(NewsContent).where(NewsContent.analysis_job_id == job_uuid)
        )
        items = list(result.scalars())
        status = "completed" if items else "pending"
        return {
            "status": status,
            "items": items,
        }

    @staticmethod
    def _status_from_score(score: int) -> ContentStatus:
        if score >= 70:
            return ContentStatus.AUTO_APPROVED
        if score >= 50:
            return ContentStatus.PENDING_REVIEW
        return ContentStatus.REJECTED


__all__ = ["AIAnalysisService", "AnalysisResult", "TogetherAIClient"]
