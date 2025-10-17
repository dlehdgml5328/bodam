"""
SQLAdmin 설정 모듈

SQLAdmin 인스턴스 생성 및 전역 설정을 관리합니다.
"""
import os
from typing import Optional

from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine


class AdminConfig:
    """SQLAdmin 설정 클래스"""

    def __init__(self):
        self.secret_key = os.getenv(
            "SQLADMIN_SECRET_KEY",
            "dev-sqladmin-secret-key-must-be-random-32-chars"
        )
        self.session_timeout = int(os.getenv("SQLADMIN_SESSION_TIMEOUT", "3600"))
        self.title = "보담(BoDam) 관리자"
        self.logo_url = None  # 로고 URL (옵션)


def create_admin(engine: AsyncEngine) -> Admin:
    """
    SQLAdmin 인스턴스를 생성합니다.

    Args:
        engine: SQLAlchemy AsyncEngine 인스턴스

    Returns:
        설정된 Admin 인스턴스
    """
    config = AdminConfig()

    admin = Admin(
        engine=engine,
        title=config.title,
        base_url="/admin",
    )

    return admin


__all__ = ["AdminConfig", "create_admin"]
