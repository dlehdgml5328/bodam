"""연결 풀 설정 Unit Tests"""
import pytest
from src.config import settings


class TestPoolConfig:
    """연결 풀 설정 로드 검증"""

    def test_db_pool_settings_loaded(self):
        """DB 연결 풀 설정 로드 확인"""
        assert settings.db_pool_size == 10
        assert settings.db_max_overflow == 20
        assert settings.db_pool_recycle == 3600
        assert settings.db_pool_pre_ping is True
        assert settings.db_pool_timeout == 0.4

    def test_http_pool_settings_loaded(self):
        """HTTP 연결 풀 설정 로드 확인"""
        assert settings.http_max_connections == 100
        assert settings.http_max_keepalive_connections == 20
        assert settings.http_keepalive_expiry == 60.0

    def test_http_timeout_settings_loaded(self):
        """HTTP 타임아웃 설정 로드 확인"""
        assert settings.http_connect_timeout == 4.0
        assert settings.http_read_timeout == 8.0
        assert settings.http_write_timeout == 10.0
        assert settings.http_payment_connect_timeout == 180.0

    def test_retry_policy_settings_loaded(self):
        """재시도 정책 설정 로드 확인"""
        assert settings.retry_max_attempts == 3
        assert settings.retry_interval == 4.0
        assert "api.tosspayments.com" in settings.retry_excluded_domains
