"""uvloop 통합 Unit Tests

uvloop이 정상적으로 적용되어 asyncio 이벤트 루프를 교체했는지 검증합니다.
"""
import asyncio
import sys

import pytest


class TestUvloopIntegration:
    """uvloop 이벤트 루프 정책 검증"""

    def test_uvloop_event_loop_policy_on_linux(self):
        """Linux 환경에서 uvloop EventLoopPolicy가 설정되었는지 확인"""
        if sys.platform == "win32":
            pytest.skip("Windows는 uvloop을 지원하지 않음")

        # uvloop이 설치되어 있는지 확인
        try:
            import uvloop
        except ImportError:
            pytest.skip("uvloop이 설치되지 않음")

        # 현재 이벤트 루프 정책 확인
        current_policy = asyncio.get_event_loop_policy()

        # uvloop.EventLoopPolicy가 설정되었는지 검증
        assert isinstance(
            current_policy, uvloop.EventLoopPolicy
        ), f"예상: uvloop.EventLoopPolicy, 실제: {type(current_policy)}"

    def test_uvloop_skipped_on_windows(self):
        """Windows 환경에서는 uvloop이 적용되지 않았는지 확인"""
        if sys.platform != "win32":
            pytest.skip("이 테스트는 Windows 전용입니다")

        # Windows에서는 기본 이벤트 루프 정책이 유지되어야 함
        current_policy = asyncio.get_event_loop_policy()

        # uvloop.EventLoopPolicy가 아닌지 검증
        assert not hasattr(current_policy, "__module__") or "uvloop" not in getattr(
            current_policy, "__module__", ""
        ), "Windows에서는 uvloop이 적용되지 않아야 함"

    @pytest.mark.asyncio
    async def test_event_loop_works_correctly(self):
        """이벤트 루프가 정상적으로 동작하는지 확인"""
        # 간단한 비동기 작업 실행
        async def simple_coroutine():
            await asyncio.sleep(0.001)
            return "success"

        result = await simple_coroutine()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(self):
        """여러 개의 동시 작업이 정상적으로 실행되는지 확인"""
        async def counter_task(n: int) -> int:
            await asyncio.sleep(0.001)
            return n * 2

        # 10개의 동시 작업 생성
        tasks = [counter_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # 결과 검증
        expected = [i * 2 for i in range(10)]
        assert results == expected
