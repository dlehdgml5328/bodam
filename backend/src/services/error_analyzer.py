"""
ErrorAnalyzer - pgvector 유사도 검색
FR-015, FR-016: 유사 에러 검색
"""
from typing import List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.error_event import ErrorEvent


class ErrorAnalyzer:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self.embedding_url = "http://localhost:8001/embed"

    async def create_embedding(self, text: str) -> List[float]:
        """384-dim embedding 생성"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.embedding_url,
                json={"text": text, "model": self.embedding_model},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def find_similar_errors(
        self,
        session: AsyncSession,
        error_message: str,
        limit: int = 5,
        similarity_threshold: float = 0.8,
    ) -> List[ErrorEvent]:
        """pgvector cosine distance로 유사 에러 검색"""
        query_embedding = await self.create_embedding(error_message)

        stmt = (
            select(ErrorEvent)
            .order_by(ErrorEvent.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def store_error_event(
        self,
        session: AsyncSession,
        level: str,
        message: str,
        traceback: str = None,
        service: str = "backend-api",
        trace_id: str = None,
        **kwargs,
    ) -> ErrorEvent:
        """에러 이벤트 저장 (embedding 포함)"""
        embedding_text = f"{message} {traceback or ''}"
        embedding = await self.create_embedding(embedding_text)

        error_event = ErrorEvent(
            level=level,
            message=message,
            traceback=traceback,
            service=service,
            trace_id=trace_id,
            embedding=embedding,
            **kwargs,
        )

        session.add(error_event)
        await session.commit()
        await session.refresh(error_event)

        return error_event
