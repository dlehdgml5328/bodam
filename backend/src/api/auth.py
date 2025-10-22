"""Authentication API endpoints."""

from __future__ import annotations

import secrets
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.user import User, UserRole
from src.security.passwords import hash_password, verify_password
from src.security.session import (
    clear_session_cookies,
    get_current_user,
    get_current_user_with_csrf,
    issue_session_tokens,
)
from src.security_config import get_security_settings
from src.services.password_reset_service import (
    PasswordResetService,
    PasswordResetTokenExpiredError,
    PasswordResetTokenNotFoundError,
)
from src.services.refresh_token_service import (
    RefreshTokenService,
    RefreshTokenExpiredError,
    RefreshTokenRevokedError,
    RefreshTokenNotFoundError,
)
from src.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)
from src.services.oauth_service import OAuthService, OAuthError, SocialProvider

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    phone: str = Field(pattern=r"^01[0-9]{8,9}$")
    id_number: str = Field(pattern=r"^\d{6}-?\d{7}$")  # 123456-1234567 또는 1234561234567


class SignupResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    class UserInfo(BaseModel):
        id: uuid.UUID
        email: EmailStr
        name: str

    user: UserInfo
    access_token: str
    csrf_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=SignupResponse)
async def signup(
    payload: SignupRequest, session: AsyncSession = Depends(get_session)
) -> SignupResponse:
    user_service = UserService(session)
    try:
        user = await user_service.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            name=payload.name,
            phone=payload.phone,
            id_number=payload.id_number,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="EMAIL_EXISTS") from exc

    return SignupResponse(
        user_id=user.id,
        email=user.email,
        message="인증 이메일이 발송되었습니다",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    user_service = UserService(session)
    try:
        user = await user_service.get_user_by_email(payload.email)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS") from exc

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ACCOUNT_DISABLED")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    tokens = await issue_session_tokens(response, user, session)

    return LoginResponse(
        user=LoginResponse.UserInfo(id=user.id, email=user.email, name=user.name),
        access_token=tokens["access_token"],
        csrf_token=tokens["csrf_token"],
    )


@router.post("/logout")
async def logout(response: Response) -> JSONResponse:
    clear_session_cookies(response)
    return JSONResponse(content={"message": "ok"})


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Refresh access token using refresh token cookie."""
    refresh_token_string = request.cookies.get("bodam_refresh")

    if not refresh_token_string:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_MISSING"
        )

    refresh_service = RefreshTokenService(session)
    user_service = UserService(session)

    try:
        # Validate refresh token
        refresh_token = await refresh_service.validate_token(refresh_token_string)

        # Get user
        user = await user_service.get_user(refresh_token.user_id)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCOUNT_DISABLED"
            )

        # Issue new tokens
        tokens = await issue_session_tokens(response, user, session)
        return tokens

    except RefreshTokenNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_REFRESH_TOKEN"
        )
    except RefreshTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_EXPIRED"
        )
    except RefreshTokenRevokedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_REVOKED"
        )


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    user_service = UserService(session)
    settings = get_security_settings()

    try:
        user = await user_service.get_user_by_email(payload.email)
    except UserNotFoundError:
        return {"message": "비밀번호 재설정 안내를 확인해주세요."}

    reset_service = PasswordResetService(session)
    token = await reset_service.create_token(
        user_id=user.id, ttl_minutes=settings.password_reset_token_minutes
    )
    return {
        "message": "비밀번호 재설정 안내를 확인해주세요.",
        "reset_token": token.token,
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    reset_service = PasswordResetService(session)
    user_service = UserService(session)

    try:
        token = await reset_service.consume_token(payload.token)
    except PasswordResetTokenNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_TOKEN") from exc
    except PasswordResetTokenExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOKEN_EXPIRED") from exc

    user = await user_service.get_user(token.user_id)
    user.password_hash = hash_password(payload.new_password)
    return {"message": "비밀번호가 재설정되었습니다."}


@router.get("/social/{provider}")
async def social_login(provider: SocialProvider) -> dict[str, str]:
    """Generate OAuth authorization URL for social login."""
    oauth_service = OAuthService()
    state = secrets.token_urlsafe(32)

    try:
        auth_url = oauth_service.get_authorization_url(provider, state)
        return {
            "authorization_url": auth_url,
            "state": state,
        }
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/social/{provider}/callback")
async def social_callback(
    provider: SocialProvider,
    code: str,
    state: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    """Handle OAuth callback and create/login user."""
    oauth_service = OAuthService()
    user_service = UserService(session)

    try:
        # 1. Exchange code for access token
        access_token = await oauth_service.get_access_token(provider, code, state)

        # 2. Get user info from provider
        user_info = await oauth_service.get_user_info(provider, access_token)

        social_id = user_info.get("social_id")
        email = user_info.get("email")
        name = user_info.get("name")

        if not social_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="소셜 로그인에서 필수 정보를 받지 못했습니다."
            )

        # 3. Check if user exists with this social account
        user = await session.scalar(
            select(User).where(
                User.social_provider == provider,
                User.social_id == social_id
            )
        )

        # 4. If not exists, check if email exists
        if not user:
            try:
                user = await user_service.get_user_by_email(email)
                # Email exists but not linked to this social account
                # Link the social account
                user.social_provider = provider
                user.social_id = social_id
                await session.flush()
            except UserNotFoundError:
                # Create new user
                user = await user_service.create_user(
                    email=email,
                    password_hash=secrets.token_urlsafe(32),  # Random password
                    name=name or email.split("@")[0],
                    role=UserRole.DONOR,
                )
                user.social_provider = provider
                user.social_id = social_id
                await session.flush()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ACCOUNT_DISABLED"
            )

        # 5. Issue tokens
        tokens = await issue_session_tokens(response, user, session)

        return LoginResponse(
            user=LoginResponse.UserInfo(id=user.id, email=user.email, name=user.name),
            access_token=tokens["access_token"],
            csrf_token=tokens["csrf_token"],
        )

    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 인증 실패: {str(exc)}"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> dict:
    """현재 로그인한 사용자 정보 조회"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "id_number": current_user.id_number,
        "role": current_user.role.value if current_user.role else "user",
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    phone: str | None = Field(default=None, pattern=r"^01[0-9]{8,9}$")
    id_number: str | None = Field(default=None, pattern=r"^\d{6}-?\d{7}$")


@router.patch("/me")
async def update_current_user_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user_with_csrf),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """현재 로그인한 사용자 프로필 수정"""
    user_service = UserService(session)

    # None이 아닌 필드만 업데이트
    update_fields = {}
    if payload.name is not None:
        update_fields["name"] = payload.name
    if payload.phone is not None:
        update_fields["phone"] = payload.phone
    if payload.id_number is not None:
        update_fields["id_number"] = payload.id_number

    updated_user = await user_service.update_user(current_user.id, **update_fields)
    await session.commit()

    return {
        "id": str(updated_user.id),
        "email": updated_user.email,
        "name": updated_user.name,
        "phone": updated_user.phone,
        "id_number": updated_user.id_number,
        "role": updated_user.role.value if updated_user.role else "user",
        "message": "프로필이 업데이트되었습니다",
    }


__all__ = ["router"]
