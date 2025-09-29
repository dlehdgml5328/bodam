"""Authentication API endpoints."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.security import get_security_settings
from src.database.connection import get_session
from src.security.passwords import hash_password, verify_password
from src.security.tokens import create_access_token
from src.services.password_reset_service import (
    PasswordResetService,
    PasswordResetTokenExpiredError,
    PasswordResetTokenNotFoundError,
)
from src.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    phone: str | None = Field(default=None, pattern=r"^01[0-9]{8,9}$")


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

    token = create_access_token(str(user.id))
    settings = get_security_settings()
    response.set_cookie(
        key="bodam_session",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain or None,
        max_age=settings.access_token_ttl_minutes * 60,
    )

    return LoginResponse(
        user=LoginResponse.UserInfo(id=user.id, email=user.email, name=user.name),
        access_token=token,
    )


@router.post("/logout")
async def logout(response: Response) -> JSONResponse:
    settings = get_security_settings()
    response.delete_cookie(
        key="bodam_session",
        domain=settings.cookie_domain or None,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    headers = {"Set-Cookie": "bodam_session=; HttpOnly; Path=/; Max-Age=0"}
    return JSONResponse(content={"message": "ok"}, headers=headers)


@router.post("/refresh")
async def refresh() -> dict:
    return {"access_token": create_access_token(str(uuid.uuid4()))}


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
async def social_login(provider: Literal["google", "kakao", "naver"]) -> RedirectResponse:
    return RedirectResponse(
        url=f"https://auth.bodam.example/{provider}", status_code=status.HTTP_302_FOUND
    )


@router.get("/social/{provider}/callback")
async def social_callback(
    provider: Literal["google", "kakao", "naver"], code: str | None = None
) -> RedirectResponse:
    if code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")
    return RedirectResponse(
        url=f"https://app.bodam.example/social/{provider}?code={code}",
        status_code=status.HTTP_302_FOUND,
    )


__all__ = ["router"]
