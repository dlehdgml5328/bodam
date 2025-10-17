"""Session helpers for issuing and validating access and CSRF tokens."""

from __future__ import annotations

import secrets
import uuid
from typing import Final

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.security_config import get_security_settings
from src.database.connection import get_session
from src.models.user import User
from src.security.tokens import TokenDecodeError, create_access_token, decode_access_token
from src.services.user_service import UserNotFoundError, UserService

SESSION_COOKIE_NAME: Final[str] = "bodam_session"
CSRF_COOKIE_NAME: Final[str] = "bodam_csrf"
CSRF_HEADER_NAME: Final[str] = "X-CSRF-Token"


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    """Return the authenticated user based on the request token."""
    token = getattr(request.state, "token", None)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    return await _decode_user_from_token(token, session)


async def get_current_user_with_csrf(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    """Return the current user and validate CSRF token for unsafe methods."""
    user = await get_current_user(request, session)
    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return user

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CSRF_VALIDATION_FAILED")
    return user


async def get_current_user_from_bearer(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    """Return the authenticated user based on Authorization bearer token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    token = auth_header.split(" ", 1)[1]
    return await _decode_user_from_token(token, session)


def issue_session_tokens(
    response: Response, user: User, *, expires_minutes: int | None = None
) -> dict[str, str]:
    """Issue an access token and CSRF token, storing them as cookies and returning both."""
    settings = get_security_settings()
    access_token = create_access_token(
        str(user.id), expires_minutes=expires_minutes
    )
    csrf_token = secrets.token_urlsafe(32)
    max_age = (expires_minutes or settings.access_token_ttl_minutes) * 60

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain or None,
        max_age=max_age,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain or None,
        max_age=max_age,
    )
    return {"access_token": access_token, "csrf_token": csrf_token}


def clear_session_cookies(response: Response) -> None:
    """Remove authentication and CSRF cookies from the client."""
    settings = get_security_settings()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        domain=settings.cookie_domain or None,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        domain=settings.cookie_domain or None,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )


async def _decode_user_from_token(token: str, session: AsyncSession) -> User:
    try:
        payload = decode_access_token(token)
    except TokenDecodeError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN") from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")

    try:
        user_id = uuid.UUID(subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN") from exc

    user_service = UserService(session)
    try:
        user = await user_service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_FOUND") from exc

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ACCOUNT_DISABLED")

    return user


__all__ = [
    "SESSION_COOKIE_NAME",
    "CSRF_COOKIE_NAME",
    "CSRF_HEADER_NAME",
    "get_current_user",
    "get_current_user_with_csrf",
    "get_current_user_from_bearer",
    "issue_session_tokens",
    "clear_session_cookies",
]
