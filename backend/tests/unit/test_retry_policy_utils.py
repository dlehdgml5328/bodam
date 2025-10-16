"""재시도 정책 Unit Tests"""
import pytest
from backend.src.integrations.retry_policy import is_excluded_domain


class TestRetryPolicyUtils:
    """재시도 정책 유틸리티 함수 검증"""

    def test_is_excluded_domain_for_payment_api(self):
        """결제 API 도메인 제외 확인"""
        assert is_excluded_domain("https://api.tosspayments.com/v1/payments") is True
        assert is_excluded_domain("https://pay.naver.com/api/test") is True

    def test_is_excluded_domain_for_general_api(self):
        """일반 API 도메인은 제외 안 됨"""
        assert is_excluded_domain("https://api.example.com") is False
        assert is_excluded_domain("https://httpbin.org/get") is False

    def test_is_excluded_domain_partial_match(self):
        """부분 일치도 제외됨"""
        # "api.tosspayments.com"이 URL에 포함되면 제외
        assert is_excluded_domain("https://test.api.tosspayments.com/v1") is True
