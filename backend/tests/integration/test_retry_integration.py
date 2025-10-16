"""재시도 정책 Integration Tests

실제 네트워크 에러 시나리오에서 재시도 동작 검증
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from backend.src.integrations.http_client import get_client
from backend.src.integrations.retry_policy import fetch_with_retry


class TestRetryIntegration:
    """재시도 정책 통합 테스트"""

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """네트워크 에러 발생 시 재시도 (최대 3회)"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=[
                    httpx.ConnectTimeout("1st attempt"),
                    httpx.ConnectTimeout("2nd attempt"),
                    AsyncMock(status_code=200, text="success")  # 3번째 성공
                ]
            ) as mock_request:
                response = await fetch_with_retry(client, "GET", "http://example.com")

                # 3회 시도 확인
                assert mock_request.call_count == 3
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_retry_for_payment_domain(self):
        """결제 도메인은 재시도 안 함"""
        async with get_client("general") as client:
            with patch.object(
                client, 'request',
                side_effect=httpx.ConnectTimeout("Timeout")
            ) as mock_request:
                with pytest.raises(httpx.ConnectTimeout):
                    await fetch_with_retry(
                        client, "GET", "https://api.tosspayments.com/v1/test"
                    )

                # 1회만 시도
                assert mock_request.call_count == 1
