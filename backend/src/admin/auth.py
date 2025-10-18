"""SQLAdmin 인증 백엔드 구현.

보담의 기존 인증 시스템(세션 쿠키 기반)과 통합하여 SQLAdmin 접근을 제어합니다.
Admin 역할(UserRole.ADMIN)을 가진 사용자만 접근 가능합니다.
"""

from __future__ import annotations

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.database.connection import SessionLocal
from src.models.user import UserRole
from src.security.passwords import verify_password
from src.security.session import (
    SESSION_COOKIE_NAME,
    issue_session_tokens,
)
from src.security.tokens import TokenDecodeError, decode_access_token
from src.services.user_service import UserNotFoundError, UserService


class AdminAuthBackend(AuthenticationBackend):
    """SQLAdmin을 위한 인증 백엔드.

    보담의 기존 세션 쿠키 기반 인증 시스템을 재사용하여
    Admin 역할을 가진 사용자만 SQLAdmin 패널에 접근할 수 있도록 제어합니다.
    """

    async def login(self, request: Request) -> bool:
        """로그인 요청 처리.

        폼 데이터에서 email과 password를 추출하여 검증하고,
        Admin 역할을 가진 사용자인 경우 세션 쿠키를 발급합니다.

        Args:
            request: Starlette Request 객체

        Returns:
            로그인 성공 여부
        """
        form = await request.form()
        email = form.get("username")  # SQLAdmin은 username 필드 사용
        password = form.get("password")

        if not email or not password:
            return False

        async with SessionLocal() as session:
            user_service = UserService(session)

            try:
                # 이메일로 사용자 조회
                user = await user_service.get_user_by_email(str(email))
            except UserNotFoundError:
                return False

            # 비밀번호 검증
            if not verify_password(str(password), user.password_hash):
                return False

            # Admin 역할 확인
            if user.role != UserRole.ADMIN:
                return False

            # 계정 활성화 상태 확인
            if not user.is_active:
                return False

            # 세션 토큰 발급 (기존 보담 인증 시스템 재사용)
            # RedirectResponse를 생성하여 쿠키 설정
            response = RedirectResponse(url="/admin", status_code=302)
            issue_session_tokens(response, user)

            # 요청의 세션에 response의 쿠키를 복사
            # (SQLAdmin의 login 메서드는 bool만 반환하므로 쿠키를 직접 설정해야 함)
            request.session.update({"token": response.cookies.get(SESSION_COOKIE_NAME)})

            return True

    async def logout(self, request: Request) -> bool:
        """로그아웃 요청 처리.

        세션 쿠키를 삭제하여 로그아웃합니다.

        Args:
            request: Starlette Request 객체

        Returns:
            로그아웃 성공 여부 (항상 True)
        """
        # 세션 데이터 클리어
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """요청 인증 확인.

        세션 쿠키에서 토큰을 추출하여 사용자를 확인하고,
        Admin 역할을 가진 활성 사용자인지 검증합니다.

        Args:
            request: Starlette Request 객체

        Returns:
            인증 성공 여부
        """
        # 쿠키 또는 세션에서 토큰 추출
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            token = request.session.get("token")

        if not token:
            return False

        async with SessionLocal() as session:
            user_service = UserService(session)

            try:
                # 토큰 디코딩
                payload = decode_access_token(token)
                subject = payload.get("sub")

                if not subject:
                    return False

                # 사용자 조회
                import uuid
                user_id = uuid.UUID(subject)
                user = await user_service.get_user(user_id)

            except (TokenDecodeError, UserNotFoundError, ValueError, TypeError):
                return False

            # Admin 역할 확인
            if user.role != UserRole.ADMIN:
                return False

            # 계정 활성화 상태 확인
            if not user.is_active:
                return False

            return True


__all__ = ["AdminAuthBackend"]
