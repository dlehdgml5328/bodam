"""
테스트 공통 픽스처 정의

관리자/일반 사용자 픽스처, 인증 토큰, AsyncClient 등을 제공합니다.
"""

import uuid
from typing import AsyncGenerator, Dict

import pytest
from httpx import AsyncClient

from src.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """비동기 HTTP 클라이언트 픽스처"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def admin_user() -> Dict[str, str]:
    """
    관리자 사용자 정보 픽스처

    Returns:
        관리자 사용자 정보 딕셔너리
    """
    return {
        "id": str(uuid.uuid4()),
        "email": "admin@bodam.example.com",
        "name": "관리자",
        "role": "admin",
    }


@pytest.fixture
def regular_user() -> Dict[str, str]:
    """
    일반 사용자 정보 픽스처

    Returns:
        일반 사용자 정보 딕셔너리
    """
    return {
        "id": str(uuid.uuid4()),
        "email": "user@bodam.example.com",
        "name": "일반사용자",
        "role": "donor",
    }


@pytest.fixture
def admin_token(admin_user: Dict[str, str]) -> str:
    """
    관리자 JWT 토큰 픽스처

    실제 구현 전이므로 더미 토큰을 반환합니다.
    구현 후에는 실제 JWT 생성 로직을 사용해야 합니다.

    Args:
        admin_user: 관리자 사용자 정보

    Returns:
        관리자 Bearer 토큰
    """
    # TODO: 실제 JWT 토큰 생성 로직으로 대체 필요
    return f"Bearer admin-token-{admin_user['id']}"


@pytest.fixture
def user_token(regular_user: Dict[str, str]) -> str:
    """
    일반 사용자 JWT 토큰 픽스처

    실제 구현 전이므로 더미 토큰을 반환합니다.
    구현 후에는 실제 JWT 생성 로직을 사용해야 합니다.

    Args:
        regular_user: 일반 사용자 정보

    Returns:
        일반 사용자 Bearer 토큰
    """
    # TODO: 실제 JWT 토큰 생성 로직으로 대체 필요
    return f"Bearer user-token-{regular_user['id']}"


@pytest.fixture
def admin_session_cookie(admin_user: Dict[str, str]) -> str:
    """
    관리자 세션 쿠키 픽스처

    실제 구현 전이므로 더미 쿠키를 반환합니다.
    구현 후에는 실제 세션 생성 로직을 사용해야 합니다.

    Args:
        admin_user: 관리자 사용자 정보

    Returns:
        관리자 세션 쿠키
    """
    # TODO: 실제 세션 쿠키 생성 로직으로 대체 필요
    return f"admin_session=session-{admin_user['id']}"
