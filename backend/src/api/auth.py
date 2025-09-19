"""Authentication API endpoints."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    phone: str | None = Field(default=None, pattern=r"^01[0-9]{8,9}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> dict:
    return {
        "user_id": str(uuid.uuid4()),
        "email": payload.email,
        "message": "인증 이메일이 발송되었습니다",
    }


@router.post("/login")
async def login(payload: LoginRequest, response: Response) -> dict:
    dummy_token = str(uuid.uuid4())
    response.set_cookie(
        key="bodam_session",
        value=dummy_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return {
        "user": {
            "id": str(uuid.uuid4()),
            "email": payload.email,
            "name": "보담 사용자",
        },
        "access_token": dummy_token,
    }


@router.post("/logout")
async def logout(response: Response) -> JSONResponse:
    response.delete_cookie("bodam_session")
    headers = {"Set-Cookie": "bodam_session=; HttpOnly; Path=/; Max-Age=0"}
    return JSONResponse(content={"message": "ok"}, headers=headers)


@router.post("/refresh")
async def refresh() -> dict:
    return {"access_token": str(uuid.uuid4())}


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
