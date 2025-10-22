"""애플리케이션 설정 관리

환경 변수를 통해 설정을 로드하고 관리합니다.
"""

from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # 추가 필드 무시
    )

    # 데이터베이스 설정
    database_url: str = "postgresql+asyncpg://bodam:bodam@localhost:5432/bodam"
    postgres_db: str = "bodam"
    postgres_user: str = "bodam"
    postgres_password: str = "bodam"

    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"

    # Celery 설정
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # API 설정
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_reload: bool = True
    
    # JWT 설정
    jwt_secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Kong Gateway 설정
    kong_admin_url: str = "http://localhost:8001"
    kong_proxy_url: str = "http://localhost:8000"
    
    # Selenium 설정
    selenium_headless: bool = True
    selenium_driver_pool_size: int = 10
    selenium_default_timeout: int = 30

    # === DB 연결 풀 설정 ===
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True
    db_pool_timeout: float = 0.4

    # === HTTP 연결 풀 설정 ===
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: float = 60.0

    # === HTTP 타임아웃 설정 (일반 API) ===
    http_connect_timeout: float = 4.0
    http_read_timeout: float = 8.0
    http_write_timeout: float = 10.0
    http_pool_timeout: float = 10.0

    # === HTTP 타임아웃 설정 (결제 API) ===
    http_payment_connect_timeout: float = 180.0
    http_payment_read_timeout: float = 180.0

    # === 재시도 설정 ===
    retry_max_attempts: int = 3
    retry_interval: float = 4.0
    retry_excluded_domains: str = "api.tosspayments.com,pay.naver.com"

    # 로그 설정
    log_level: str = "INFO"
    log_format: str = "console"  # console 또는 json
    
    # Sentry 설정 (선택사항)
    sentry_dsn: Optional[str] = None
    
    # 환경 구분
    environment: str = "development"
    


# 전역 설정 인스턴스
settings = Settings()


__all__ = ["settings", "Settings"]
