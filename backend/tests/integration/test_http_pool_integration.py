"""HTTP 연결 풀 Integration Tests

실제 HTTP 요청으로 연결 풀 동작 검증
"""
import pytest
from src.integrations.http_client import get_client


class TestHttpPoolIntegration:
    """HTTP 클라이언트 연결 풀 통합 테스트"""

    @pytest.mark.asyncio
    async def test_general_client_basic_request(self):
        """일반 클라이언트로 기본 HTTP 요청"""
        async with get_client("general") as client:
            # httpbin.org로 테스트 (공개 API)
            response = await client.get("https://httpbin.org/get")
            assert response.status_code == 200
            data = response.json()
            assert "headers" in data

    @pytest.mark.asyncio
    async def test_payment_api_longer_timeout(self):
        """결제 API는 180초 타임아웃"""
        async with get_client("payment") as client:
            # 결제 클라이언트는 180초 타임아웃
            assert client.timeout.read == 180.0

            # 짧은 요청도 정상 동작
            response = await client.get("https://httpbin.org/delay/1")
            assert response.status_code == 200
