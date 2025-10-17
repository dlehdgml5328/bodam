"""Admin 인증 API 엔드포인트.

SQLAdmin과 보담 인증 시스템을 통합하는 로그인/로그아웃 엔드포인트를 제공합니다.
세션 쿠키를 통해 인증 상태를 관리합니다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.user import UserRole
from src.security.passwords import verify_password
from src.security.session import clear_session_cookies, issue_session_tokens
from src.services.user_service import UserNotFoundError, UserService

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


class LoginRequest(BaseModel):
    """로그인 요청 스키마."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 스키마."""

    message: str
    user_email: str
    role: str


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def admin_login(
    credentials: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    """Admin 로그인 엔드포인트.

    이메일과 비밀번호로 인증하고, Admin 역할을 확인한 후
    세션 쿠키를 발급합니다.

    Args:
        credentials: 로그인 요청 데이터 (email, password)
        response: FastAPI Response 객체 (쿠키 설정용)
        session: 데이터베이스 세션

    Returns:
        로그인 성공 메시지와 사용자 정보

    Raises:
        HTTPException: 인증 실패 시 401 Unauthorized
        HTTPException: Admin 권한 없을 시 403 Forbidden
    """
    user_service = UserService(session)

    try:
        # 이메일로 사용자 조회
        user = await user_service.get_user_by_email(credentials.email)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
        ) from exc

    # 비밀번호 검증
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
        )

    # 계정 활성화 상태 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_DISABLED",
        )

    # Admin 역할 확인
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN_ACCESS_REQUIRED",
        )

    # 세션 쿠키 발급 (기존 보담 인증 시스템 재사용)
    issue_session_tokens(response, user)

    return LoginResponse(
        message="로그인 성공",
        user_email=user.email,
        role=user.role.value,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def admin_logout(response: Response) -> dict[str, str]:
    """Admin 로그아웃 엔드포인트.

    세션 쿠키를 삭제하여 로그아웃 처리합니다.

    Args:
        response: FastAPI Response 객체 (쿠키 삭제용)

    Returns:
        로그아웃 성공 메시지
    """
    # 세션 쿠키 삭제 (기존 보담 인증 시스템 재사용)
    clear_session_cookies(response)

    return {"message": "로그아웃 성공"}


__all__ = ["router"]
