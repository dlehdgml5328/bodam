"""Service helpers for password reset tokens."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.password_reset import PasswordResetToken


class PasswordResetTokenNotFoundError(Exception):
    """Raised when a password reset token does not exist."""


class PasswordResetTokenExpiredError(Exception):
    """Raised when a password reset token has expired or already used."""


class PasswordResetService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_token(self, *, user_id: uuid.UUID, ttl_minutes: int) -> PasswordResetToken:
        token_value = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        token = PasswordResetToken(user_id=user_id, token=token_value, expires_at=expires_at)
        self._session.add(token)
        await self._session.flush()
        return token

    async def consume_token(self, token_value: str) -> PasswordResetToken:
        token = await self._session.scalar(
            select(PasswordResetToken).where(PasswordResetToken.token == token_value)
        )
        if token is None:
            raise PasswordResetTokenNotFoundError(token_value)
        if token.used or token.expires_at <= datetime.now(timezone.utc):
            raise PasswordResetTokenExpiredError(token_value)
        token.used = True
        await self._session.flush()
        return token


__all__ = [
    "PasswordResetService",
    "PasswordResetTokenNotFoundError",
    "PasswordResetTokenExpiredError",
]
