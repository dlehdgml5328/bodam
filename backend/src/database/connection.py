"""Async SQLAlchemy database session management with connection pooling.

연결 풀 설정을 포함한 데이터베이스 세션 관리
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings as config_settings

settings = config_settings

DATABASE_URL = settings.database_url

# DB 연결 풀 설정 적용
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    # 연결 풀 설정
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_timeout=settings.db_pool_timeout,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncSession:
    async with session_scope() as session:
        yield session


__all__ = ["engine", "SessionLocal", "session_scope", "get_session"]
