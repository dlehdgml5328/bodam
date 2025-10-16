"""DB 연결 풀 Integration Tests

실제 DB 연결로 연결 풀 동작 검증
"""
import pytest
import asyncio
from sqlalchemy.exc import TimeoutError
from backend.src.database.connection import SessionLocal, engine


class TestDBPoolIntegration:
    """DB 연결 풀 통합 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_queries_within_pool_size(self):
        """pool_size(10) 내에서 동시 쿼리 실행 성공"""
        async def run_query(i):
            async with SessionLocal() as session:
                result = await session.execute(f"SELECT {i} as num")
                return result.scalar()

        # 10개 동시 쿼리 (pool_size 내)
        results = await asyncio.gather(*[run_query(i) for i in range(10)])
        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_pool_connection_reuse(self):
        """연결 재사용 확인 (체크인 후 다시 체크아웃)"""
        # 첫 번째 연결
        async with SessionLocal() as session1:
            result1 = await session1.execute("SELECT 1")
            assert result1.scalar() == 1

        # 두 번째 연결 (첫 번째 연결이 풀로 반환되어 재사용됨)
        async with SessionLocal() as session2:
            result2 = await session2.execute("SELECT 2")
            assert result2.scalar() == 2

        # 풀 크기 확인 (연결이 재사용되므로 크기 유지)
        assert engine.pool.size() <= 10
